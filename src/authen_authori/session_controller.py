import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from authen_authori.usermodel import UserModel, get_db
from authen_authori.userschema import User, UserProfileResponse
from authen_authori.security import get_password_hash, verify_password

# Separate router dedicated entirely to session cookies
session_router = APIRouter(prefix="/session-user", tags=["session-cookie-auth"])

# Cookie configuration
SESSION_COOKIE_NAME = "session_id"
SESSION_EXPIRE_SECONDS = 1800  # 30 minutes

# In-memory server-side session store
# Maps: session_id -> user_id
# Note: In production this would typically be stored in Redis or database table
SESSIONS: dict[str, int] = {}


# =====================================================================
# 1. Dependency: Get Current User from Cookie
# =====================================================================
def get_current_user_from_session(
    request: Request,
    db: Session = Depends(get_db)
) -> UserModel:
    """
    Unlike JWT where we decode a cryptographic string from the Authorization header,
    here the client browser/HTTP client sends a cookie automatically.
    We read the session_id cookie and look up the user_id in server-side storage.
    """
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id or session_id not in SESSIONS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated or session expired"
        )

    user_id = SESSIONS[session_id]
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user


# =====================================================================
# 2. Authorization: Role Checker
# =====================================================================
def require_session_role(required_role: str):
    """Checks whether the session-authenticated user has the necessary role."""
    def role_checker(
        current_user: UserModel = Depends(get_current_user_from_session)
    ) -> UserModel:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires '{required_role}' role"
            )
        return current_user
    return role_checker


# =====================================================================
# 3. Endpoints
# =====================================================================
@session_router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user_in: User, db: Session = Depends(get_db)) -> dict:
    existing = db.query(UserModel).filter(UserModel.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = get_password_hash(user_in.password)
    new_user = UserModel(email=user_in.email, password=hashed_pw, role=user_in.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"email": new_user.email, "id": new_user.id, "role": new_user.role}


@session_router.post("/login", status_code=status.HTTP_200_OK)
def login_user(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login endpoint:
    1. Validates password.
    2. Creates a random, opaque session_id.
    3. Saves session_id -> user.id on the server (in SESSIONS).
    4. Sets the HTTP Set-Cookie header on the response.
    Notice: No token string is returned in the response body!
    """
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    # Generate random unique session ID
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = user.id

    # Tell client to save cookie
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        max_age=SESSION_EXPIRE_SECONDS,
        httponly=True,  # Protects against XSS (JavaScript cannot read this cookie)
        samesite="lax"
    )

    return {
        "message": "Login successful! Session cookie set.",
        "email": user.email,
        "role": user.role
    }


@session_router.post("/logout", status_code=status.HTTP_200_OK)
def logout_user(request: Request, response: Response):
    """
    Logout is instantaneous on server:
    1. Delete the session from server memory.
    2. Tell the client to delete the cookie.
    """
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id and session_id in SESSIONS:
        del SESSIONS[session_id]

    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"message": "Logged out successfully. Session destroyed."}


@session_router.get("/me", response_model=UserProfileResponse)
def read_current_user(current_user: UserModel = Depends(get_current_user_from_session)):
    return current_user


@session_router.get("/student/grades")
def view_student_grades(student: UserModel = Depends(require_session_role("student"))):
    return {
        "message": f"Welcome Student {student.email} (via Session Cookie)!",
        "courses": [
            {"subject": "Mathematics", "grade": "A"},
            {"subject": "Computer Science", "grade": "A+"}
        ]
    }


@session_router.get("/teacher/portal")
def view_teacher_portal(teacher: UserModel = Depends(require_session_role("teacher"))):
    return {
        "message": f"Welcome Teacher {teacher.email} (via Session Cookie)!",
        "controls": "Full access to grade submissions and syllabus editing."
    }
