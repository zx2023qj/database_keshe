from flask import render_template, session, redirect, url_for,make_response,Blueprint

index_blueprint = Blueprint('index', __name__)

# index route
@index_blueprint.route('/')
def index():
    if 'username' in session:
        # if already login, redirect to main page
        role = session.get('role')

        if role == 'student':
            return redirect(url_for('student.student'))
        elif role == 'teacher':
            return redirect(url_for('teacher.teacher'))
        elif role == 'admin':
            return redirect(url_for('admin.admin'))

    return render_template('index.html')

# dashboard route
@index_blueprint.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('auth.login'))

    role = session['role']
    if role == 'student':
        return redirect(url_for('student.student'))
    elif role == 'teacher':
        return redirect(url_for('teacher.teacher'))
    elif role == 'admin':
        return redirect(url_for('admin.admin'))

# unknown route
@index_blueprint.route('/<path:path>')
def catch_all(path):
    return redirect(url_for('index.index'))



