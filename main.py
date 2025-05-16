from typing import Union
from fastapi import FastAPI, HTTPException
from models.student_model import Student
from services.student_service import create_student_service


app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/students/create")
def create_student(student: Student):
    response = create_student_service(student)
    # if not response["success"]:
    #     raise HTTPException(status_code=400, detail=response["message"])
    return response