from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., pattern=r"^\S+@\S+\.\S+$")

class UserResponse(BaseModel):
    id:int
    name:str
    email:str
