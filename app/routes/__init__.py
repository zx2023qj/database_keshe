# routes/__init__.py
from flask import Blueprint
from .admin_routes import admin_blueprint
from .auth_routes import auth_blueprint
from .exam_routes import exam_blueprint
from .index_routes import index_blueprint
from .question_routes import question_blueprint
from .student_routes import student_blueprint
from .subject_routes import subject_blueprint
from .teacher_routes import teacher_blueprint
from .user_routes import user_blueprint


def init_routes(app):
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(exam_blueprint)
    app.register_blueprint(index_blueprint)  # 注册index路由模块
    app.register_blueprint(question_blueprint)
    app.register_blueprint(student_blueprint)
    app.register_blueprint(subject_blueprint)
    app.register_blueprint(teacher_blueprint)
    app.register_blueprint(user_blueprint)
    


