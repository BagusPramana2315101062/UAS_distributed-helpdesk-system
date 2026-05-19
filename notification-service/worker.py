import json
import os
import time

import pika
import psycopg2
from psycopg2.extras import RealDictCursor


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://helpdesk_user:helpdesk_pass@postgres:5432/helpdesk_db"
)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))

TICKET_ASSIGNED_QUEUE = "ticket_assigned_queue"
TICKET_CLOSED_QUEUE = "ticket_closed_queue"


def get_db_connection():
    retries = 15

    for attempt in range(retries):
        try:
            return psycopg2.connect(
                DATABASE_URL,
                cursor_factory=RealDictCursor
            )
        except psycopg2.OperationalError:
            print(f"[Notification Service] Database belum siap. Percobaan {attempt + 1}/{retries}", flush=True)
            time.sleep(2)

    raise Exception("[Notification Service] Gagal terhubung ke database.")


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
            print(f"[Notification Service] RabbitMQ belum siap. Percobaan {attempt + 1}/{retries}", flush=True)
            time.sleep(2)

    raise Exception("[Notification Service] Gagal terhubung ke RabbitMQ.")


def save_notification(user_id: int, ticket_id: int, message: str):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO notifications (user_id, ticket_id, message, is_read)
            VALUES (%s, %s, %s, %s)
            RETURNING id, user_id, ticket_id, message, is_read, created_at
            """,
            (user_id, ticket_id, message, False)
        )

        notification = cursor.fetchone()
        connection.commit()

        return notification

    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def handle_ticket_assigned(channel, method, properties, body):
    try:
        event = json.loads(body.decode("utf-8"))

        print(f"[Notification Service] ticket_assigned received: {event}", flush=True)

        user_message = (
            f"Tiket #{event['ticket_id']} sudah ditugaskan kepada admin "
            f"{event['admin_name']} oleh leader node {event['leader_id']}."
        )

        admin_message = (
            f"Anda mendapat assignment untuk menangani tiket #{event['ticket_id']}."
        )

        save_notification(
            user_id=int(event["user_id"]),
            ticket_id=int(event["ticket_id"]),
            message=user_message
        )

        save_notification(
            user_id=int(event["admin_id"]),
            ticket_id=int(event["ticket_id"]),
            message=admin_message
        )

        channel.basic_ack(delivery_tag=method.delivery_tag)

        print("[Notification Service] Notification saved for user and admin", flush=True)

    except Exception as error:
        print(f"[Notification Service] Error ticket_assigned: {error}", flush=True)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def handle_ticket_closed(channel, method, properties, body):
    try:
        event = json.loads(body.decode("utf-8"))

        print(f"[Notification Service] ticket_closed received: {event}", flush=True)

        message = f"Tiket #{event['ticket_id']} dengan judul '{event['title']}' sudah ditutup."

        save_notification(
            user_id=int(event["user_id"]),
            ticket_id=int(event["ticket_id"]),
            message=message
        )

        channel.basic_ack(delivery_tag=method.delivery_tag)

        print("[Notification Service] Ticket closed notification saved", flush=True)

    except Exception as error:
        print(f"[Notification Service] Error ticket_closed: {error}", flush=True)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_worker():
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    channel.queue_declare(queue=TICKET_ASSIGNED_QUEUE, durable=True)
    channel.queue_declare(queue=TICKET_CLOSED_QUEUE, durable=True)

    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue=TICKET_ASSIGNED_QUEUE,
        on_message_callback=handle_ticket_assigned
    )

    channel.basic_consume(
        queue=TICKET_CLOSED_QUEUE,
        on_message_callback=handle_ticket_closed
    )

    print("[Notification Service] Waiting for ticket_assigned and ticket_closed events...", flush=True)

    channel.start_consuming()


if __name__ == "__main__":
    start_worker()