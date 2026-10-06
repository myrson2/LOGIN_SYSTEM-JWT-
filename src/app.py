from fastapi import FastAPI

from authen_authori.controller import router as auth_router
from authen_authori.usermodel import create_tables

app = FastAPI()
app.include_router(auth_router)

@app.on_event("startup")
def startup() -> None:
	create_tables()