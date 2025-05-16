from pydantic import BaseModel, EmailStr, Field
from typing import Literal

class Student(BaseModel):
    full_name: str = Field(..., example="John Doe")
    email: EmailStr = Field(..., example="yourname@stu.cu.edu.ng")
    program: str = Field(..., example="Computer Science")
    matriculation_number: str = Field(..., example="21/1234")
    registration_number: str = Field(..., example="CU/21/1234")
    room_number: str = Field(..., example="B123")
    gender: Literal["Male", "Female"] = Field(..., example="Male")
    hall_of_residence: str = Field(..., example="Joseph Hall")
    level: Literal["100", "200", "300", "400", "500"] = Field(..., example="300")
