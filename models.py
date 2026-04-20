from sqlalchemy import Integer, DateTime,Date,Time, Column, ForeignKey,String,Boolean
from database import Base
from sqlalchemy.sql import func
class User(Base):
    '''
    Creates tables for users to add there details
    '''
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String,nullable=False)
    email = Column(String,unique=True,nullable=False,index=True)
    hashed_password = Column(String,nullable=False)
    role = Column(String,nullable=False)
    institution_id = Column(Integer,ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime,nullable=False,server_default=func.now())

class Batch(Base):
    '''
    Creates tables for batches to add there details
    '''
    __tablename__ = 'batches'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    institution_id = Column(Integer,ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime,nullable=False,server_default=func.now())

class BatchTrainer(Base):
    '''
    Creates tables to assign trainers to batches
    '''
    __tablename__ = 'batch_trainers'
    batch_id = Column(Integer,ForeignKey("batches.id"), primary_key=True)
    trainer_id = Column(Integer,ForeignKey("users.id"),primary_key=True)

class BatchStudent(Base):
    '''
    Students to which batches
    '''
    __tablename__ = 'batch_students'
    batch_id = Column(Integer,ForeignKey("batches.id"), primary_key=True)
    student_id = Column(Integer,ForeignKey("users.id"), primary_key=True)

class BatchInvite(Base):
    '''
    Invite tokens trainers create for students to join a batch.
    '''
    __tablename__ = 'batch_invites'
    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer,ForeignKey("batches.id"), nullable=False)
    token = Column(String,unique=True,nullable=False,index=True)
    created_by = Column(Integer,ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime,nullable=False)
    used = Column(Boolean,default=False,nullable=False)

class Session(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer,ForeignKey("batches.id"), nullable=False)
    trainer_id = Column(Integer,ForeignKey("users.id"), nullable=False)
    title = Column(String,nullable=False)
    date = Column(Date,nullable=False)
    start_time = Column(Time,nullable=False)
    end_time = Column(Time,nullable=False)
    created_at = Column(DateTime,nullable=False,server_default=func.now())

class Attendance(Base):
    __tablename__ = 'attendance'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer,ForeignKey("sessions.id"), nullable=False)
    student_id = Column(Integer,ForeignKey("users.id"), nullable=False)
    status = Column(String,nullable=False)
    marked_at = Column(DateTime,server_default=func.now())
