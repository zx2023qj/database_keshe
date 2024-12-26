from . import db
from datetime import datetime, timedelta

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True)
    role = db.Column(db.String(50), nullable=False)
    ip = db.Column(db.String(45), nullable=True)
    created_time = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(hours=8))
    updated_time = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(hours=8), onupdate=datetime.utcnow() + timedelta(hours=8))

    # 添加关系属性，用于删除用户时级联删除用户关联的科目
    user_usersubjects = db.relationship('UserSubject', backref='user', cascade='all, delete-orphan')
    user_examrecords = db.relationship('ExamRecord', backref='user', cascade='all, delete-orphan')
    user_questions = db.relationship('Question', backref='user', cascade='all, delete-orphan')

class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"),nullable=False)
    created_time = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(hours=8))
    updated_time = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(hours=8), onupdate=datetime.utcnow() + timedelta(hours=8))

    # 添加关系属性，用于删除问题时级联删除问题关联的选项和答案
    questions_choices = db.relationship('Choice', backref='question', cascade='all, delete-orphan')
    questions_answers = db.relationship('Answer', backref='question', cascade='all, delete-orphan')
    exam_questions = db.relationship('ExamQuestion', backref='question', cascade='all, delete-orphan')

class Subject(db.Model):
    __tablename__ = "subjects"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    exam_duration = db.Column(db.Integer, nullable=False)
    created_time = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(hours=8))
    updated_time = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(hours=8), onupdate=datetime.utcnow() + timedelta(hours=8))
    # 添加关系属性，用于删除科目时级联删除科目关联的问题
    subject_questions = db.relationship('Question', backref='subject', cascade='all, delete-orphan')
    subject_usersubjects = db.relationship('UserSubject', backref='subject', cascade='all, delete-orphan')
    subject_examrecords = db.relationship('ExamRecord', backref='subject', cascade='all, delete-orphan')

class UserSubject(db.Model):
    __tablename__ = "user_subjects"
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), primary_key=True)
    exam_done = db.Column(db.Boolean, nullable=False)

class Answer(db.Model):
    __tablename__ = "answers"
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    answer_text = db.Column(db.Text, nullable=False)
    created_time = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(hours=8))
    updated_time = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(hours=8), onupdate=datetime.utcnow() + timedelta(hours=8))

class Choice(db.Model):
    __tablename__ = "choices"
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    content = db.Column(db.String(255), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    created_time = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(hours=8))
    updated_time = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(hours=8), onupdate=datetime.utcnow() + timedelta(hours=8))

class ExamRecord(db.Model):
    __tablename__ = "exam_records"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    score = db.Column(db.Float, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_time = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(hours=8))

    # 添加关系属性，用于删除考试记录时级联删除考试记录关联的考试问题
    exam_questions = db.relationship('ExamQuestion', backref='exam_record', cascade='all, delete-orphan')

class ExamQuestion(db.Model):
    __tablename__ = "exam_questions"
    id = db.Column(db.Integer, primary_key=True)
    exam_record_id = db.Column(db.Integer, db.ForeignKey("exam_records.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    user_answer = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    created_time = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(hours=8))

class Log(db.Model):
    __tablename__ = "logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(255), nullable=False)
    log_type = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text, nullable=True)
    created_time = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(hours=8))
