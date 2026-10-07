import email
from datetime import timedelta

from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from authen_authori.usermodel import UserModel, get_db
from authen_authori.userschema import User
from authen_authori.security import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/user", tags=["authen"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/login")

@router.get("/")
def read_root(token: str = Depends(oauth2_scheme)):
    return {"message": "You are authenticated!", "token": token}

@router.post('/register', status_code=status.HTTP_201_CREATED)
async def register_user(users: User, db: Session = Depends(get_db)) -> dict:
    # Check if user already exists
    existing_user = db.query(UserModel).filter(UserModel.email == users.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_password = get_password_hash(users.password)
    user = UserModel(email=users.email, password=hashed_password)

    db.add(user)
    db.commit()
    db.refresh(user) # Refresh to get the generated ID
    return { "email": user.email, "id": user.id }


@router.post('/login')
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

