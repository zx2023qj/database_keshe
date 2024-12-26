from flask import Flask, render_template, request, jsonify, session, redirect, url_for,make_response,Blueprint
from app.models import User,Subject,UserSubject,Log
from app import db,redis_client
from hashlib import sha256
from datetime import datetime, timedelta
import json


user_blueprint = Blueprint('user', __name__)

@user_blueprint.route('/user', methods=['POST'])
def user():

    # check if user is logged in and is admin
    username = session.get('username')
    if not username:
        return jsonify({'status': 'error', 'message': 'Please login first'})
    role = session.get('role')
    if role != 'admin':
        return jsonify({'status': 'error', 'message': 'Permission denied'})

    # get user id and action
    action = request.form.get('action')
    user_id = User.query.with_entities(User.id).filter(User.username == username).first().id  
    if action == 'read':

        # read user from redis
        redis_users = redis_client.lrange('users', 0, -1)
        if redis_users:
            userdata = [json.loads(redis_user) for redis_user in redis_users]
        else:
            # read user from mysql
            users = User.query.with_entities(User.id, User.username, User.email, User.role).all()
            userdata = [{'id': user.id, 'username': user.username, 'email': user.email,'role':user.role} for user in users]
        
        # read user log by user
        user_read_event = Log(user_id=user_id, action='read',log_type='user',details='Read all users')
        db.session.add(user_read_event)
        db.session.commit()
        return jsonify({'user': userdata})

    elif action == 'add':

        # get data from form
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        role = request.form.get('role')
        subjects = request.form.getlist('subjects[]')
        ip_address = request.remote_addr

        # check if username or email already exists
        user = User.query.filter((User.username == username) | (User.email == email)).first()
        if user:
            return jsonify({'status': 'error', 'message': 'Username or Email already exists'})

        # add user to mysql
        hashed_password = sha256(password.encode()).hexdigest()
        add_user = User(username=username, password=hashed_password, email=email, role=role, ip=ip_address)
        db.session.add(add_user)
        db.session.commit()
        
        # add user to redis
        redis_client.rpush('users', json.dumps({'id': add_user.id, 'username': add_user.username, 'email': add_user.email,'role':add_user.role}))

        # add user subjects
        # delete duplicate subjects
        subjects = list(set(subjects))
        for subject in subjects:
            subject_id = Subject.query.filter_by(name=subject).first().id
            add_user_subject = UserSubject(user_id=add_user.id, subject_id=subject_id, exam_done=False)
            db.session.add(add_user_subject)
            db.session.commit()

        # add user log by user
        user_add_event = Log(user_id=user_id, action='add',log_type='user',details='success add user:' + username)
        db.session.add(user_add_event)
        db.session.commit()

        # add user log by new user
        user_add_event = Log(user_id=add_user.id, action='add',log_type='user',details='Add user:' + username)
        db.session.add(user_add_event)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'User added successfully'})

    elif action == 'edit':

        # get data from form
        username = request.form.get('username')
        password = request.form.get('password')
        subjects = request.form.getlist('subjects[]')
        ip_address = request.remote_addr

        # check if user exists
        user = User.query.filter(User.username == username).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'})
        
        # edit user
        hashed_password = sha256(password.encode()).hexdigest()
        user.password = hashed_password
        user.ip = ip_address
        updated_time = datetime.utcnow() + timedelta(hours=8)
        user.updated_time = updated_time
        db.session.commit()

        # update user subjects
        old_subjects = UserSubject.query.filter(UserSubject.user_id == user.id).all()

        # drop old subjects
        for old_subject in old_subjects:
            db.session.delete(old_subject)
            db.session.commit()

        # add new subjects
        # delete duplicate subjects
        subjects = list(set(subjects))
        for subject in subjects:
            subject_id = Subject.query.filter_by(name=subject).first().id
            edit_user_subject = UserSubject(user_id=user.id, subject_id=subject_id, exam_done=False)
            db.session.add(edit_user_subject)
            db.session.commit()

        # edit user log by user
        user_edit_event = Log(user_id=user_id, action='edit',log_type='user',details='success edit user:' + username)
        db.session.add(user_edit_event)
        db.session.commit()

        # edit user log by new user
        user_edit_event = Log(user_id=user.id, action='edit',log_type='user',details='Edit user:' + username)
        db.session.add(user_edit_event)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'User edited successfully'})



        
    elif action == 'delete':

        # get data from form
        username = request.form.get('username')
        user = User.query.filter(User.username == username).first()
        
        # check if user exists and is not admin
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'})
        if username == 'admin':
            return jsonify({'status': 'error', 'message': 'perssion denied'})
        
        # delete user log by new user (add log before delete user)
        user_delete_event = Log(user_id=user.id, action='delete',log_type='user',details='Delete user:' + username)
        db.session.add(user_delete_event)
        db.session.commit()

        # delete user in redis
        redis_users = redis_client.lrange('users', 0, -1)
        for redis_user in redis_users:
            redis_user = json.loads(redis_user)
            if redis_user['username'] == username:
                redis_client.lrem('users', 0, json.dumps(redis_user))
                break

        # delete user
        db.session.delete(user)
        db.session.commit()
        # delete user log by user
        user_delete_event = Log(user_id=user_id, action='delete',log_type='user',details='success delete user:' + username)
        db.session.add(user_delete_event)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'User deleted successfully'})

    return jsonify({'status': 'error', 'message': 'Invalid action'})