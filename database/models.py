"""SQLAlchemy модели для системы управления школьной успеваемостью."""

from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, Boolean,
    ForeignKey, UniqueConstraint, CheckConstraint, Identity,
    func
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Account(Base):
    __tablename__ = "accounts"

    user_id = Column(Integer, Identity(start=1), primary_key=True)
    login = Column(Text, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    u_role = Column(Text, nullable=False)


class School(Base):
    __tablename__ = "schools"

    school_id = Column(Integer, Identity(start=1), primary_key=True)
    title = Column(Text, nullable=False)
    established_in = Column(Integer, nullable=True)
    address = Column(Text, nullable=False)

    classes = relationship("Class", back_populates="school")


class Teacher(Base):
    __tablename__ = "teachers"

    teacher_id = Column(Integer, ForeignKey("accounts.user_id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    full_name = Column(Text, nullable=False)
    address = Column(Text, nullable=False)
    birth_date = Column(Date, nullable=False)
    gender = Column(String(1), nullable=False)
    head_teacher = Column(Boolean, default=False, nullable=False)
    emp_rec_book_num = Column(Text, nullable=False, unique=True)

    account = relationship("Account", backref="teacher")
    classes = relationship("Class", back_populates="class_teacher")
    marks = relationship("MarkLog", back_populates="teacher")
    staff_schedule = relationship("StaffSchedule", back_populates="teacher")
    staff_records = relationship("Staff", back_populates="teacher")


class Class(Base):
    __tablename__ = "classes"

    class_id = Column(Integer, Identity(start=1), primary_key=True)
    school_id = Column(Integer, ForeignKey("schools.school_id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    class_teacher_id = Column(Integer, ForeignKey("teachers.teacher_id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    letter = Column(String(1), nullable=False)
    form_year = Column(Integer, nullable=False)
    cabinet = Column(Text, nullable=True)
    pupil_count = Column(Integer, default=0, nullable=False)
    c_number = Column(Integer, nullable=False)

    school = relationship("School", back_populates="classes")
    class_teacher = relationship("Teacher", back_populates="classes")
    pupils_classes = relationship("PupilClass", back_populates="class_ref")


class Pupil(Base):
    __tablename__ = "pupils"

    pupil_id = Column(Integer, ForeignKey("accounts.user_id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    full_name = Column(Text, nullable=False)
    address = Column(Text, nullable=False)
    birth_date = Column(Date, nullable=False)
    gender = Column(String(1), nullable=False)

    account = relationship("Account", backref="pupil")
    pupils_classes = relationship("PupilClass", back_populates="pupil")
    marks = relationship("MarkLog", back_populates="pupil")
    performance_reports = relationship("PerformanceReport", back_populates="pupil")


class Parent(Base):
    __tablename__ = "parents"

    parent_id = Column(Integer, ForeignKey("accounts.user_id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    full_name = Column(Text, nullable=False)
    address = Column(Text, nullable=False)
    birth_date = Column(Date, nullable=True)
    gender = Column(String(1), nullable=False)

    account = relationship("Account", backref="parent")
    children = relationship("ParentChild", back_populates="parent")


class ParentChild(Base):
    __tablename__ = "parents_children"

    child_id = Column(Integer, ForeignKey("pupils.pupil_id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    parent_id = Column(Integer, ForeignKey("parents.parent_id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    relation_type = Column(Text, nullable=False)

    parent = relationship("Parent", back_populates="children")
    child = relationship("Pupil")


class Subject(Base):
    __tablename__ = "subjects"

    subject_id = Column(Integer, Identity(start=1), primary_key=True)
    title = Column(Text, nullable=False, unique=True)

    marks = relationship("MarkLog", back_populates="subject")
    staff_schedule = relationship("StaffSchedule", back_populates="subject")
    performance_reports = relationship("PerformanceReport", back_populates="subject")


class MarkLog(Base):
    __tablename__ = "mark_log"

    mark_id = Column(Integer, Identity(start=1), primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects.subject_id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.teacher_id"), nullable=False)
    pupil_id = Column(Integer, ForeignKey("pupils.pupil_id"), nullable=False)
    mark_value = Column(Integer, nullable=False)
    put_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    assessment_form = Column(Text, nullable=False)

    subject = relationship("Subject", back_populates="marks")
    teacher = relationship("Teacher", back_populates="marks")
    pupil = relationship("Pupil", back_populates="marks")


class PupilClass(Base):
    __tablename__ = "pupils_classes"

    pupil_id = Column(Integer, ForeignKey("pupils.pupil_id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    class_id = Column(Integer, ForeignKey("classes.class_id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    entered_at = Column(Date, nullable=False)
    left_at = Column(Date, nullable=True)

    pupil = relationship("Pupil", back_populates="pupils_classes")
    class_ref = relationship("Class", back_populates="pupils_classes")


class PerformanceReport(Base):
    __tablename__ = "performance_report"

    pupil_id = Column(Integer, ForeignKey("pupils.pupil_id"), primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects.subject_id"), primary_key=True)
    mark_total = Column(Integer, nullable=False)
    weights_sum = Column(Integer, nullable=False)
    final_mark = Column(Integer, nullable=False)

    pupil = relationship("Pupil", back_populates="performance_reports")
    subject = relationship("Subject", back_populates="performance_reports")


class PhoneNumber(Base):
    __tablename__ = "phone_numbers"

    user_id = Column(Integer, ForeignKey("accounts.user_id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    phone_number = Column(Text, nullable=False, unique=True)


class Staff(Base):
    __tablename__ = "staff"

    worker_id = Column(Integer, ForeignKey("teachers.teacher_id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    school_id = Column(Integer, ForeignKey("schools.school_id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    hired_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fired_at = Column(DateTime(timezone=True), nullable=True)

    teacher = relationship("Teacher", back_populates="staff_records")
    school = relationship("School")


class StaffSchedule(Base):
    __tablename__ = "staff_schedule"

    teacher_id = Column(Integer, ForeignKey("teachers.teacher_id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects.subject_id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)

    teacher = relationship("Teacher", back_populates="staff_schedule")
    subject = relationship("Subject", back_populates="staff_schedule")


class Responsibility(Base):
    __tablename__ = "responsibilities"

    head_teacher_id = Column(Integer, ForeignKey("teachers.teacher_id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    responsibility = Column(Text, nullable=False)
