from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError
from datetime import datetime, timedelta
import uuid
import logging
import os
from database import get_db, Base, engine
from models import User, Batch, Session as SessionModel, BatchStudent, Attendance, BatchInvite
from schemas import SignupRequest, LoginRequest, BatchRequest, Create_Sessions, Mark_Attendance, JoinClassRequest
from auth import create_token, hash_password, verify_password, decode_token

# set up basic logging so we can see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SkillBridge API")

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # reads the bearer token, decodes it, returns user_id and role
    try:
        token = credentials.credentials
        payload = decode_token(token)
        return {"user_id": payload["user_id"], "role": payload["role"]}
    except JWTError as e:
        logger.warning(f"JWT decode failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except KeyError as e:
        logger.warning(f"Token missing required field: {e}")
        raise HTTPException(status_code=401, detail="Invalid token payload")


@app.get("/")
def root():
    return {"status": "SkillBridge API is running"}


@app.post("/auth/signup")
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    # reject duplicate emails
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists, please log in")
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
    logger.info(f"New user signed up: {new_user.email} ({new_user.role})")
    return {"access_token": token, "token_type": "bearer"}


@app.post("/auth/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    # same error message for both failures so attackers can't enumerate emails
    existing = db.query(User).filter(User.email == request.email).first()
    if existing is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(request.password, existing.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({"user_id": existing.id, "role": existing.role})
    logger.info(f"User logged in: {existing.email}")
    return {"access_token": token, "token_type": "bearer"}


@app.post("/batches")
async def create_batch(
        request: BatchRequest,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    if current_user["role"] not in ["trainer", "institution"]:
        raise HTTPException(status_code=403, detail="Access Denied")
    new_batch = Batch(
        name=request.name,
        institution_id=current_user["user_id"]
    )
    db.add(new_batch)
    db.commit()
    db.refresh(new_batch)
    return {"id": new_batch.id, "name": new_batch.name, "institution_id": new_batch.institution_id}


@app.post("/sessions")
async def create_session(
        request: Create_Sessions,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "trainer":
        raise HTTPException(status_code=403, detail="Access Denied")
    # prevent the same batch from having two sessions at the same time
    existing_session = db.query(SessionModel).filter(
        SessionModel.batch_id == request.batch_id,
        SessionModel.date == request.date,
        SessionModel.start_time == request.start_time
    ).first()
    if existing_session:
        raise HTTPException(status_code=400, detail="Session already exists")
    new_session = SessionModel(
        batch_id=request.batch_id,
        title=request.title,
        date=request.date,
        start_time=request.start_time,
        end_time=request.end_time,
        trainer_id=current_user["user_id"]
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return {
        "id": new_session.id,
        "title": new_session.title,
        "batch_id": new_session.batch_id,
        "trainer_id": new_session.trainer_id,
        "date": new_session.date,
        "start_time": new_session.start_time,
        "end_time": new_session.end_time
    }


@app.post("/batches/{batch_id}/invite")
async def create_invite(
        batch_id: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "trainer":
        raise HTTPException(status_code=403, detail="Access Denied")
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    # generate a random unique token, valid for 7 days
    token = str(uuid.uuid4())
    new_invite = BatchInvite(
        batch_id=batch_id,
        token=token,
        created_by=current_user["user_id"],
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(new_invite)
    db.commit()
    return {"token": token, "expires_at": new_invite.expires_at}


@app.post("/batches/join")
async def join_batch(
        request: JoinClassRequest,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can join batches")
    invite = db.query(BatchInvite).filter(BatchInvite.token == request.token).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid token")
    if invite.used:
        raise HTTPException(status_code=400, detail="Token already used")
    if invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token has expired")
    # block duplicate enrollment in the same batch
    already_enrolled = db.query(BatchStudent).filter(
        BatchStudent.batch_id == invite.batch_id,
        BatchStudent.student_id == current_user["user_id"]
    ).first()
    if already_enrolled:
        raise HTTPException(status_code=400, detail="Already enrolled in this batch")
    new_enrollment = BatchStudent(
        student_id=current_user["user_id"],
        batch_id=invite.batch_id
    )
    invite.used = True
    db.add(new_enrollment)
    db.commit()
    return {"message": "Successfully joined batch", "batch_id": invite.batch_id}


@app.post("/attendance/mark")
async def mark_attendance(
        request: Mark_Attendance,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Access Denied")
    session = db.query(SessionModel).filter(SessionModel.id == request.session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session does not exist")
    # student must be enrolled in the batch this session belongs to
    enrolled = db.query(BatchStudent).filter(
        BatchStudent.batch_id == session.batch_id,
        BatchStudent.student_id == current_user["user_id"]
    ).first()
    if not enrolled:
        raise HTTPException(status_code=403, detail="You are not enrolled in this batch")
    already_marked = db.query(Attendance).filter(
        Attendance.session_id == request.session_id,
        Attendance.student_id == current_user["user_id"]
    ).first()
    if already_marked:
        raise HTTPException(status_code=400, detail="Attendance already marked for this session")
    new_attendance = Attendance(
        session_id=request.session_id,
        student_id=current_user["user_id"],
        status=request.status
    )
    db.add(new_attendance)
    db.commit()
    db.refresh(new_attendance)
    return {
        "id": new_attendance.id,
        "session_id": new_attendance.session_id,
        "student_id": new_attendance.student_id,
        "status": new_attendance.status,
        "marked_at": new_attendance.marked_at
    }

# read environment variable for monitoring
MONITORING_API_KEY = os.getenv("MONITORING_API_KEY")


@app.get("/sessions/{session_id}/attendance")
async def get_session_attendance(
        session_id: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "trainer":
        raise HTTPException(status_code=403, detail="Access Denied")
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    records = db.query(Attendance).filter(Attendance.session_id == session_id).all()
    return [
        {
            "id": r.id,
            "student_id": r.student_id,
            "status": r.status,
            "marked_at": r.marked_at
        }
        for r in records
    ]


@app.post("/auth/monitoring-token")
async def get_monitoring_token(
        key: dict,
        current_user: dict = Depends(get_current_user)
):
    # step 1 — caller must be a monitoring officer
    if current_user["role"] != "monitoring_officer":
        raise HTTPException(status_code=403, detail="Only monitoring officers can access this")

    # step 2 — verify the secret API key
    if key.get("key") != MONITORING_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # step 3 — issue a scoped token valid for 1 hour
    scoped_token = create_token({
        "user_id": current_user["user_id"],
        "role": "monitoring_officer",
        "scope": "monitoring"
    },expires_in_hours=1)
    return {"monitoring_token": scoped_token, "expires_in": "1 hour"}


@app.get("/monitoring/attendance")
async def monitoring_attendance(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
):
    # validate the scoped monitoring token specifically
    try:
        token = credentials.credentials
        payload = decode_token(token)
        # this endpoint needs the scoped token, not the standard login token
        if payload.get("scope") != "monitoring":
            raise HTTPException(status_code=401, detail="Monitoring token required")
        if payload.get("role") != "monitoring_officer":
            raise HTTPException(status_code=403, detail="Access Denied")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired monitoring token")
    except KeyError:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    records = db.query(Attendance).all()
    return [
        {
            "id": r.id,
            "session_id": r.session_id,
            "student_id": r.student_id,
            "status": r.status,
            "marked_at": r.marked_at
        }
        for r in records
    ]
