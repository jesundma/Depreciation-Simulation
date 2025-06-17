from flask import session, redirect, url_for, request, render_template, jsonify
from functools import wraps

# Dummy user for demonstration
# TEMPORARY LOGIN CREDENTIALS - DELETE WHEN ACTUAL FUNCTIONALITY IS IMPLEMENTED
USERS = {
    'admin': {'password': 'password123', 'role': 'admin'},
    'user': {'password': 'testpass', 'role': 'user'},
    'John Doe': {'password': '1234', 'role': 'admin'},  # TEMP: REMOVE THIS USER LATER
    'Jack Doe': {'password': '1234', 'role': 'user'},   # TEMP: REMOVE THIS USER LATER
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session.get('role') != 'admin':
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def register_login_routes(app):
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'GET':
            return render_template('login.html')
        username = request.form.get('username')
        password = request.form.get('password')
        user = USERS.get(username)
        if user and user['password'] == password:
            session['user'] = username
            session['role'] = user['role']
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Invalid username or password.'})

    @app.route('/logout')
    def logout():
        session.pop('user', None)
        return redirect(url_for('login'))
