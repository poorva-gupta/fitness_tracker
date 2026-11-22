
import math
import razorpay
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from dotenv import dotenv_values
from schemas import BookingResponse, UserCreate, UserProfileCreate,WorkoutCreate,WorkoutUpdate,DietCreate,DietUpdate,Login,InstructorCreate,InstructorResponse,InstructorUpdate,PaymentVerification
from database import Config, get_db
from models import Booking, User, User_profile, Workout,Diet,Instructor,Payment
from pwdlib import PasswordHash
import jwt
from datetime import datetime,timedelta,timezone
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from rag.rag_routes import router as rag_router
from fastapi.responses import FileResponse
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
RAZOR_APIKEY = os.getenv("RAZOR_APIKEY")
RAZOR_SECRET = os.getenv("RAZOR_SECRET")
print("Key ID loaded:", bool(RAZOR_APIKEY))
print("Secret loaded:", bool(RAZOR_SECRET))
print("Key mode:", RAZOR_APIKEY[:8] if RAZOR_APIKEY else "Missing")
Client=razorpay.Client(auth=(RAZOR_APIKEY,RAZOR_SECRET))
app = FastAPI()
app.include_router(rag_router)
password_hash=PasswordHash.recommended()
env = dotenv_values(".env")
SECRET_KEY=env.get("SECRET_KEY")
ALGORITHM=env.get("ALGORITHM","HS256")
ACCESS_TOKEN_EXPIRE_MINUTES=int(env.get("ACCESS_TOKEN_EXPIRE_MINUTES","30"))
db_config = Config(env)
app.state.db_config = db_config
db_config.set_up()
oauth2_scheme = HTTPBearer()

def create_access_token(user_id:int):
    expire=datetime.now(timezone.utc)+timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload={
        "sub":str(user_id),
        "exp":expire
    }
    token=jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return token
@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )

    new_user = User(
        name=user.name,
        age=user.age,
        email=user.email,
        password=password_hash.hash(user.password),
        role="user"
    )

    db.add(new_user)
    db.commit()

    return {"message": "User Created Successfully"}


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = int(payload["sub"])

    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user

def get_current_admin(
        current_user:User=Depends(get_current_user)
):
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Admin access required"
            )
        return current_user

       
@app.get("/payment")
def payment_page():
    file_path = os.path.join(os.path.dirname(__file__), "payment.html")
    return FileResponse(file_path)
@app.post("/user_profile")
def create_user_profile(profile:UserProfileCreate,db:Session=Depends(get_db),current_user: User = Depends(get_current_user)):
    if profile.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot create another user's profile"
    )
    existing_user=db.query(User).filter(User.id==profile.user_id).first()
    if not existing_user:
        raise HTTPException(
            status_code=404,
            detail="user not found"
        )
    if existing_user.profile:
        raise HTTPException(
            status_code=409,
            detail="User profile already exists"
        )
    new_profile=User_profile(
        user_id=profile.user_id,
        height=profile.height,
        weight=profile.weight,
        fitness_goal=profile.fitness_goal

    )
    db.add(new_profile)
    db.commit()
    return {"message":"user profile created successfully"}


@app.get("/user_profile/{user_id}")
def get_user_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You cannot access another user's profile"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if not user.profile:
        raise HTTPException(
            status_code=404,
            detail="User profile not found"
        )

    return user.profile


@app.put("/user_profile/{user_id}")
def update_user_profile(
    user_id: int,
    profile: UserProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.id!=user_id:
        raise HTTPException(
            status_code=403,
            detail="you cannot update another user's profile"
        )
    
    user=db.query(User).filter(User.id==user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="user not found"
        )
    if not user.profile:
        raise HTTPException(
            status_code=404,
            detail="user profile not found"
        )
    user.profile.height = profile.height
    user.profile.weight = profile.weight
    user.profile.fitness_goal = profile.fitness_goal
    db.commit()
    return {"message": "user profile updated successfully"}

@app.delete("/user_profile/{user_id}")
def delete_user_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot delete another user's profile"
        )
    user=db.query(User).filter(User.id==user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="user not found"
        )
    if not user.profile:
        raise HTTPException(
            status_code=404,
            detail="user profile not found"
        )
    db.delete(user.profile)
    db.commit()
    return {"message": "user profile deleted successfully"}

