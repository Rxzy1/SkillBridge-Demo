from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db, Base, engine
from models import User, Batch
from schemas import SignupRequest,LoginRequest,BatchRequest
from auth import create_token, hash_password, verify_password,decode_token

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SkillBridge API")

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = decode_token(token)
        return {"user_id": payload["user_id"], "role": payload["role"]}
    except:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@app.get("/")
def root():
    return {"status": "SkillBridge API is running"}

@app.post("/auth/signup")
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists,Please Log in")
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

@app.post("/auth/login")
async def login(request:LoginRequest,db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing is None:
        raise HTTPException(status_code=401, detail="Email doesn't exist")
    if not verify_password(request.password,existing.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid Password")
    token = create_token({"user_id": existing.id, "role": existing.role})
    return {"access_token": token, "token_type": "bearer"}
@app.post("/batches")
async def create_batch(request: BatchRequest,
                       db: Session = Depends(get_db),
                       current_user:dict  = Depends(get_current_user)):
    if current_user["role"] not in ["trainer","institution"]:
        raise HTTPException(status_code=403, detail="Access Denied")
    new_batch = Batch(
        name = request.name,
        institution_id = current_user["user_id"]
    )
    db.add(new_batch)
    db.commit()
    db.refresh(new_batch)
    return {"user_id":new_batch.id, "name":new_batch.name, "institution_id":new_batch.institution_id}




