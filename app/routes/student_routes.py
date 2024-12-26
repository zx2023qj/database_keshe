from flask import Flask, render_template, request, jsonify, session, redirect, url_for,make_response,Blueprint
from app.models import User

student_blueprint = Blueprint('student', __name__)

@student_blueprint.route('/student')
def student():
    
    # check if user is logged in
    if 'username' not in session:
        return redirect(url_for('auth.login'))  # 如果没有登录，跳转到登录页面
    if session['role'] != 'student':
        return redirect(url_for('index.index'))  # 如果不是学生，跳转到首页
    username = session['username']

    # get info about student
    user = User.query.filter_by(username=username).first()
    user_subjects = user.user_usersubjects
    subject_data = [{'id': user_subject.subject.id, 'name': user_subject.subject.name,'exam_done':str(user_subject.exam_done).lower()} for user_subject in user_subjects]
    student_info = {
        'id': user.id,
        'username': user.username,
        'email': user.email
    }

    return render_template('student.html', student_info=student_info,subjects=subject_data)