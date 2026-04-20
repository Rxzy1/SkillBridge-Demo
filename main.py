from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Base, engine
from models import User
from schemas import SignupRequest
from auth import create_token, hash_password
import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SkillBridge API")

@app.get("/")
def root():
    return {"status": "SkillBridge API is running"}

@app.post("/auth/signup")
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    new_user = User(
        name=request.name,
        email=request.email,
        hashed_password=hash_password(request.password),
        role=request.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    token = create_token({"user_id": new_user.id, "role": new_user.role})
    return {"access_token": token, "token_type": "bearer"}