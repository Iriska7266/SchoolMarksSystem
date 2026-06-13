"""Бизнес-логика и CRUD-операции."""

from sqlalchemy import text, func
from sqlalchemy.orm import Session
from database.models import (
    Account, School, Teacher, Class, Pupil, Parent,
    Subject, MarkLog, PupilClass, PerformanceReport,
    StaffSchedule, Staff, ParentChild, PhoneNumber, Responsibility
)
from typing import Any


# ─── Аутентификация ───────────────────────────────────────────────────────────

def authenticate_user(db: Session, login: str, password_hash: str) -> Account | None:
    return db.query(Account).filter(
        Account.login == login,
        Account.password_hash == password_hash
    ).first()


def get_account_by_id(db: Session, user_id: int) -> Account | None:
    return db.query(Account).filter(Account.user_id == user_id).first()


# ─── Школы ────────────────────────────────────────────────────────────────────

def get_schools(db: Session) -> list[School]:
    return db.query(School).order_by(School.title).all()


def get_school(db: Session, school_id: int) -> School | None:
    return db.query(School).filter(School.school_id == school_id).first()


def create_school(db: Session, title: str, address: str, established_in: int | None = None) -> School:
    school = School(title=title, address=address, established_in=established_in)
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def update_school(db: Session, school_id: int, **kwargs) -> School | None:
    school = get_school(db, school_id)
    if school:
        for k, v in kwargs.items():
            if hasattr(school, k) and v is not None:
                setattr(school, k, v)
        db.commit()
        db.refresh(school)
    return school


def delete_school(db: Session, school_id: int) -> bool:
    school = get_school(db, school_id)
    if school:
        db.delete(school)
        db.commit()
        return True
    return False


# ─── Учителя ──────────────────────────────────────────────────────────────────

def get_teachers(db: Session) -> list[dict[str, Any]]:
    results = db.query(Teacher, Account).join(Account, Teacher.teacher_id == Account.user_id).order_by(Teacher.full_name).all()
    return [_teacher_to_dict(t, a) for t, a in results]


def get_teacher(db: Session, teacher_id: int) -> dict[str, Any] | None:
    result = db.query(Teacher, Account).join(Account, Teacher.teacher_id == Account.user_id).filter(Teacher.teacher_id == teacher_id).first()
    if result:
        t, a = result
        return _teacher_to_dict(t, a)
    return None


def _teacher_to_dict(t: Teacher, a: Account) -> dict[str, Any]:
    return {
        "teacher_id": t.teacher_id,
        "full_name": t.full_name,
        "address": t.address,
        "birth_date": t.birth_date,
        "gender": t.gender,
        "head_teacher": t.head_teacher,
        "emp_rec_book_num": t.emp_rec_book_num,
        "login": a.login,
        "role": a.u_role,
    }


