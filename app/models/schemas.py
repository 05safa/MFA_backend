from pydantic import BaseModel, EmailStr, Field

class Register(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class Login(BaseModel):
    email: EmailStr
    password: str
