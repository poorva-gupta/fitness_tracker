from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    name: str
    age: int
    email: EmailStr
    password: str


class UserProfileCreate(BaseModel):
    user_id: int
    height: float
    weight: float
    fitness_goal: str


class WorkoutCreate(BaseModel):
    user_id: int
    exercise_name: str
    duration: float
    calories_burned: float


class WorkoutUpdate(BaseModel):
    exercise_name: str
    duration: float
    calories_burned: float


class DietCreate(BaseModel):
    user_id: int
    diet_plan: str
    calories_intake: float


class DietUpdate(BaseModel):
    diet_plan: str
    calories_intake: float


class Login(BaseModel):
    email: EmailStr
    password: str


class InstructorCreate(BaseModel):
    name: str
    email: EmailStr
    specialization: str
    experience_years: int = Field(ge=0)
    price_per_month: float = Field(gt=0)
    age:int
    password:str
    is_available: bool = True

class InstructorResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    specialization: str
    experience_years: int
    price_per_month: float
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


class InstructorUpdate(BaseModel):
    name: str
    email: EmailStr
    specialization: str
    experience_years: int = Field(ge=0)
    price_per_month: float = Field(gt=0)
    is_available: bool


class BookingUpdate(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None


class BookingResponse(BaseModel):
    id: int
    user_id: int
    instructor_id: int
    start_date: datetime
    end_date: datetime
    total_price: float
    status: str

    model_config = ConfigDict(from_attributes=True)

class PaymentVerification(BaseModel):
    razorpay_order_id:str
    razorpay_payment_id:str
    razorpay_signature:str