# JWT Authentication & Password Hashing Tutorial

This tutorial explains how we integrated JSON Web Tokens (JWT) for authentication and encrypted (hashed) user passwords in our FastAPI application.

## 1. What are we trying to achieve?
- **Password Encryption:** We don't want to save plain text passwords in the database. If the database gets leaked, everyone's passwords would be exposed. We use a hashing algorithm (`bcrypt`) to turn the password into a scrambled string that can't be reversed.
- **JWT Authentication:** When a user logs in with their email and password, we need a way to "remember" them so they don't have to log in for every single request. We create a JWT (JSON Web Token)—a secure, digital ID card. The user sends this token with their future requests to prove who they are.

## 2. Steps we took to build this

### Step 1: Install Required Packages
We added the necessary libraries to handle password hashing and JWT generation:
```bash
uv add bcrypt pyjwt
```
- **`bcrypt`**: The core mathematical engine that securely hashes (encrypts) passwords.
- **`pyjwt`**: Creates and decodes our JWT tokens.

#### A Note on `bcrypt` vs `passlib`:
Initially, you might see tutorials recommending `passlib`. 
- **`bcrypt`** is the actual engine doing the encryption. 
- **`passlib`** is just a "wrapper" or middleman that can talk to many different encryption engines. 
Because `passlib` has not been updated in years, it causes crashing bugs when trying to talk to newer versions of the `bcrypt` engine. To fix this, we removed `passlib` and wired our app directly to the `bcrypt` library. This is the modern, faster, and bug-free approach!

#### The 72-Byte Limit:
The `bcrypt` algorithm has a strict mathematical rule: **it ignores everything after the 72nd byte of a password**. 
To prevent errors or security issues, we updated our Pydantic `User` schema to explicitly reject passwords longer than 72 bytes.

### Step 2: Set up the Security Module (`security.py`)
We created a new file called `security.py` to handle the heavy lifting:
- **`get_password_hash`**: Takes a plain text password and scrambles it using bcrypt.
- **`verify_password`**: Compares a plain password from a login attempt with the hashed password stored in the database.
- **`create_access_token`**: Generates the JWT token when a user logs in successfully. It packs the user's email inside and gives the token an expiration time (e.g., 30 minutes).

### Step 3: Update User Registration (`/register` route)
When a new user signs up:
1. We check if their email is already in the database.
2. If it's a new email, we take their password and hash it using our `get_password_hash` function.
3. We save the user to the database with the **hashed password**, not the plain one.

### Step 4: Add User Login (`/login` route)
When a user wants to log in:
1. They send their email (username) and password.
2. We look up their email in the database.
3. We take the password they just typed and use `verify_password` to see if it matches the hashed password from the database.
4. If it matches, we generate a JWT using `create_access_token` and send it back to the user.

### Step 5: Secure Other Routes
To protect a route (like the root `/` endpoint), we use FastAPI's `OAuth2PasswordBearer`. This tells FastAPI: *"Hey, anyone who wants to access this route MUST provide a valid JWT token in their request header."*
If they don't have a token, FastAPI automatically rejects their request!

## Summary
1. **Register:** User gives password ➡️ We hash it ➡️ Save to DB.
2. **Login:** User gives password ➡️ We hash and compare with DB ➡️ If match, send back a JWT.
3. **Access Protected Route:** User sends JWT ➡️ We verify the JWT ➡️ Let them in!

By doing this, our app is now secure and follows modern web authentication practices!
