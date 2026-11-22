from sqlalchemy import String,Integer,Column,DateTime, func,ForeignKey, Float, Boolean
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,relationship
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__="users"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    name:Mapped[str]=mapped_column(String(100),nullable=False)
    age:Mapped[int]=mapped_column(Integer,nullable=False)
    email:Mapped[str]=mapped_column(String(100),unique=True,nullable=False)
    password:Mapped[str]=mapped_column(String(100),nullable=False)
    created_at:Mapped[datetime]=mapped_column(DateTime,server_default=func.now())
    profile:Mapped["User_profile"]=relationship(back_populates="user",uselist=False)
    workouts:Mapped[list["Workout"]]=relationship(back_populates="user")
    diets:Mapped[list["Diet"]]=relationship(back_populates="user")
    is_admin:Mapped[bool]=mapped_column(default=False,nullable=False)
    instructor_id:Mapped[int|None]=mapped_column(ForeignKey("instructors.id"),nullable=False)
    instructor:Mapped["Instructor|None"]=relationship(foreign_keys=[instructor_id])
    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")
    role:Mapped[str]=mapped_column(String(50),nullable=False,default="user")

class User_profile(Base):
    __tablename__="user_profiles"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    user_id:Mapped[int]=mapped_column(Integer,ForeignKey("users.id"),unique=True)
    height:Mapped[float]=mapped_column(Float)
    weight:Mapped[float]=mapped_column(Float)
    fitness_goal:Mapped[str]=mapped_column(String(100))
    user:Mapped[User]=relationship(back_populates="profile")

class Workout(Base):
    __tablename__="workouts"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    user_id:Mapped[int]=mapped_column(Integer,ForeignKey("users.id"))
    exercise_name:Mapped[str]=mapped_column(String(100))
    duration:Mapped[float]=mapped_column(Float)
    calories_burned:Mapped[float]=mapped_column(Float)
    user:Mapped[User]=relationship(back_populates="workouts")


class Diet(Base):
    __tablename__="diets"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    user_id:Mapped[int]=mapped_column(Integer,ForeignKey("users.id"))
    diet_plan:Mapped[str]=mapped_column(String(100))
    user:Mapped[User]=relationship(back_populates="diets")
    calories_consumed:Mapped[float]=mapped_column(Float)
    user:Mapped[User]=relationship(back_populates="diets")

class Instructor(Base):
    __tablename__="instructors"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    name:Mapped[str]=mapped_column(String(100))
    email:Mapped[str]=mapped_column(String(100))
    specialization:Mapped[str]=mapped_column(String(100))
    experience_years:Mapped[int]=mapped_column(Integer)
    price_per_month:Mapped[float]=mapped_column(Float)
    bookings: Mapped[list["Booking"]] = relationship(back_populates="instructor")
    is_available: Mapped[bool] = mapped_column(Boolean,default=True,nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"),unique=True,nullable=True)
    user:Mapped["User|None"]=relationship(foreign_keys=[user_id])

class Booking(Base):
    __tablename__="bookings"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    user_id:Mapped[int]=mapped_column(Integer,ForeignKey("users.id"))
    instructor_id:Mapped[int]=mapped_column(Integer,ForeignKey("instructors.id"))
    total_price:Mapped[float]=mapped_column(Float,nullable=False)
    start_date:Mapped[datetime]=mapped_column(DateTime,nullable=False)
    end_date:Mapped[datetime]=mapped_column(DateTime,nullable=False)
    status:Mapped[str]=mapped_column(String(50),nullable=False,default="pending")
    user:Mapped[User]=relationship(back_populates="bookings")
    instructor:Mapped[Instructor]=relationship(back_populates="bookings")
    payments: Mapped[list["Payment"]] = relationship(back_populates="booking")

class Payment(Base):
    __tablename__="payments"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    booking_id:Mapped[int]=mapped_column(Integer,ForeignKey("bookings.id"))
    razorpay_order_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    amount:Mapped[int]=mapped_column(Integer,nullable=False)
    status:Mapped[str]=mapped_column(String(50),nullable=False,default="created")
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    created_at:Mapped[datetime]=mapped_column(DateTime,server_default=func.now())
    booking: Mapped["Booking"] = relationship(back_populates="payments")