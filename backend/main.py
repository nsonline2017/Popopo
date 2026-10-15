import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import Base, engine
from routers import auth, quizzes
from services.dicom import MEDIA_ROOT

Base.metadata.create_all(bind=engine)

# seed admin
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from auth import hash_password
db = SessionLocal()
try:
    if not db.query(User).filter(User.email == "admin@example.com").first():
        db.add(User(email="admin@example.com", hashed_password=hash_password("admin123"), name="Admin", role="admin"))
        db.commit()
finally:
    db.close()

app = FastAPI(title="Popopo Radiology Quiz")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(quizzes.router)

os.makedirs(MEDIA_ROOT, exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_ROOT), name="media")

# Serve frontend build if present
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.isdir(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
