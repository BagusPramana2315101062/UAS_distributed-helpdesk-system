import json
import os
import time

import pika


RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))


def get_rabbitmq_connection():
    retries = 15

    for attempt in range(retries):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    port=RABBITMQ_PORT,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
            )
            return connection
        except pika.exceptions.AMQPConnectionError:
            print(f"[RabbitMQ Publisher] RabbitMQ belum siap. Percobaan {attempt + 1}/{retries}", flush=True)
            time.sleep(2)

    raise Exception("[RabbitMQ Publisher] Gagal terhubung ke RabbitMQ.")


def publish_event(queue_name: str, payload: dict):
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    channel.queue_declare(queue=queue_name, durable=True)

    channel.basic_publish(
        exchange="",
        routing_key=queue_name,
        body=json.dumps(payload, default=str),
        properties=pika.BasicProperties(
            delivery_mode=2,
            content_type="application/json"
        )
    )

    print(f"[RabbitMQ Publisher] Event sent to {queue_name}: {payload}", flush=True)

    connection.close()