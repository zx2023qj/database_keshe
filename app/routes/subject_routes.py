from flask import Flask, render_template, request, jsonify, session, redirect, url_for,make_response,Blueprint
from app.models import User,Subject,Log
from app import db
from datetime import datetime, timedelta

subject_blueprint = Blueprint('subject', __name__)

@subject_blueprint.route('/subject', methods=['POST'])
def subject():
    # check if user is logged in
    username = session.get('username')
    if not username:
        return jsonify({'status': 'error', 'message': 'Please login first'})
    
    # check if user is admin
    role = session.get('role')
    if role != 'admin':
        return jsonify({'status': 'error', 'message': 'Permission denied'})
    user_id = User.query.with_entities(User.id).filter(User.username == username).first().id
    action = request.form.get('action')

    # read all subjects
    if action == 'read':

        # get all subjects
        subjects = Subject.query.with_entities(Subject.id, Subject.name, Subject.exam_duration).all()
        subject_data = [{'id': subject.id, 'name': subject.name, 'duration': subject.exam_duration} for subject in subjects]
        
        # read subject log
        subject_read_event = Log(user_id=user_id, action='read',log_type='subject',details='Read all subjects')
        db.session.add(subject_read_event)
        db.session.commit()
        return jsonify({'subject': subject_data})

    # add subject
    elif action == 'add':

        # get data from form
        subject = request.form.get('subject')
        duration = request.form.get('duration')

        # check if subject already exists
        existing_subject = Subject.query.filter(Subject.name == subject).first()
        if existing_subject:
            return jsonify({'status': 'error', 'message': 'Subject already exists'})

        # add new subject
        add_subject = Subject(name=subject, exam_duration=duration)
        db.session.add(add_subject)
        db.session.commit() 

        # add subject log
        subject_add_event = Log(user_id=user_id, action='add',log_type='subject',details='success add subject:' + subject)
        db.session.add(subject_add_event)
        db.session.commit()
        return jsonify({'status': 'success','message': 'Subject added successfully:'+subject})

    # edit subject
    elif action == 'edit':

        # get data from form
        subject = request.form.get('subject')
        duration = request.form.get('duration')

        # if subject not exists
        edit_subject = Subject.query.filter(Subject.name == subject).first()
        if not edit_subject:
            return jsonify({'status': 'error', 'message': 'Subject not exists'})

        # edit subject 
        edit_subject.exam_duration = duration
        update_time = datetime.utcnow() + timedelta(hours=8)
        edit_subject.updated_time = update_time
        db.session.add(edit_subject)
        db.session.commit()

        # edit subject log
        subject_edit_event = Log(user_id=user_id, action='edit',log_type='subject',details='success edit subject:' + subject)
        db.session.add(subject_edit_event)
        db.session.commit()
        return jsonify({'status': 'success','message': 'Subject edited successfully:'+subject})

    # delete subject
    elif action == 'delete':

        # get data from form    
        subject = request.form.get('subject')
        delete_subject = Subject.query.filter(Subject.name == subject).first()

        # if subject exists
        if delete_subject:
            db.session.delete(delete_subject)
            db.session.commit()
            
            # delete subject log
            subject_delete_event = Log(user_id=user_id, action='delete',log_type='subject',details='success delete subject:' + subject)
            db.session.add(subject_delete_event)
            db.session.commit()
            return jsonify({'status': 'success','message': 'Subject deleted successfully:'+subject})
        
        return jsonify({'status': 'error', 'message': 'subject not found'})

    return jsonify({'status': 'error', 'message': 'Invalid action'})