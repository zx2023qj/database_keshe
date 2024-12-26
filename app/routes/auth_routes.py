from flask import render_template, request, session, redirect, url_for,Blueprint
from app.models import User,Log
from app import db,redis_client
from hashlib import sha256
from datetime import datetime, timedelta
import json

auth_blueprint = Blueprint('auth', __name__)

# register route
@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        # get form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        ip_address = request.remote_addr

        # check if password and confirm_password are the same
        if password != confirm_password:
            error_message = "两次输入的密码不一致，请返回重试！"
            return render_template('register.html', error_message=error_message)
        
        # check if username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            error_message = "用户名或邮箱已存在，请返回重试！"
            return render_template('register.html', error_message=error_message)
        
        # save user to mysql
        hashed_password = sha256(password.encode()).hexdigest()
        new_user = User(username=username, email=email, password=hashed_password, role='student', ip=ip_address)
        db.session.add(new_user)
        db.session.commit()

        # save user to redis
        redis_client.rpush('users', json.dumps({
            'id': new_user.id,
            'username': new_user.username,
            'email': new_user.email,
            'role': new_user.role,
        }))
        # user register log
        register_event = Log(user_id=new_user.id, action='register',log_type='auth',details='success ip_address:' + new_user.ip)
        db.session.add(register_event)
        db.session.commit()    

        # return success page
        return render_template('register_success.html', username=username)

    return render_template('register.html')


# login route
@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        # get form data
        username = request.form.get('username')
        password = request.form.get('password')
        ip_address = request.remote_addr
        
        # get user from database
        user = User.query.filter_by(username=username).first()
        
        # check if user exists and password is correct
        if user and user.password == sha256(password.encode()).hexdigest():

            # login success, set session
            session['username'] = username
            session['role'] = user.role
            
            # updar user ip and updated_time
            # updated_time update automaticly depends on other data changing,so update_time need to froce update
            user.ip = ip_address
            user.updated_time = datetime.utcnow() + timedelta(hours=8)
            db.session.commit()
            
            # user login log
            login_event = Log(user_id=user.id, action='login',log_type='auth',details='success ip_address:' + user.ip)
            db.session.add(login_event)
            db.session.commit()
            return redirect(url_for('index.dashboard'))

        else:

            # login failed
            error_message = "用户名或密码错误"
            return render_template('login.html', error_message=error_message)

    return render_template('login.html')

# logout route
@auth_blueprint.route('/logout', methods=['POST'])
def logout():
    # login first
    if 'username' not in session:
        return redirect(url_for('auth.login'))

    # if method is POST
    if request.method == 'POST':

        # if user confirm to logout
        if request.form.get('confirm') == 'yes':
            
            # clear session
            username = session['username']
            session.clear()

            # user logout log
            user = User.query.filter_by(username=username).first()
            logout_event = Log(user_id=user.id, action='logout',log_type='auth',details='success')
            db.session.add(logout_event)
            db.session.commit()
            return redirect(url_for('index.index'))