from database import SessionLocal, Base, engine
from models import User, Batch, BatchStudent, BatchTrainer, Session as SessionModel, Attendance, BatchInvite
from auth import hash_password
from datetime import date, time, datetime, timedelta

Base.metadata.create_all(bind=engine)

db = SessionLocal()

# clear old data so we can run this multiple times cleanly
db.query(Attendance).delete()
db.query(SessionModel).delete()
db.query(BatchStudent).delete()
db.query(BatchTrainer).delete()
db.query(BatchInvite).delete()
db.query(Batch).delete()
db.query(User).delete()
db.commit()

# 2 institutions
inst1 = User(name="ABC College", email="abc@college.com", hashed_password=hash_password("Test@1234"), role="institution")
inst2 = User(name="XYZ Institute", email="xyz@institute.com", hashed_password=hash_password("Test@1234"), role="institution")
db.add_all([inst1, inst2])
db.commit()
db.refresh(inst1)
db.refresh(inst2)

# programme manager
manager = User(name="Programme Manager", email="manager@skillbridge.com", hashed_password=hash_password("Test@1234"), role="programme_manager")
db.add(manager)
db.commit()

# monitoring officer
monitor = User(name="Monitor Officer", email="monitor@skillbridge.com", hashed_password=hash_password("Test@1234"), role="monitoring_officer")
db.add(monitor)
db.commit()

# 4 trainers
trainer1 = User(name="Trainer One", email="trainer1@skillbridge.com", hashed_password=hash_password("Test@1234"), role="trainer", institution_id=inst1.id)
trainer2 = User(name="Trainer Two", email="trainer2@skillbridge.com", hashed_password=hash_password("Test@1234"), role="trainer", institution_id=inst1.id)
trainer3 = User(name="Trainer Three", email="trainer3@skillbridge.com", hashed_password=hash_password("Test@1234"), role="trainer", institution_id=inst2.id)
trainer4 = User(name="Trainer Four", email="trainer4@skillbridge.com", hashed_password=hash_password("Test@1234"), role="trainer", institution_id=inst2.id)
db.add_all([trainer1, trainer2, trainer3, trainer4])
db.commit()
db.refresh(trainer1)
db.refresh(trainer2)
db.refresh(trainer3)
db.refresh(trainer4)

# 15 students
students = []
for i in range(15):
    s = User(
        name=f"Student {i+1}",
        email=f"student{i+1}@skillbridge.com",
        hashed_password=hash_password("Test@1234"),
        role="student",
        institution_id=inst1.id if i < 8 else inst2.id
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    students.append(s)

# 3 batches
batch1 = Batch(name="Python Fundamentals", institution_id=inst1.id)
batch2 = Batch(name="Web Development", institution_id=inst1.id)
batch3 = Batch(name="Data Science", institution_id=inst2.id)
db.add_all([batch1, batch2, batch3])
db.commit()
db.refresh(batch1)
db.refresh(batch2)
db.refresh(batch3)

# assign trainers to batches
db.add(BatchTrainer(batch_id=batch1.id, trainer_id=trainer1.id))
db.add(BatchTrainer(batch_id=batch2.id, trainer_id=trainer2.id))
db.add(BatchTrainer(batch_id=batch3.id, trainer_id=trainer3.id))
db.commit()

# enroll students into batches
# batch1 and batch2 get first 8 students
# batch3 gets last 7 students
for s in students[:8]:
    db.add(BatchStudent(batch_id=batch1.id, student_id=s.id))
    db.add(BatchStudent(batch_id=batch2.id, student_id=s.id))
for s in students[8:]:
    db.add(BatchStudent(batch_id=batch3.id, student_id=s.id))
db.commit()

# 8 sessions
session1 = SessionModel(batch_id=batch1.id, trainer_id=trainer1.id, title="Intro to Python", date=date(2026, 4, 1), start_time=time(10, 0), end_time=time(12, 0))
session2 = SessionModel(batch_id=batch1.id, trainer_id=trainer1.id, title="Variables and Types", date=date(2026, 4, 3), start_time=time(10, 0), end_time=time(12, 0))
session3 = SessionModel(batch_id=batch1.id, trainer_id=trainer1.id, title="Control Flow", date=date(2026, 4, 5), start_time=time(10, 0), end_time=time(12, 0))
session4 = SessionModel(batch_id=batch2.id, trainer_id=trainer2.id, title="HTML Basics", date=date(2026, 4, 2), start_time=time(14, 0), end_time=time(16, 0))
session5 = SessionModel(batch_id=batch2.id, trainer_id=trainer2.id, title="CSS Styling", date=date(2026, 4, 4), start_time=time(14, 0), end_time=time(16, 0))
session6 = SessionModel(batch_id=batch3.id, trainer_id=trainer3.id, title="Intro to Data Science", date=date(2026, 4, 1), start_time=time(11, 0), end_time=time(13, 0))
session7 = SessionModel(batch_id=batch3.id, trainer_id=trainer3.id, title="Pandas Basics", date=date(2026, 4, 3), start_time=time(11, 0), end_time=time(13, 0))
session8 = SessionModel(batch_id=batch3.id, trainer_id=trainer3.id, title="Data Visualisation", date=date(2026, 4, 5), start_time=time(11, 0), end_time=time(13, 0))
db.add_all([session1, session2, session3, session4, session5, session6, session7, session8])
db.commit()
db.refresh(session1)
db.refresh(session2)
db.refresh(session3)
db.refresh(session4)
db.refresh(session5)
db.refresh(session6)
db.refresh(session7)
db.refresh(session8)

# attendance for batch1 sessions (students 1-8)
for s in students[:8]:
    db.add(Attendance(session_id=session1.id, student_id=s.id, status="present"))
    db.add(Attendance(session_id=session2.id, student_id=s.id, status="present"))
    db.add(Attendance(session_id=session3.id, student_id=s.id, status="late"))
db.commit()

# attendance for batch2 sessions (students 1-8)
for s in students[:8]:
    db.add(Attendance(session_id=session4.id, student_id=s.id, status="present"))
    db.add(Attendance(session_id=session5.id, student_id=s.id, status="absent"))
db.commit()

# attendance for batch3 sessions (students 9-15)
for s in students[8:]:
    db.add(Attendance(session_id=session6.id, student_id=s.id, status="present"))
    db.add(Attendance(session_id=session7.id, student_id=s.id, status="present"))
    db.add(Attendance(session_id=session8.id, student_id=s.id, status="late"))
db.commit()

db.close()

print("Done.")
print("Institutions: abc@college.com, xyz@institute.com")
print("Trainers: trainer1@skillbridge.com to trainer4@skillbridge.com")
print("Students: student1@skillbridge.com to student15@skillbridge.com")
print("Manager: manager@skillbridge.com")
print("Monitor: monitor@skillbridge.com")
print("All passwords: Test@1234")