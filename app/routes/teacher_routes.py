from flask import Flask, render_template, request, jsonify, session, redirect, url_for,make_response,Blueprint
from app.models import User,Subject,Log,UserSubject

teacher_blueprint = Blueprint('teacher', __name__)

@teacher_blueprint.route('/teacher')
def teacher():
    # check if user is logged in
    if 'username' not in session:
        return redirect(url_for('auth.login')) 

    # check if user is teacher
    username = session.get('username')
    role = session.get('role')
    if role != 'teacher':
        return redirect(url_for('index.index'))  
    
    # get info about teacher
    user = User.query.filter_by(username=username).first()
    user_subjects = user.user_usersubjects
    subject_data = [{'id': user_subject.subject.id, 'name': user_subject.subject.name} for user_subject in user_subjects]
    teacher_info = {
        'name': session.get('username'),
        'subjects': subject_data 
    }
    
    return render_template('teacher.html', teacher_info=teacher_info)