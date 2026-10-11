# JWT Authentication & Authorization Guide (FastAPI)

This guide explains how JWT authentication works in this project and how to use `current_user` for authentication and role-based authorization.

---

## 1. Payload (Body) vs. Metadata (Headers)

When communicating with any web API, an HTTP request is made of **two distinct layers**:

```
┌────────────────────────────────────────────────────────┐
│  THE ENVELOPE / METADATA (HTTP Headers)                │
│  - Host: 127.0.0.1:8011                                │
│  - Content-Type: application/json                      │
│  - Authorization: Bearer eyJhbGciOiJIUz... <── TAG!    │
│  - User-Agent: python-httpx                            │
│                                                        │
│   ┌────────────────────────────────────────────────┐   │
│   │  THE GIFT INSIDE / PAYLOAD (HTTP Body)         │   │
│   │                                                │   │
│   │  {"email": "student@example.com"}              │   │
│   │  (The actual content/data being transferred)   │   │
│   │                                                │   │
│   └────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

### The Gift Tag Analogy
- **The Box & Gift Tag (Headers / Metadata):** Extra information describing the parcel. The **gift tag** says: *"From Alice (Signed Badge: Bearer <token>)"*.
- **The Contents (Payload / Body):** The actual item inside the parcel.

### Why Authorization CANNOT go inside the Payload (Body)
1. **`GET` requests don't have a body:** 
   When accessing routes like `GET /user/student/grades` or `GET /user/me`, HTTP standards state that `GET` requests should **not** have a body. If credentials lived in the payload, you couldn't secure `GET` requests!
2. **Fast Gatekeeping:**
   The server's security guard (FastAPI's `OAuth2PasswordBearer`) checks the "gift tag" (Header) immediately. If the badge is missing or expired, it rejects the request (`401 Unauthorized`) right away **without wasting server resources unwrapping the body**.

### Why `client.headers.update(...)` is needed
When you log in, the server gives you an `access_token` in the response body. If you just leave it inside a variable (e.g., `user["access_token"]`), it stays in your pocket.

Running:
```python
client.headers.update({"Authorization": f"Bearer {token}"})
```
updates the **envelope's metadata**. From that moment on, your HTTP client automatically stamps `Authorization: Bearer <token>` onto the outside of **every single request** you send.

---

## 2. Authentication vs Authorization

- **Authentication (AuthN):** *"Who are you?"*
  - The client logs in with email/password and receives a signed JWT access token.
  - On subsequent requests, the client sends this token in the header:
    ```http
    Authorization: Bearer <your_access_token>
    ```
  - The server verifies the token signature and extracts the user (`sub`).

- **Authorization (AuthZ):** *"What are you allowed to do?"*
  - Once the user is identified (`current_user`), the server checks their permissions or roles (e.g., standard `student` vs `teacher` vs `admin`) before granting access to specific endpoints.

---

## 2. Implementing `get_current_user`

Add a dependency function that reads the bearer token, decodes it, and retrieves the user record from the database.

### In `src/authen_authori/security.py`

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from authen_authori.usermodel import UserModel, get_db

# Tells FastAPI where clients obtain tokens (used for Swagger UI interactive login)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Decode token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    # 2. Extract user identity
    email: str | None = payload.get("sub")
    if email is None:
        raise credentials_exception

    # 3. Retrieve user from database
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if user is None:
        raise credentials_exception

    return user
```

---

## 3. Protecting Endpoints (Authentication)

Use `Depends(get_current_user)` on your routes to protect them. Only requests with valid tokens will succeed.

### In `src/authen_authori/controller.py`

```python
from authen_authori.security import get_current_user
from authen_authori.usermodel import UserModel

@router.get("/me")
def read_current_user(current_user: UserModel = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email
    }
```

---

## 4. Role-Based Authorization

To restrict endpoints to specific roles (e.g. `admin`):

### 1) Add a role column to `UserModel` (`src/authen_authori/usermodel.py`)

```python
class UserModel(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, default="user")  # 'user', 'admin', etc.
```

### 2) Create a Role Checker Dependency Factory (`src/authen_authori/security.py`)

```python
def require_role(required_role: str):
    def role_checker(current_user: UserModel = Depends(get_current_user)) -> UserModel:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker
```

### 3) Protect Admin Endpoints (`src/authen_authori/controller.py`)

```python
from authen_authori.security import require_role

@router.get("/admin/dashboard")
def admin_only_route(admin_user: UserModel = Depends(require_role("admin"))):
    return {
        "message": f"Welcome Admin {admin_user.email}!",
        "access": "granted"
    }
```
