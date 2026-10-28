from pydantic import BaseModel,EmailStr,Field
from datetime import datetime

class UserCreate(BaseModel):
    name:str
    age:int
    email:EmailStr
    password:str

class UserProfileCreate(BaseModel):
    user_id:int
    height:float
    weight:float
    fitness_goal:str

class WorkoutCreate(BaseModel):
    user_id:int
    exercise_name:str
    duration:float
    calories_burned:float


class WorkoutUpdate(BaseModel):
    exercise_name: str
    duration: float
    calories_burned: float

class DietCreate(BaseModel):
    user_id:int
    diet_plan:str
    calories_intake:float
class Dietupdate(BaseModel):
    diet_plan:str
    calories_intake:float

class Login(BaseModel):
    email:EmailStr
    password:str

class InstructorCreate(BaseModel):
    name:str
    email:EmailStr
    specialization:str
    experience_years:int=Field(ge=0)
    price_per_month:float=Field(gt=0)

class InstructorResponse(BaseModel):
    id:int
    name:str
    email:EmailStr
    specialization:str
    experience_years:int
    price_per_month:float
    is_available:bool
    class Config:
        from_attributes=True

class InstructorUpdate(BaseModel):
    name:str
    email:EmailStr
    specialization:str
    experience_years:int=Field(ge=0)
    price_per_month:float=Field(gt=0)
    is_available:bool