# Comparison: JWT Authentication vs. Session Cookie Authentication

This document compares the two different authentication & authorization systems implemented in this project side by side.

---

## 1. File Structure Overview

| Component | JWT Implementation | Session Cookie Implementation |
| :--- | :--- | :--- |
| **Route Controller** | `src/authen_authori/controller.py` (`/user/*`) | `src/authen_authori/session_controller.py` (`/session-user/*`) |
| **CLI Demo** | `src/authen_authori/interface.py` | `src/authen_authori/session_interface.py` |
| **Token / State Helper** | `src/authen_authori/security.py` | Built-in `uuid` & server dictionary / table |

---

## 2. Core Architectural Differences

| Feature | JWT (Stateless) | Session Cookie (Stateful) |
| :--- | :--- | :--- |
| **Where session is stored** | **On Client only** inside the signed token string. | **On Server** in a session dictionary / database (`SESSIONS[session_id] = user_id`). |
| **What login returns** | A token in the JSON body (`access_token`). | Nothing secret in body; sends HTTP header `Set-Cookie: session_id=...`. |
| **How client sends it back** | Must attach `Authorization: Bearer <token>` in headers manually or via `client.headers.update(...)`. | **Automatic.** Browsers and `httpx.Client` send cookies on every request without code. |
| **Revoking / Logging out** | Difficult without blacklists/expiry because token is self-contained. | **Instant.** Delete `SESSIONS[session_id]` on the server. |
| **XSS Protection** | Moderate / Weak if stored in browser `localStorage`. | Strong when marked `HttpOnly=True` (JavaScript cannot steal it). |

---

## 3. The Trade-off Summary

- **JWT:**
  - The server does **zero state lookups**. It just does math (`jwt.decode`) to confirm the signature is real.
  - *Catch:* If a token is stolen, the server cannot easily cancel it until it expires (unless you maintain a blacklist).
- **Session Cookie:**
  - The server holds a **registry** (`SESSIONS = {}`).
  - *Benefit:* Instant logout/revocation—just delete the ID from the server's memory.
  - *Catch:* If your server restarts or you have multiple server instances (load balancers), you must share the session store (e.g. in Redis or a DB table).


---

## 4. Side-by-Side Code Comparison

### A. The Login Handler

#### JWT Approach (`controller.py`):
```python
# Creates signed token string and returns it in JSON
access_token = create_access_token(data={"sub": user.email})
return UserResponse(
    email=user.email,
    access_token=access_token,
    token_type="bearer"
)
```

#### Session Cookie Approach (`session_controller.py`):
```python
# Generates random ID, saves in server memory, sets HTTP Cookie
session_id = str(uuid.uuid4())
SESSIONS[session_id] = user.id

response.set_cookie(
    key="session_id",
    value=session_id,
    httponly=True,  # JavaScript cannot read it
    max_age=1800,
    samesite="lax"
)
return {"message": "Login successful"}
```

---

### B. Extracting the Current User (`get_current_user`)

#### JWT Approach (`security.py`):
```python
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # 1. Reads token from Authorization: Bearer header
    # 2. Cryptographically validates signature with SECRET_KEY
    payload = decode_access_token(token)
    email = payload.get("sub")
    # 3. Fetches user from DB
    return db.query(UserModel).filter(UserModel.email == email).first()
```

#### Session Cookie Approach (`session_controller.py`):
```python
def get_current_user_from_session(request: Request, db: Session = Depends(get_db)):
    # 1. Reads cookie sent automatically in request.cookies
    session_id = request.cookies.get("session_id")
    # 2. Looks up user ID in server-side memory
    user_id = SESSIONS.get(session_id)
    # 3. Fetches user from DB
    return db.query(UserModel).filter(UserModel.id == user_id).first()
```

---

### C. Client-Side Code Comparison (`httpx.Client`)

#### JWT Client (`interface.py`):
```python
# Must extract token from JSON body and update client headers manually
response = client.post("/user/login", data={"username": email, "password": password})
token = response.json()["access_token"]
client.headers.update({"Authorization": f"Bearer {token}"})  # <-- MANUAL STEP
```

#### Session Cookie Client (`session_interface.py`):
```python
# No token in body; client receives Set-Cookie header and manages it automatically
response = client.post("/session-user/login", data={"username": email, "password": password})
# NO client.headers.update(...) NEEDED!
# client.cookies automatically has the session_id!
```

---

## 5. How to Run Both Demos

Start the FastAPI server:
```powershell
$env:DATABASE_KEY="sqlite:///./test.db"
uvicorn app:app --port 8011 --reload
```

### Try JWT Demo:
```powershell
python -m authen_authori.interface
```

### Try Session Cookie Demo:
```powershell
python -m authen_authori.session_interface
```

---

## 6. Detailed Session Cookie Mechanics: Register & Login Explained

### A. How `register` Works & Where `user_payload` Goes
In the registration function:
```python
@session_router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user_in: User, db: Session = Depends(get_db)) -> dict:
```
- `user_payload` does **NOT** go to `Response`.
- It enters through **`user_in: User`** (Pydantic body model parsed from the HTTP request body).
- `response: Response` is **not** an incoming payload; it is a FastAPI utility object used exclusively to manipulate the outgoing HTTP response (e.g., stamping headers or cookies).

### B. Line-by-Line Breakdown of the Login Session Setup
```python
# 1. Generate random unique session ID
session_id = str(uuid.uuid4())
```
Generates an unguessable 128-bit random string (e.g. `"c9bf9e57-1685-4c89-bafb-ff5af830be8a"`). This string contains zero user info.

```python
# 2. Store session in server memory
SESSIONS[session_id] = user.id
```
Saves the mapping in the server's memory registry (`SESSIONS` dictionary). The server records: *"Whoever holds this `session_id` owns User ID X"*.

```python
# 3. Tell client to save cookie
response.set_cookie(
    key=SESSION_COOKIE_NAME,
    value=session_id,
    max_age=SESSION_EXPIRE_SECONDS,
    httponly=True,
    samesite="lax"
)
```
- Instructs FastAPI to add an HTTP response header: `Set-Cookie: session_id=c9bf9e57...; Max-Age=1800; HttpOnly; SameSite=lax`.
- `httponly=True`: Prevents browser JavaScript (`document.cookie`) from accessing the session ID, protecting against XSS attacks.
- `max_age=1800`: Sets browser cookie expiration to 30 minutes.
- `samesite="lax"`: Protects against Cross-Site Request Forgery (CSRF).

### C. Is `session_id` Part of the Payload?
**No.** `session_id` is **never** placed in the HTTP body (payload). It is placed in the **HTTP Response Headers** via `Set-Cookie`.
- **Client storage:** The browser / `httpx.Client` stores it in its cookie jar.
- **Server storage:** The mapping (`session_id -> user.id`) is stored in the server's `SESSIONS` dictionary.
