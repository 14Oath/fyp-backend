from typing import Union, Literal
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import EmailStr
from beanie import PydanticObjectId as ObjectId
from models.student_model import Student
from services.student_service import get_all_students_service
from database import init_db
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic here
    print("🚀 App is starting up")

    grid_fs_bucket = await init_db()
    if not grid_fs_bucket:
        raise RuntimeError("❌ Failed to initialize GridFS bucket.")
    app.state.grid_fs_bucket = grid_fs_bucket

    yield

    # Shutdown logic here
    print("🛑 App is shutting down")


app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/students/create")
async def create_student(
    request: Request,
    full_name: str = Form(...),
    email: EmailStr = Form(...),
    program: str = Form(...),
    matriculation_number: str = Form(...),
    registration_number: str = Form(...),
    room_number: str = Form(...),
    gender: Literal["male", "female"] = Form(...),
    hall_of_residence: str = Form(...),
    level: Literal["100", "200", "300", "400", "500"] = Form(...),
    profile_image: UploadFile = File(...)
):
    try:
        grid_fs_bucket = request.app.state.grid_fs_bucket

        # Check if student exists already
        existing = await Student.find_one(Student.matriculation_number == matriculation_number)
        if existing:
            raise HTTPException(status_code=400, detail="Student already exists")

        # Read image bytes
        image_bytes = await profile_image.read()

        # Save image to GridFS
        gridfs_file_id = await grid_fs_bucket.upload_from_stream(profile_image.filename, image_bytes)

        print(f"Image saved with ID: {gridfs_file_id}")

        # Create new Student with GridFS file id
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


@app.get("/students")
async def get_all_students():
    try:
        response = await get_all_students_service()
        return {"status": "success", "data": response}
    except Exception as e:
        print(f"Error getting students: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/students/{matric_number}")
async def get_student_info(matric_number: str):
    """Get student details without profile image (faster)"""
    try:
        student = await Student.find_one(Student.matriculation_number == matric_number)
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        return {
            "status": "success",
            "data": {
                "id": str(student.id),
                "full_name": student.full_name,
                "email": student.email,
                "program": student.program,
                "matriculation_number": student.matriculation_number,
                "registration_number": student.registration_number,
                "room_number": student.room_number,
                "gender": student.gender,
                "hall_of_residence": student.hall_of_residence,
                "level": student.level,
                "has_profile_image": bool(student.profile_image),
                "profile_image_url": f"/students/{matric_number}/image" if student.profile_image else None
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting student info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/students/{matric_number}/image")
async def get_student_image(matric_number: str, request: Request):
    """Get student profile image as file"""
    try:
        grid_fs_bucket = request.app.state.grid_fs_bucket

        student = await Student.find_one(Student.matriculation_number == matric_number)
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        if not student.profile_image:
            raise HTTPException(status_code=404, detail="No profile image found for this student")
        
        image_id = ObjectId(student.profile_image) if isinstance(student.profile_image, str) else student.profile_image
        
        # Download file from GridFS
        grid_out = await grid_fs_bucket.open_download_stream(image_id)
        image_data = await grid_out.read()
        
        # Determine content type
        content_type = "image/jpeg"  # default
        file_info = await grid_fs_bucket.find({"_id": image_id}).to_list(1)
        if file_info and "metadata" in file_info[0]:
            content_type = file_info[0]["metadata"].get("content_type", content_type)
        elif file_info:
            filename = file_info[0].get("filename", "")
            if filename.lower().endswith('.png'):
                content_type = "image/png"
            elif filename.lower().endswith('.gif'):
                content_type = "image/gif"
        
        return Response(
            content=image_data, 
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename={student.matriculation_number}_profile.jpg"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting student image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
