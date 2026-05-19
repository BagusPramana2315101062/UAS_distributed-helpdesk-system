import json
import os
import time
import requests
import pika
import psycopg2
from psycopg2.extras import RealDictCursor


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://helpdesk_user:helpdesk_pass@postgres:5432/helpdesk_db"
)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))

LEADER_SERVICE_URL = os.getenv("LEADER_SERVICE_URL", "http://leader-election-service:9000")

TICKET_CREATED_QUEUE = "ticket_created_queue"
TICKET_ASSIGNED_QUEUE = "ticket_assigned_queue"


def get_db_connection():
    retries = 15

    for attempt in range(retries):
        try:
            return psycopg2.connect(
                DATABASE_URL,
                cursor_factory=RealDictCursor
            )
        except psycopg2.OperationalError:
            print(f"[Assignment Service] Database belum siap. Percobaan {attempt + 1}/{retries}", flush=True)
            time.sleep(2)

    raise Exception("[Assignment Service] Gagal terhubung ke database.")


def get_rabbitmq_connection():
    retries = 20

    for attempt in range(retries):
        try:
            return pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    port=RABBITMQ_PORT,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
            )
        except pika.exceptions.AMQPConnectionError:
            print(f"[Assignment Service] RabbitMQ belum siap. Percobaan {attempt + 1}/{retries}", flush=True)
            time.sleep(2)

    raise Exception("[Assignment Service] Gagal terhubung ke RabbitMQ.")


def choose_admin(ticket_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT id, name, email, role
            FROM users
            WHERE role = 'ADMIN'
            ORDER BY id ASC
            """
        )

        admins = cursor.fetchall()

        if not admins:
            raise Exception("Tidak ada admin yang tersedia.")

        selected_index = ticket_id % len(admins)
        selected_admin = admins[selected_index]

        return selected_admin

    finally:
        cursor.close()
        connection.close()


def get_current_leader():
    try:
        response = requests.get(f"{LEADER_SERVICE_URL}/leader", timeout=5)
        response.raise_for_status()
        data = response.json()

        leader_id = data.get("leader_id")

        if leader_id is None:
            raise Exception("Leader belum tersedia.")

        print(f"[Assignment Service] Current leader from Leader Election Service: {leader_id}", flush=True)

        return leader_id

    except Exception as error:
        print(f"[Assignment Service] Gagal mengambil leader aktif: {error}", flush=True)
        return 0


def save_assignment(ticket_id: int, admin_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()

    leader_id = get_current_leader()

    try:
        cursor.execute(
            """
            INSERT INTO assignments (ticket_id, admin_id, assigned_by_leader_id)
            VALUES (%s, %s, %s)
            RETURNING id, ticket_id, admin_id, assigned_by_leader_id, created_at
            """,
            (ticket_id, admin_id, leader_id)
        )

        assignment = cursor.fetchone()

        cursor.execute(
            """
            UPDATE tickets
            SET status = 'ASSIGNED'
            WHERE id = %s
            """,
            (ticket_id,)
        )

        connection.commit()

        return assignment

    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()

def publish_ticket_assigned(channel, payload: dict):
    channel.queue_declare(queue=TICKET_ASSIGNED_QUEUE, durable=True)

    channel.basic_publish(
        exchange="",
        routing_key=TICKET_ASSIGNED_QUEUE,
        body=json.dumps(payload, default=str),
        properties=pika.BasicProperties(
            delivery_mode=2,
            content_type="application/json"
        )
    )

    print(f"[Assignment Service] Event sent to {TICKET_ASSIGNED_QUEUE}: {payload}", flush=True)


def handle_ticket_created(channel, method, properties, body):
    try:
        event = json.loads(body.decode("utf-8"))

        print(f"[Assignment Service] Event received: {event}", flush=True)

        ticket_id = int(event["ticket_id"])
        user_id = int(event["user_id"])

        selected_admin = choose_admin(ticket_id)
        assignment = save_assignment(ticket_id, selected_admin["id"])

        assigned_event = {
            "event": "ticket_assigned",
            "ticket_id": ticket_id,
            "user_id": user_id,
            "admin_id": selected_admin["id"],
            "admin_name": selected_admin["name"],
            "leader_id": assignment["assigned_by_leader_id"],
            "assignment_id": assignment["id"]
        }

        publish_ticket_assigned(channel, assigned_event)

        channel.basic_ack(delivery_tag=method.delivery_tag)

        print(
            f"[Assignment Service] Ticket {ticket_id} assigned to {selected_admin['name']}",
            flush=True
        )

    except Exception as error:
        print(f"[Assignment Service] Error: {error}", flush=True)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_worker():
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    channel.queue_declare(queue=TICKET_CREATED_QUEUE, durable=True)
    channel.queue_declare(queue=TICKET_ASSIGNED_QUEUE, durable=True)

    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue=TICKET_CREATED_QUEUE,
        on_message_callback=handle_ticket_created
    )

    print("[Assignment Service] Waiting for ticket_created events...", flush=True)

    channel.start_consuming()


if __name__ == "__main__":
    start_worker()