import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://helpdesk_user:helpdesk_pass@localhost:5432/helpdesk_db"
)


def get_connection():
    retries = 10

    for attempt in range(retries):
        try:
            connection = psycopg2.connect(
                DATABASE_URL,
                cursor_factory=RealDictCursor
            )
            return connection
        except psycopg2.OperationalError:
            print(f"Database belum siap. Percobaan {attempt + 1}/{retries}")
            time.sleep(2)

    raise Exception("Gagal terhubung ke database setelah beberapa percobaan.")