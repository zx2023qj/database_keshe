from flask import render_template, session, redirect, url_for,Blueprint
from app.models import User,Subject

admin_blueprint = Blueprint('admin', __name__)

@admin_blueprint.route('/admin')
def admin():
    
    # Check if user is logged in and is an admin
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    # get user info 
    user = User.query.filter_by(username=session['username']).first()
    admin_info = {"name": user.username}
    subjects = Subject.query.with_entities(Subject.name).all()
    return render_template('admin.html', admin_info=admin_info,subjects = subjects)