def create_teacher(db: Session, login: str, password_hash: str, full_name: str,
                   address: str, gender: str, birth_date: str,
                   emp_rec_book_num: str, head_teacher: bool = False) -> Teacher:
    role = "headteacher" if head_teacher else "teacher"
    account = Account(login=login, password_hash=password_hash, u_role=role)
    db.add(account)
    db.flush()

    teacher = Teacher(
        teacher_id=account.user_id,
        full_name=full_name,
        address=address,
        gender=gender.lower(),
        birth_date=birth_date,
        emp_rec_book_num=emp_rec_book_num,
        head_teacher=head_teacher
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


def update_teacher(db: Session, teacher_id: int, **kwargs) -> bool:
    teacher = db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()
    if not teacher:
        return False
    updatable = {"full_name", "address", "gender", "birth_date", "emp_rec_book_num", "head_teacher"}
    for k, v in kwargs.items():
        if k in updatable and v is not None:
            setattr(teacher, k, v.lower() if k == "gender" else v)
    db.commit()
    return True


def delete_teacher(db: Session, teacher_id: int) -> bool:
    # Проверка: не является ли классным руководителем
    active = db.query(Class).join(Staff, Class.school_id == Staff.school_id).filter(
        Class.class_teacher_id == teacher_id,
        Staff.fired_at.is_(None)
    ).count()
    if active > 0:
        return False
    db.query(Teacher).filter(Teacher.teacher_id == teacher_id).delete()
    db.commit()
    return True


# ─── Классы ───────────────────────────────────────────────────────────────────

def get_classes(db: Session) -> list[dict[str, Any]]:
    results = db.query(Class, School, Teacher).join(School).join(Teacher, Class.class_teacher_id == Teacher.teacher_id).order_by(Class.c_number, Class.letter).all()
    return [_class_to_dict(c, s, t) for c, s, t in results]


def get_class(db: Session, class_id: int) -> dict[str, Any] | None:
    result = db.query(Class, School, Teacher).join(School).join(Teacher, Class.class_teacher_id == Teacher.teacher_id).filter(Class.class_id == class_id).first()
    if result:
        c, s, t = result
        return _class_to_dict(c, s, t)
    return None


def _class_to_dict(c: Class, s: School, t: Teacher) -> dict[str, Any]:
    return {
        "class_id": c.class_id,
        "school_id": c.school_id,
        "school_title": s.title,
        "class_teacher_id": c.class_teacher_id,
        "class_teacher_name": t.full_name,
        "letter": c.letter,
        "form_year": c.form_year,
        "cabinet": c.cabinet,
        "pupil_count": c.pupil_count,
        "c_number": c.c_number,
        "title": f"{c.c_number}{c.letter}"
    }


def create_class(db: Session, school_id: int, class_teacher_id: int,
                 letter: str, form_year: int, c_number: int,
                 cabinet: str | None = None) -> Class:
    cls = Class(
        school_id=school_id, class_teacher_id=class_teacher_id,
        letter=letter, form_year=form_year, c_number=c_number,
        cabinet=cabinet
    )
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return cls


def update_class(db: Session, class_id: int, **kwargs) -> bool:
    cls = db.query(Class).filter(Class.class_id == class_id).first()
    if not cls:
        return False
    updatable = {"school_id", "class_teacher_id", "letter", "form_year", "cabinet", "c_number"}
    for k, v in kwargs.items():
        if k in updatable and v is not None:
            setattr(cls, k, v)
    db.commit()
    return True


def delete_class(db: Session, class_id: int) -> bool:
    db.query(Class).filter(Class.class_id == class_id).delete()
    db.commit()
    return True


# ─── Ученики ─────────────────────────────────────────────────────────────────

def get_pupils(db: Session) -> list[dict[str, Any]]:
    results = db.query(Pupil, Account).join(Account, Pupil.pupil_id == Account.user_id).order_by(Pupil.full_name).all()
    return [_pupil_to_dict(p, a) for p, a in results]


def get_pupil(db: Session, pupil_id: int) -> dict[str, Any] | None:
    result = db.query(Pupil, Account).join(Account, Pupil.pupil_id == Account.user_id).filter(Pupil.pupil_id == pupil_id).first()
    if result:
        p, a = result
        return _pupil_to_dict(p, a)
    return None


def _pupil_to_dict(p: Pupil, a: Account) -> dict[str, Any]:
    return {
        "pupil_id": p.pupil_id,
        "full_name": p.full_name,
        "address": p.address,
        "birth_date": p.birth_date,
        "gender": p.gender,
        "login": a.login,
        "role": a.u_role,
    }


def create_pupil(db: Session, login: str, password_hash: str, full_name: str,
                 address: str, gender: str, birth_date: str) -> Pupil:
    account = Account(login=login, password_hash=password_hash, u_role="pupil")
    db.add(account)
    db.flush()
    pupil = Pupil(
        pupil_id=account.user_id,
        full_name=full_name,
        address=address,
        gender=gender.lower(),
        birth_date=birth_date,
    )
    db.add(pupil)
    db.commit()
    db.refresh(pupil)
    return pupil


def update_pupil(db: Session, pupil_id: int, **kwargs) -> bool:
    pupil = db.query(Pupil).filter(Pupil.pupil_id == pupil_id).first()
    if not pupil:
        return False
    updatable = {"full_name", "address", "gender", "birth_date"}
    for k, v in kwargs.items():
        if k in updatable and v is not None:
            setattr(pupil, k, v.lower() if k == "gender" else v)
    db.commit()
    return True


def delete_pupil(db: Session, pupil_id: int) -> bool:
    db.query(Pupil).filter(Pupil.pupil_id == pupil_id).delete()
    db.commit()
    return True


def enroll_pupil(db: Session, pupil_id: int, class_id: int, entered_at: str | None = None) -> bool:
    """Зачисляет ученика в класс."""
    from datetime import date
    # Проверка: ученик не должен быть активен в другом классе
    active = db.query(PupilClass).filter(
        PupilClass.pupil_id == pupil_id, PupilClass.left_at.is_(None)
    ).first()
    if active:
        return False

    # Проверка: в классе не больше 30 учеников
    cls = db.query(Class).filter(Class.class_id == class_id).first()
    if cls and cls.pupil_count >= 30:
        return False

    pc = PupilClass(
        pupil_id=pupil_id,
        class_id=class_id,
        entered_at=date.fromisoformat(entered_at) if entered_at else date.today(),
    )
    db.add(pc)
    if cls:
        cls.pupil_count += 1
    db.commit()
    return True


def expel_pupil(db: Session, pupil_id: int, left_at: str | None = None) -> bool:
    """Отчисляет ученика из класса."""
    from datetime import date
    pc = db.query(PupilClass).filter(
        PupilClass.pupil_id == pupil_id, PupilClass.left_at.is_(None)
    ).first()
    if not pc:
        return False

    pc.left_at = date.fromisoformat(left_at) if left_at else date.today()

    cls = db.query(Class).filter(Class.class_id == pc.class_id).first()
    if cls and cls.pupil_count > 0:
        cls.pupil_count -= 1

    db.commit()
    return True


# ─── Родители ─────────────────────────────────────────────────────────────────

def get_parents(db: Session) -> list[dict[str, Any]]:
    results = db.query(Parent, Account).join(Account, Parent.parent_id == Account.user_id).order_by(Parent.full_name).all()
    return [_parent_to_dict(p, a) for p, a in results]


def _parent_to_dict(p: Parent, a: Account) -> dict[str, Any]:
    return {
        "parent_id": p.parent_id,
        "full_name": p.full_name,
        "address": p.address,
        "birth_date": p.birth_date,
        "gender": p.gender,
        "login": a.login,
    }


def create_parent(db: Session, login: str, password_hash: str, full_name: str,
                  address: str, gender: str, birth_date: str | None = None) -> Parent:
    account = Account(login=login, password_hash=password_hash, u_role="parent")
    db.add(account)
    db.flush()
    parent = Parent(
        parent_id=account.user_id,
        full_name=full_name,
        address=address,
        gender=gender.lower(),
        birth_date=birth_date,
    )
    db.add(parent)
    db.commit()
    db.refresh(parent)
    return parent


def update_parent(db: Session, parent_id: int, **kwargs) -> bool:
    parent = db.query(Parent).filter(Parent.parent_id == parent_id).first()
    if not parent:
        return False
    updatable = {"full_name", "address", "gender", "birth_date"}
    for k, v in kwargs.items():
        if k in updatable and v is not None:
            setattr(parent, k, v.lower() if k == "gender" else v)
    db.commit()
    return True


def delete_parent(db: Session, parent_id: int) -> bool:
    has_children = db.query(ParentChild).filter(ParentChild.parent_id == parent_id).count() > 0
    if has_children:
        return False
    db.query(Parent).filter(Parent.parent_id == parent_id).delete()
    db.commit()
    return True


# ─── Предметы ─────────────────────────────────────────────────────────────────

def get_subjects(db: Session) -> list[Subject]:
    return db.query(Subject).order_by(Subject.title).all()


def create_subject(db: Session, title: str) -> Subject:
    subject = Subject(title=title)
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


def update_subject(db: Session, subject_id: int, title: str) -> bool:
    subject = db.query(Subject).filter(Subject.subject_id == subject_id).first()
    if not subject:
        return False
    subject.title = title
    db.commit()
    return True


def delete_subject(db: Session, subject_id: int) -> bool:
    db.query(Subject).filter(Subject.subject_id == subject_id).delete()
    db.commit()
    return True


# ─── Оценки ───────────────────────────────────────────────────────────────────

def get_marks(db: Session, pupil_id: int | None = None, subject_id: int | None = None,
              class_id: int | None = None) -> list[dict[str, Any]]:
    q = db.query(MarkLog, Subject, Teacher, Pupil).join(Subject).join(Teacher).join(Pupil)
    if pupil_id:
        q = q.filter(MarkLog.pupil_id == pupil_id)
    if subject_id:
        q = q.filter(MarkLog.subject_id == subject_id)
    if class_id:
        q = q.join(PupilClass, MarkLog.pupil_id == PupilClass.pupil_id).filter(
            PupilClass.class_id == class_id, PupilClass.left_at.is_(None)
        )
    results = q.order_by(MarkLog.put_at.desc()).all()
    return [_mark_to_dict(m, s, t, p) for m, s, t, p in results]


def _mark_to_dict(m: MarkLog, s: Subject, t: Teacher, p: Pupil) -> dict[str, Any]:
    return {
        "mark_id": m.mark_id,
        "subject_id": m.subject_id,
        "subject_title": s.title,
        "teacher_id": m.teacher_id,
        "teacher_name": t.full_name,
        "pupil_id": m.pupil_id,
        "pupil_name": p.full_name,
        "mark_value": m.mark_value,
        "put_at": m.put_at,
        "assessment_form": m.assessment_form,
    }


def create_mark(db: Session, subject_id: int, teacher_id: int, pupil_id: int,
                mark_value: int, assessment_form: str) -> MarkLog:
    mark = MarkLog(
        subject_id=subject_id, teacher_id=teacher_id,
        pupil_id=pupil_id, mark_value=mark_value,
        assessment_form=assessment_form
    )
    db.add(mark)
    db.commit()
    db.refresh(mark)
    return mark


def update_mark(db: Session, mark_id: int, **kwargs) -> bool:
    mark = db.query(MarkLog).filter(MarkLog.mark_id == mark_id).first()
    if not mark:
        return False
    updatable = {"mark_value", "assessment_form"}
    for k, v in kwargs.items():
        if k in updatable and v is not None:
            setattr(mark, k, v)
    db.commit()
    return True


def delete_mark(db: Session, mark_id: int) -> bool:
    db.query(MarkLog).filter(MarkLog.mark_id == mark_id).delete()
    db.commit()
    return True


# ─── Успеваемость ─────────────────────────────────────────────────────────────

def get_performance(db: Session, class_id: int | None = None,
                    pupil_id: int | None = None) -> list[dict[str, Any]]:
    q = db.query(PerformanceReport, Pupil, Subject).join(Pupil).join(Subject)
    if pupil_id:
        q = q.filter(PerformanceReport.pupil_id == pupil_id)
    if class_id:
        q = q.join(PupilClass, PerformanceReport.pupil_id == PupilClass.pupil_id).filter(
            PupilClass.class_id == class_id, PupilClass.left_at.is_(None)
        )
    results = q.order_by(Pupil.full_name, Subject.title).all()
    return [_perf_to_dict(r, p, s) for r, p, s in results]


def _perf_to_dict(r: PerformanceReport, p: Pupil, s: Subject) -> dict[str, Any]:
    return {
        "pupil_id": r.pupil_id,
        "pupil_name": p.full_name,
        "subject_id": r.subject_id,
        "subject_title": s.title,
        "mark_total": r.mark_total,
        "weights_sum": r.weights_sum,
        "final_mark": r.final_mark,
    }


# ─── Статистика / Дашборд ────────────────────────────────────────────────────

def get_dashboard_stats(db: Session) -> dict[str, Any]:
    total_pupils = db.query(Pupil).count()
    total_teachers = db.query(Teacher).count()
    total_classes = db.query(Class).count()
    total_subjects = db.query(Subject).count()
    total_marks = db.query(MarkLog).count()
    total_parents = db.query(Parent).count()
    total_schools = db.query(School).count()

    avg_mark = db.query(func.avg(MarkLog.mark_value)).scalar()
    avg_mark = round(avg_mark, 2) if avg_mark else 0

    class_list = get_classes(db)

    return {
        "total_pupils": total_pupils,
        "total_teachers": total_teachers,
        "total_classes": total_classes,
        "total_subjects": total_subjects,
        "total_marks": total_marks,
        "total_parents": total_parents,
        "total_schools": total_schools,
        "avg_mark": avg_mark,
        "classes": class_list,
    }


def get_pupils_by_class(db: Session, class_id: int) -> list[dict[str, Any]]:
    results = (
        db.query(Pupil, PupilClass)
        .join(PupilClass, Pupil.pupil_id == PupilClass.pupil_id)
        .filter(PupilClass.class_id == class_id, PupilClass.left_at.is_(None))
        .order_by(Pupil.full_name)
        .all()
    )
    return [{
        "pupil_id": p.pupil_id,
        "full_name": p.full_name,
        "birth_date": p.birth_date,
        "gender": p.gender,
    } for p, _ in results]


def get_teacher_subjects(db: Session, teacher_id: int) -> list[Subject]:
    results = (
        db.query(Subject)
        .join(StaffSchedule, Subject.subject_id == StaffSchedule.subject_id)
        .filter(StaffSchedule.teacher_id == teacher_id)
        .all()
    )
    return results


def get_class_pupils_count(db: Session) -> list[dict[str, Any]]:
    results = (
        db.query(Class, func.count(PupilClass.pupil_id).label("actual_count"))
        .outerjoin(PupilClass, Class.class_id == PupilClass.class_id)
        .filter(PupilClass.left_at.is_(None))
        .group_by(Class.class_id)
        .order_by(Class.c_number, Class.letter)
        .all()
    )
    return [{"class_id": c.class_id, "title": f"{c.c_number}{c.letter}", "count": cnt} for c, cnt in results]


def recalc_performance_for_pupil(db: Session, pupil_id: int) -> int:
    """Пересчитывает итоговые оценки для одного ученика по всем предметам."""
    count = 0
    subjects = db.query(Subject).all()
    for subj in subjects:
        db.execute(
            text("SELECT recalc_performance_for_pupil_subject(:p, :s)"),
            {"p": pupil_id, "s": subj.subject_id}
        )
        count += 1
    db.commit()
    return count


def recalc_performance_for_class(db: Session, class_id: int) -> int:
    """Пересчитывает итоговые оценки для всех учеников класса."""
    pupils = get_pupils_by_class(db, class_id)
    count = 0
    subjects = db.query(Subject).all()
    for pupil in pupils:
        for subj in subjects:
            db.execute(
                text("SELECT recalc_performance_for_pupil_subject(:p, :s)"),
                {"p": pupil["pupil_id"], "s": subj.subject_id}
            )
            count += 1
    db.commit()
    return count


def get_subject_teachers(db: Session, subject_id: int) -> list[dict]:
    """Возвращает учителей, ведущих данный предмет."""
    results = (
        db.query(Teacher, Account)
        .join(StaffSchedule, Teacher.teacher_id == StaffSchedule.teacher_id)
        .join(Account, Teacher.teacher_id == Account.user_id)
        .filter(StaffSchedule.subject_id == subject_id)
        .order_by(Teacher.full_name)
        .all()
    )
    return [{"teacher_id": t.teacher_id, "full_name": t.full_name, "login": a.login} for t, a in results]


def get_teacher_classes(db: Session, teacher_id: int) -> list[dict]:
    """Возвращает классы, которые вёл/ведёт учитель."""
    results = (
        db.query(Class)
        .filter(Class.class_teacher_id == teacher_id)
        .order_by(Class.c_number, Class.letter)
        .all()
    )
    return [{"class_id": c.class_id, "title": f"{c.c_number}{c.letter}"} for c in results]


def get_parent_children(db: Session, parent_id: int) -> list[dict]:
    """Возвращает детей родителя."""
    results = (
        db.query(Pupil, ParentChild)
        .join(ParentChild, Pupil.pupil_id == ParentChild.child_id)
        .filter(ParentChild.parent_id == parent_id)
        .all()
    )
    return [{"pupil_id": p.pupil_id, "full_name": p.full_name, "relation": pc.relation_type} for p, pc in results]


def get_pupil_marks_grouped(db: Session, pupil_id: int) -> list[dict]:
    """Возвращает оценки ученика, сгруппированные по предметам."""
    from collections import defaultdict
    marks = get_marks(db, pupil_id=pupil_id)
    grouped = defaultdict(list)
    for m in marks:
        grouped[m["subject_title"]].append(m)
    result = []
    for subject_name, subject_marks in grouped.items():
        values = [m["mark_value"] for m in subject_marks]
        avg = round(sum(values) / len(values), 2) if values else 0
        result.append({
            "subject": subject_name,
            "marks": subject_marks,
            "avg": avg,
            "count": len(values),
        })
    return result


def get_own_pupil_id(db: Session, user_id: int) -> int | None:
    """Возвращает pupil_id для учётной записи ученика."""
    pupil = db.query(Pupil).filter(Pupil.pupil_id == user_id).first()
    return pupil.pupil_id if pupil else None


def get_parent_children_ids(db: Session, user_id: int) -> list[int]:
    """Возвращает список pupil_id детей для учётной записи родителя."""
    results = db.query(ParentChild.child_id).filter(
        ParentChild.parent_id == user_id
    ).all()
    return [r[0] for r in results]


def get_teacher_subject_ids(db: Session, teacher_id: int) -> list[int]:
    """Возвращает список subject_id, которые ведёт учитель."""
    results = db.query(StaffSchedule.subject_id).filter(
        StaffSchedule.teacher_id == teacher_id
    ).all()
    return [r[0] for r in results]


def get_teacher_class_parents(db: Session, teacher_id: int) -> list[dict]:
    """Возвращает родителей учеников из класса, где учитель — классный руководитель."""
    pupils = (
        db.query(Pupil)
        .join(PupilClass, Pupil.pupil_id == PupilClass.pupil_id)
        .join(Class, PupilClass.class_id == Class.class_id)
        .filter(Class.class_teacher_id == teacher_id, PupilClass.left_at.is_(None))
        .all()
    )
    if not pupils:
        return []
    pupil_ids = [p.pupil_id for p in pupils]
    results = (
        db.query(Parent, ParentChild, Pupil)
        .join(ParentChild, Parent.parent_id == ParentChild.parent_id)
        .join(Pupil, ParentChild.child_id == Pupil.pupil_id)
        .filter(ParentChild.child_id.in_(pupil_ids))
        .order_by(Parent.full_name)
        .all()
    )
    seen = set()
    parents = []
    for parent, pc, pupil in results:
        if parent.parent_id not in seen:
            seen.add(parent.parent_id)
            parents.append({
                "parent_id": parent.parent_id,
                "full_name": parent.full_name,
                "gender": parent.gender,
                "children": [],
            })
        # Добавляем ребёнка к последнему родителю
        parents[-1]["children"].append({
            "pupil_id": pupil.pupil_id,
            "full_name": pupil.full_name,
            "relation": pc.relation_type,
        })
    return parents
