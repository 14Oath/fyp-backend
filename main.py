from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import EmailStr
from typing import Literal
import numpy as np
import cv2

from models.student_model import Student
from face_embedding import get_embedding_from_image
from face_recognition import FaceRegistrar, FaceVerifier
import face_embeddings
from database import init_db

# App setup and lifespan context
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 App is starting up")
    grid_fs_bucket = await init_db()
    if not grid_fs_bucket:
        raise RuntimeError("❌ Failed to initialize GridFS bucket.")
    app.state.grid_fs_bucket = grid_fs_bucket
    yield
    print("🛑 App is shutting down")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 📌 ROUTES ---------- #

@app.post("/students/create", tags=["Students"])
async def create_student(
    request: Request,
    full_name: str = Form(...),
    email: EmailStr = Form(...),
    program: str = Form(...),
    matriculation_number: str = Form(...),
    registration_number: str = Form(...),
    room_details: str = Form(...),
    gender: Literal["male", "female"] = Form(...),
    hall_of_residence: str = Form(...),
    level: Literal["100", "200", "300", "400", "500"] = Form(...),
    profile_image: UploadFile = File(...)
):
    try:
        grid_fs_bucket = request.app.state.grid_fs_bucket

        existing = await Student.find_one(Student.matriculation_number == matriculation_number)
        if existing:
            raise HTTPException(status_code=400, detail="Student already exists")

        image_bytes = await profile_image.read()
        gridfs_file_id = await grid_fs_bucket.upload_from_stream(profile_image.filename, image_bytes)
        print(f"Image saved with ID: {gridfs_file_id}")

        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        embedding = face_embeddings.get_embedding_from_image(img)
        if embedding is None:
            raise HTTPException(status_code=400, detail="Failed to extract face embedding from image")

        registrar = FaceRegistrar()
        success = registrar.register_face(
            person_id=matriculation_number,
            embedding=embedding,
            image_path=profile_image.filename
        )
        registrar.close()

        if not success:
            raise HTTPException(status_code=500, detail="Failed to save face embedding")

        student = Student(
            full_name=full_name,
            email=email,
            program=program,
            matriculation_number=matriculation_number,
            registration_number=registration_number,
            room_number=room_number,
            gender=gender,
            hall_of_residence=hall_of_residence,
            level=level,
            profile_image=gridfs_file_id
        )

        await student.create()

        return {"message": "Student created successfully", "student_id": str(student.id)}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating student: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/students/verify", tags=["Students"])
async def verify_student_face(
    request: Request,
    profile_image: UploadFile = File(...),
    threshold: float = 0.7
):
    try:
        grid_fs_bucket = request.app.state.grid_fs_bucket

        image_bytes = await profile_image.read()
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        embedding = face_embeddings.get_embedding_from_image(img)
        if embedding is None:
            raise HTTPException(status_code=400, detail="Failed to extract face embedding")

        verifier = FaceVerifier()
        matched_id = verifier.verify_face(embedding, threshold=threshold)
        verifier.close()

        if not matched_id:
            return {"message": "No matching student found"}

        student = await Student.find_one(Student.matriculation_number == matched_id)
        if not student:
            raise HTTPException(status_code=404, detail="Matched student not found in database")

        return {
            "message": "Student verified successfully",
            "student": {
                "full_name": student.full_name,
                "program": student.program,
                "hall_of_residence": student.hall_of_residence,
                "matriculation_number": student.matriculation_number,
                "level": student.level,
                "room_Details": student.room_Details
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during verification: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
