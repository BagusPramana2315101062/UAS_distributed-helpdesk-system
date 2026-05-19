import os

import grpc
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.database import get_connection
from app.grpc_client import get_available_admins, get_user_by_id
from app.models import TicketCreate, TicketStatusUpdate
from app.rabbitmq import publish_event


INSTANCE_NAME = os.getenv("INSTANCE_NAME", "ticket-service-local")

app = FastAPI(
    title="Distributed Helpdesk Ticket Service",
    description="REST API untuk Helpdesk Ticketing System pada proyek UAS Distributed System.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "service": "Ticket Service",
        "instance": INSTANCE_NAME,
        "message": "Distributed Helpdesk Ticket Service is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "UP",
        "instance": INSTANCE_NAME
    }


@app.get("/grpc/users/{user_id}")
def grpc_get_user(user_id: int):
    try:
        user = get_user_by_id(user_id)
        return {
            "instance": INSTANCE_NAME,
            "source": "gRPC User Service",
            "data": user
        }
    except grpc.RpcError as error:
        raise HTTPException(
            status_code=503,
            detail=f"Gagal menghubungi User Service melalui gRPC: {error.details()}"
        )


@app.get("/grpc/admins")
def grpc_get_admins():
    try:
        admins = get_available_admins()
        return {
            "instance": INSTANCE_NAME,
            "source": "gRPC User Service",
            "total": len(admins),
            "data": admins
        }
    except grpc.RpcError as error:
        raise HTTPException(
            status_code=503,
            detail=f"Gagal mengambil data admin melalui gRPC: {error.details()}"
        )


@app.post("/tickets")
def create_ticket(ticket: TicketCreate):
    try:
        user = get_user_by_id(ticket.user_id)
    except grpc.RpcError as error:
        raise HTTPException(
            status_code=503,
            detail=f"User Service gRPC tidak dapat dihubungi: {error.details()}"
        )

    if not user["valid"]:
        raise HTTPException(status_code=404, detail="User tidak ditemukan melalui gRPC User Service.")

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO tickets (user_id, title, description, category, priority, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, user_id, title, description, category, priority, status, created_at
            """,
            (
                ticket.user_id,
                ticket.title,
                ticket.description,
                ticket.category,
                ticket.priority,
                "OPEN"
            )
        )

        new_ticket = cursor.fetchone()
        connection.commit()

        print(f"[{INSTANCE_NAME}] Ticket created: {new_ticket['id']} after gRPC user validation", flush=True)

        event_payload = {
            "event": "ticket_created",
            "ticket_id": new_ticket["id"],
            "user_id": new_ticket["user_id"],
            "title": new_ticket["title"],
            "category": new_ticket["category"],
            "priority": new_ticket["priority"],
            "source_instance": INSTANCE_NAME
        }

        publish_event("ticket_created_queue", event_payload)

        return {
            "message": "Ticket berhasil dibuat, user tervalidasi via gRPC, dan event dikirim ke RabbitMQ.",
            "instance": INSTANCE_NAME,
            "validated_user": user,
            "data": new_ticket,
            "event": event_payload
        }

    except Exception as error:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(error))
    finally:
        cursor.close()
        connection.close()


@app.get("/tickets")
def get_tickets():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT 
                tickets.id,
                tickets.user_id,
                users.name AS user_name,
                tickets.title,
                tickets.description,
                tickets.category,
                tickets.priority,
                tickets.status,
                tickets.created_at
            FROM tickets
            JOIN users ON tickets.user_id = users.id
            ORDER BY tickets.id DESC
            """
        )

        tickets = cursor.fetchall()

        return {
            "instance": INSTANCE_NAME,
            "total": len(tickets),
            "data": tickets
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
    finally:
        cursor.close()
        connection.close()


@app.get("/tickets/{ticket_id}")
def get_ticket_by_id(ticket_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT 
                tickets.id,
                tickets.user_id,
                users.name AS user_name,
                tickets.title,
                tickets.description,
                tickets.category,
                tickets.priority,
                tickets.status,
                tickets.created_at
            FROM tickets
            JOIN users ON tickets.user_id = users.id
            WHERE tickets.id = %s
            """,
            (ticket_id,)
        )

        ticket = cursor.fetchone()

        if ticket is None:
            raise HTTPException(status_code=404, detail="Ticket tidak ditemukan.")

        return {
            "instance": INSTANCE_NAME,
            "data": ticket
        }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
    finally:
        cursor.close()
        connection.close()


@app.get("/assignments")
def get_assignments():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT 
                assignments.id,
                assignments.ticket_id,
                tickets.title AS ticket_title,
                assignments.admin_id,
                users.name AS admin_name,
                assignments.assigned_by_leader_id,
                assignments.created_at
            FROM assignments
            JOIN tickets ON assignments.ticket_id = tickets.id
            JOIN users ON assignments.admin_id = users.id
            ORDER BY assignments.id DESC
            """
        )

        assignments = cursor.fetchall()

        return {
            "instance": INSTANCE_NAME,
            "total": len(assignments),
            "data": assignments
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
    finally:
        cursor.close()
        connection.close()


@app.get("/notifications")
def get_notifications():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT 
                notifications.id,
                notifications.user_id,
                users.name AS user_name,
                notifications.ticket_id,
                notifications.message,
                notifications.is_read,
                notifications.created_at
            FROM notifications
            JOIN users ON notifications.user_id = users.id
            ORDER BY notifications.id DESC
            """
        )

        notifications = cursor.fetchall()

        return {
            "instance": INSTANCE_NAME,
            "total": len(notifications),
            "data": notifications
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
    finally:
        cursor.close()
        connection.close()


@app.put("/tickets/{ticket_id}/status")
def update_ticket_status(ticket_id: int, payload: TicketStatusUpdate):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE tickets
            SET status = %s
            WHERE id = %s
            RETURNING id, user_id, title, description, category, priority, status, created_at
            """,
            (payload.status, ticket_id)
        )

        updated_ticket = cursor.fetchone()

        if updated_ticket is None:
            raise HTTPException(status_code=404, detail="Ticket tidak ditemukan.")

        connection.commit()

        print(f"[{INSTANCE_NAME}] Ticket status updated: {ticket_id} -> {payload.status}", flush=True)

        if payload.status.upper() == "CLOSED":
            event_payload = {
                "event": "ticket_closed",
                "ticket_id": updated_ticket["id"],
                "user_id": updated_ticket["user_id"],
                "title": updated_ticket["title"],
                "status": updated_ticket["status"],
                "source_instance": INSTANCE_NAME
            }

            publish_event("ticket_closed_queue", event_payload)

        return {
            "message": "Status ticket berhasil diperbarui.",
            "instance": INSTANCE_NAME,
            "data": updated_ticket
        }

    except HTTPException:
        connection.rollback()
        raise
    except Exception as error:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(error))
    finally:
        cursor.close()
        connection.close()