@app.post("/workout")
def create_workout(
    workout: WorkoutCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if workout.user_id!=current_user.id:
        raise HTTPException(
            status_code=403,
            detail="you cannot create a workout for another user"
        )
    user=db.query(User).filter(User.id==workout.user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="user not found"
        )
    new_workout=Workout(
        user_id=workout.user_id,
        exercise_name=workout.exercise_name,
        duration=workout.duration,
        calories_burned=workout.calories_burned
    )
    db.add(new_workout)
    db.commit()
    return{"message":"workout created successfully"}

@app.get("/workouts/{user_id}")
def get_workouts(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You cannot access another user's workouts"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="user not found"
        )

    return user.workouts

@app.put("/update_workout/{workout_id}")
def update_workout(
    workout_id: int,
    workout: WorkoutUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing_workout = db.query(Workout).filter(
        Workout.id == workout_id
    ).first()

    if not existing_workout:
        raise HTTPException(
            status_code=404,
            detail="workout not found"
        )

    if existing_workout.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot update another user's workout"
        )

    existing_workout.exercise_name = workout.exercise_name
    existing_workout.duration = workout.duration
    existing_workout.calories_burned = workout.calories_burned

    db.commit()

    return {"message": "workout updated successfully"}
@app.delete("/delete_workout/{workout_id}")
def delete_workout(
    workout_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing_workout = db.query(Workout).filter(
        Workout.id == workout_id
    ).first()

    if not existing_workout:
        raise HTTPException(
            status_code=404,
            detail="workout not found"
        )

    if existing_workout.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot delete another user's workout"
        )

    db.delete(existing_workout)
    db.commit()

    return {"message": "workout deleted successfully"}

@app.post("/diet")
def create_diet(
    diet: DietCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if diet.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot create a diet plan for another user"
        )

    user = db.query(User).filter(
        User.id == diet.user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    new_diet = Diet(
        user_id=diet.user_id,
        diet_plan=diet.diet_plan,
        calories_intake=diet.calories_intake
    )

    db.add(new_diet)
    db.commit()

    return {
        "message": "Diet created successfully"
    }

@app.get("/diets/{user_id}")
def get_diets(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You cannot access another user's diets"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="user not found"
        )

    return user.diets
@app.put("/update_diet/{diet_id}")
def update_diet(
    diet_id: int,
    diet: DietCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing_diet = db.query(Diet).filter(
        Diet.id == diet_id
    ).first()

    if not existing_diet:
        raise HTTPException(
            status_code=404,
            detail="diet not found"
        )

    if existing_diet.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot update another user's diet"
        )

    existing_diet.diet_plan = diet.diet_plan
    existing_diet.calories_intake = diet.calories_intake

    db.commit()

    return {"message": "diet updated successfully"}

@app.delete("/delete_diet/{diet_id}")
def delete_diet(
    diet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing_diet = db.query(Diet).filter(
        Diet.id == diet_id
    ).first()

    if not existing_diet:
        raise HTTPException(
            status_code=404,
            detail="diet not found"
        )

    if existing_diet.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot delete another user's diet"
        )

    db.delete(existing_diet)
    db.commit()

    return {"message": "diet deleted successfully"}

@app.get("/diet_Plan")
def get_diet_plan():
    return [
        {
            "plan_id":1,
            "plan_name":"Weight Loss Plan",
            "description":"A diet plan focused on reducing calorie intake and promoting weight loss.",
        },
        {
            "plan_id":2,
            "plan_name":"Muscle Gain Plan",
            "description":"A diet plan designed to support muscle growth and strength training.",
        },
        {
            "plan_id":3,
            "plan_name":"Balanced Diet Plan",
            "description":"A diet plan that emphasizes a balanced intake of nutrients for overall health.",
        }
    ]


@app.get("/dashboard/{user_id}")
def get_dashboard(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You cannot access another user's dashboard"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    workouts = user.workouts
    diets = user.diets

    total_workouts = len(workouts)
    total_duration = sum(workout.duration for workout in workouts)
    total_calories_burned = sum(
        workout.calories_burned for workout in workouts
    )
    total_calories_intake = sum(
        diet.calories_intake for diet in diets
    )

    return {
        "User_id": user.id,
        "total_workouts": total_workouts,
        "total_workout_duration": total_duration,
        "total_calories_burned": total_calories_burned,
        "total_calories_intake": total_calories_intake
    }



@app.post("/login")
def login(user_data:Login,db:Session=Depends(get_db)):
    user=db.query(User).filter(User.email==user_data.email).first()
    if not user or not password_hash.verify(
        user_data.password,
        user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    access_token=create_access_token(user.id)
    return{
        "message":"Login successfull",
        "access_token":access_token,
        "token_type":"bearer"
    }

@app.post("/instructors",response_model=InstructorResponse)
def create_instructor(
    instructor_data:InstructorCreate,
    db:Session=Depends(get_db),
    current_admin:User=Depends(get_current_admin)
):
    existing_user = db.query(User).filter(User.email == instructor_data.email).first()
    if existing_user:
        raise HTTPException(
        status_code=409,
        detail="Email already exists"
    )
    new_user=User(
            name=instructor_data.name,
            age=instructor_data.age,
            email=instructor_data.email,
            password=password_hash.hash(instructor_data.password),
            role="instructor",
            is_admin=False
        )
    db.add(new_user)
    db.flush()
    instructor=Instructor(
        name=instructor_data.name,
        email=instructor_data.email,
        specialization=instructor_data.specialization,
        experience_years=instructor_data.experience_years,
        price_per_month=instructor_data.price_per_month,
        is_available=instructor_data.is_available,
        user_id=new_user.id

    )
    try:
        db.add(new_user)
        db.flush()
        instructor.user_id=new_user.id
        db.add(instructor)
        db.commit()
    except Exception as e:
        db.rollback()
        raise

    return instructor

@app.get("/instructors",response_model=list[InstructorResponse])
def get_instructors(db:Session=Depends(get_db)):
    instructors=(
        db.query(Instructor).filter(Instructor.is_available==True).all()
    )
    return instructors


@app.get(
    "/instructors/{instructor_id}",
    response_model=InstructorResponse
)
def get_instructor(
    instructor_id: int,
    db: Session = Depends(get_db)
):
    instructor = (
        db.query(Instructor)
        .filter(
            Instructor.id == instructor_id,
            Instructor.is_available == True).first()
        
    )

    if not instructor:
        raise HTTPException(
            status_code=404,
            detail="Instructor not found"
        )
    return instructor

@app.put("/instructors/{instructor_id}",response_model=InstructorResponse)
def update_instructor(
    instructor_id:int,
    instructor_data:InstructorUpdate,
    db:Session=Depends(get_db),
    current_admin:User=Depends(get_current_admin)
):
    instructor=(db.query(Instructor).filter(Instructor.id==instructor_id).first())
    if not instructor:
        raise HTTPException(
            status_code=404,
            detail="instructor not found"
        )
    instructor.name = instructor_data.name
    instructor.email = instructor_data.email
    instructor.specialization = instructor_data.specialization
    instructor.experience_years = instructor_data.experience_years
    instructor.price_per_month = instructor_data.price_per_month
    instructor.is_available = instructor_data.is_available
    db.commit()
    return instructor

@app.delete("/instructors/{instructor_id}")
def deactivate_instructor(
    instructor_id:int,
    db:Session=Depends(get_db),
    current_admin:User=Depends(get_current_admin)
):
    instructor=(db.query(Instructor).filter(Instructor.id==instructor_id).first())
    if not instructor:
        raise HTTPException(
            status_code=404,
            detail="Instructor not found"
        )
    instructor.is_available=False
    db.commit()
    return{
        "message":"Instructor deactivated successfully"
    }

@app.post("/choose_instructor/{instructor_id}")
def choose_instructor(
    instructor_id:int,
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
    
):
    instructor=(db.query(Instructor).filter(Instructor.id==instructor_id,Instructor.is_available==True).first())
    if not instructor:
        raise HTTPException(
            status_code=404,
            detail="Instructor not found or unavailable"
        )
    current_user.instructor_id=instructor.id
    db.commit()
    return{
        "message":"Instructor selected successfully",
        "instructor_id":current_user.instructor_id,
        "instructor_name":instructor.name
    }


@app.get("/my_instructor")
def get_my_instructor(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.instructor_id is None:
        return {
            "message": "You have not selected an instructor"
        }

    instructor = (
        db.query(Instructor)
        .filter(Instructor.id == current_user.instructor_id)
        .first()
    )

    if not instructor:
        raise HTTPException(
            status_code=404,
            detail="Selected instructor not found"
        )

    return instructor


@app.delete("/my_instructor")
def remove_my_instructor(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.instructor_id is None:
        raise HTTPException(
            status_code=404,
            detail="You have not selected an instructor"
        )

    current_user.instructor_id = None

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Instructor selection removed successfully"
    }

@app.post("/bookings", response_model=BookingResponse)
def create_booking(
    instructor_id: int,
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    instructor = db.query(Instructor).filter(
        Instructor.id == instructor_id,
        Instructor.is_available == True
    ).first()

    if not instructor:
        raise HTTPException(
            status_code=404,
            detail="Instructor not found or unavailable"
        )

    if start_date >= end_date:
        raise HTTPException(
            status_code=400,
            detail="Invalid booking dates"
        )

    if start_date < datetime.now():
        raise HTTPException(
            status_code=400,
            detail="Booking start date cannot be in the past"
        )

    total_days = (end_date - start_date).days
    duration_months = math.ceil(total_days / 30)

    total_price = duration_months * instructor.price_per_month

    new_booking = Booking(
        user_id=current_user.id,
        instructor_id=instructor_id,
        start_date=start_date,
        end_date=end_date,
        total_price=total_price,
        status="pending"
    )

    try:
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Booking creation failed"
        )

    return new_booking

@app.get("/bookings",response_model=list[BookingResponse])
def get_bookings(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    bookings=db.query(Booking).filter(Booking.user_id==current_user.id).all()
    if not bookings:
        raise HTTPException(
            status_code=404,
            detail="no bookings found"
        )
    return bookings

@app.delete("/bookings/{booking_id}")
def cancel_booking(booking_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    booking=db.query(Booking).filter(Booking.id==booking_id,Booking.user_id==current_user.id).first()
    if not booking:
        raise HTTPException(
            status_code=404,
            detail="booking not found"
        )
    if booking.status!="pending":
        raise HTTPException(
            status_code=400,
            detail="only pending bookings can be canceled"
        )
   
    db.delete(booking)
    db.commit()
    return{
        "message":"booking canceled successfully"
    }

@app.post("/payments/create_order/{booking_id}")
def create_payment_order(booking_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.instructor_id is None:
        raise HTTPException(status_code=400,detail="you have not selected an instructor")
    instructor=db.query(Instructor).filter(Instructor.id==current_user.instructor_id).first()
    if not instructor:
        raise HTTPException(status_code=404,detail="instructor not found")
    booking=db.query(Booking).filter(Booking.id==booking_id,Booking.user_id==current_user.id).first()
    if not booking:
        raise HTTPException(status_code=404,detail="booking not found")
    payment = db.query(Payment).filter(
    Payment.booking_id == booking.id,
    Payment.status == "success"
).first()
    if payment:
        raise HTTPException(status_code=400,detail="payment order already exists for this booking")
    amount=int(round(booking.total_price*100))
    order_data={
        "amount":amount,
        "currency":"INR",
        "receipt":f"booking_{booking.id}"
    }
    order=Client.order.create(data=order_data)
    new_payment=Payment(
        booking_id=booking.id,
        razorpay_order_id=order["id"],
        amount=order["amount"],
        status="created",
        currency="INR"
    )
    db.add(new_payment)
    db.commit()
    return {
        "order_id":order["id"],
        "amount":order["amount"],
        "currency":order["currency"],
        "key_id":RAZOR_APIKEY
    }

@app.post("/payments/verify")
def verify_payment(data:PaymentVerification,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    payment=db.query(Payment).filter(Payment.razorpay_order_id==data.razorpay_order_id).first()
    if not payment:
        raise HTTPException(status_code=404,detail="payment order not found")
    booking=db.query(Booking).filter(Booking.id==payment.booking_id,Booking.user_id==current_user.id).first()
    if not booking or booking.user_id!=current_user.id:
        raise HTTPException(status_code=403,detail="not authorized")
    try:
        Client.utility.verify_payment_signature({
            "razorpay_order_id":data.razorpay_order_id,
            "razorpay_payment_id":data.razorpay_payment_id,
            "razorpay_signature":data.razorpay_signature
        })
    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(status_code=400,detail="payment signature verification failed")
    payment.razorpay_payment_id=data.razorpay_payment_id
    payment.razorpay_signature=data.razorpay_signature
    payment.status="success"
    booking.status="confirmed"
    db.commit()
    return{"message":"payment verified",
           "booking_status":booking.status,
           "payment_status":payment.status}
           

@app.get("/payments/{payment_id}")
def get_payment_status(payment_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    payment=db.query(Payment).filter(Payment.id==payment_id).first()
    if not payment:
        raise HTTPException(status_code=404,detail="payment not found")
    booking=db.query(Booking).filter(Booking.id==payment.booking_id).first()
    if not booking or booking.user_id!=current_user.id:
        raise HTTPException(status_code=403,detail="not authorized")
    return {
        "payment_id": payment.id,
        "booking_id": payment.booking_id,
        "amount": payment.amount / 100,
        "currency": payment.currency,
        "payment_status": payment.status,
        "razorpay_order_id": payment.razorpay_order_id,
        "razorpay_payment_id": payment.razorpay_payment_id
    }
