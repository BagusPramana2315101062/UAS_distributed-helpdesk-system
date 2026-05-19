import os
import sys

import grpc


PROTO_DIR = os.path.join(os.path.dirname(__file__), "proto")
sys.path.append(PROTO_DIR)

import user_pb2
import user_pb2_grpc


USER_SERVICE_HOST = os.getenv("USER_SERVICE_HOST", "user-service")
USER_SERVICE_PORT = os.getenv("USER_SERVICE_PORT", "50051")


def get_user_by_id(user_id: int):
    target = f"{USER_SERVICE_HOST}:{USER_SERVICE_PORT}"

    print(f"[gRPC Client] Calling UserService.GetUserById at {target}")

    with grpc.insecure_channel(target) as channel:
        stub = user_pb2_grpc.UserServiceStub(channel)
        response = stub.GetUserById(
            user_pb2.UserRequest(user_id=user_id),
            timeout=5
        )

    return {
        "id": response.id,
        "name": response.name,
        "email": response.email,
        "role": response.role,
        "valid": response.valid
    }


def get_available_admins():
    target = f"{USER_SERVICE_HOST}:{USER_SERVICE_PORT}"

    print(f"[gRPC Client] Calling UserService.GetAvailableAdmins at {target}")

    with grpc.insecure_channel(target) as channel:
        stub = user_pb2_grpc.UserServiceStub(channel)
        response = stub.GetAvailableAdmins(
            user_pb2.Empty(),
            timeout=5
        )

    admins = []

    for admin in response.admins:
        admins.append({
            "id": admin.id,
            "name": admin.name,
            "email": admin.email,
            "role": admin.role,
            "valid": admin.valid
        })

    return admins