from datetime import date, time
from pydantic import BaseModel, EmailStr
from enum import Enum


class UserRole(str, Enum):
    student            = "student"
    trainer            = "trainer"
    institution        = "institution"
    programme_manager  = "programme_manager"
    monitoring_officer = "monitoring_officer"

class attendance_status(str, Enum):
    present = "present"
    absent = "absent"
    late = "late"

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class BatchRequest(BaseModel):
    name: str


class Create_Sessions(BaseModel):
    batch_id: int
    title: str
    date: date
    start_time: time
    end_time: time

class Mark_Attendance(BaseModel):
    session_id: int
    status:attendance_status

class JoinClassRequest(BaseModel):
    token:str



