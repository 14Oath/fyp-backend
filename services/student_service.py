from models.student_model import Student
from database import students_collection

async def create_student_service(student: Student):
    existing = await students_collection.find_one({"matriculation_number": student.matriculation_number})
    if existing:
        return {"message": "Student already exists"}
    await students_collection.insert_one(student.dict())
    return {"message": "Student created"}
