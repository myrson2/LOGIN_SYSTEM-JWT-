import email
from datetime import timedelta

from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from authen_authori.usermodel import UserModel, get_db
from authen_authori.userschema import User, UserResponse, UserProfileResponse
from authen_authori.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    oauth2_scheme,
    get_current_user,
    require_role,
)

router = APIRouter(prefix="/user", tags=["authen"])

@router.get("/me", response_model=UserProfileResponse)
def read_current_user(current_user: UserModel = Depends(get_current_user)):
    return current_user

@router.get("/student/grades")
def view_student_grades(student: UserModel = Depends(require_role("student"))):
    return {
        "message": f"Welcome Student {student.email}!",
        "courses": [
            {"subject": "Mathematics", "grade": "A"},
            {"subject": "Computer Science", "grade": "A+"}
        ]
    }

@router.get("/teacher/portal")
def view_teacher_portal(teacher: UserModel = Depends(require_role("teacher"))):
    return {
        "message": f"Welcome Teacher {teacher.email}!",
        "controls": "Full access to grade submissions and syllabus editing."
    }

@router.get("/admin/dashboard")
def admin_dashboard(admin: UserModel = Depends(require_role("admin"))):
    return {
        "message": f"Welcome Admin {admin.email}! Access granted to sensitive resources.",
        "admin_id": admin.id
    }

@router.post('/register', status_code=status.HTTP_201_CREATED)
async def register_user(users: User, db: Session = Depends(get_db)) -> dict:
    # Check if user already exists
    existing_user = db.query(UserModel).filter(UserModel.email == users.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_password = get_password_hash(users.password)
    user = UserModel(email=users.email, password=hashed_password, role=users.role)

    db.add(user)
    db.commit()
    db.refresh(user) # Refresh to get the generated ID
    return { "email": user.email, "id": user.id, "role": user.role }


@router.post('/login', status_code=status.HTTP_200_OK, response_model=UserResponse)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> UserResponse:
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return UserResponse(
        email=user.email,
        access_token=access_token,
        token_type="bearer"
    )

