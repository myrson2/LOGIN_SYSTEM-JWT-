from pydantic import BaseModel, ValidationError, field_validator


class User(BaseModel):
    email: str
    password: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        v = v.strip()

        if not v.endswith("@example.com"):
            raise ValueError("Email address must end with '@example.com'")

        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Prevent the bcrypt 72-byte limit error
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password must be less than 72 bytes long')

        return v.strip()

class UserResponse(BaseModel):
    email: str
    access_token: str
    token_type: str
