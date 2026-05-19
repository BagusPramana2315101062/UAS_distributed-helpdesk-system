import os
import time
from concurrent import futures

import grpc
import psycopg2
from psycopg2.extras import RealDictCursor

import user_pb2
import user_pb2_grpc


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://helpdesk_user:helpdesk_pass@postgres:5432/helpdesk_db"
)


def get_connection():
    retries = 10

    for attempt in range(retries):
        try:
            return psycopg2.connect(
                DATABASE_URL,
                cursor_factory=RealDictCursor
            )
        except psycopg2.OperationalError:
            print(f"[User Service] Database belum siap. Percobaan {attempt + 1}/{retries}")
            time.sleep(2)

    raise Exception("[User Service] Gagal terhubung ke database.")


class UserService(user_pb2_grpc.UserServiceServicer):
    def GetUserById(self, request, context):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT id, name, email, role
                FROM users
                WHERE id = %s
                """,
                (request.user_id,)
            )

            user = cursor.fetchone()

            if user is None:
                print(f"[gRPC User Service] User ID {request.user_id} tidak ditemukan")
                return user_pb2.UserResponse(
                    id=0,
                    name="",
                    email="",
                    role="",
                    valid=False
                )

            print(f"[gRPC User Service] User ditemukan: {user['name']}")

            return user_pb2.UserResponse(
                id=user["id"],
                name=user["name"],
                email=user["email"],
                role=user["role"],
                valid=True
            )

        finally:
            cursor.close()
            connection.close()

    def GetAvailableAdmins(self, request, context):
        connection = get_connection()
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

            response = user_pb2.AdminList()

            for admin in admins:
                response.admins.append(
                    user_pb2.UserResponse(
                        id=admin["id"],
                        name=admin["name"],
                        email=admin["email"],
                        role=admin["role"],
                        valid=True
                    )
                )

            print(f"[gRPC User Service] Mengirim {len(admins)} admin aktif")

            return response

        finally:
            cursor.close()
            connection.close()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()

    print("[gRPC User Service] Running on port 50051")

    server.wait_for_termination()


if __name__ == "__main__":
    serve()