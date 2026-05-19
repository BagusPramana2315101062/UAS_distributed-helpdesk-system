from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    user_id: int = Field(..., example=1)
    title: str = Field(..., example="Tidak bisa login")
    description: str = Field(..., example="Saya tidak bisa login ke sistem akademik.")
    category: str = Field(..., example="Account")
    priority: str = Field(..., example="HIGH")


class TicketStatusUpdate(BaseModel):
    status: str = Field(..., example="IN_PROGRESS")