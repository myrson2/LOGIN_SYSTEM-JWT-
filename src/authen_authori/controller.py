import email

from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session

from authen_authori.usermodel import UserModel, get_db
from authen_authori.userschema import User

router = APIRouter(prefix="/user", tags=["authen"])

@router.get("/")
def read_root():
    return {"Hello": "World"}

@router.post('/register', status_code=status.HTTP_201_CREATED)
async def login_user(users: User, db: Session = Depends(get_db)) -> dict:
    user = UserModel(**users.model_dump())

    db.add(user)
    db.commit()
    db.refresh(user) # Refresh to get the generated ID
    return { "email": user.email }

