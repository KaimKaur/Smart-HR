from uuid import UUID

from pydantic import BaseModel


class EmploymentStatusResponse(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}


class EmploymentStatusListResponse(BaseModel):
    items: list[EmploymentStatusResponse]


class AttendanceStatusResponse(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}


class AttendanceStatusListResponse(BaseModel):
    items: list[AttendanceStatusResponse]
