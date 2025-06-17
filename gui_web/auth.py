from flask import session, redirect, url_for, request, render_template, jsonify
from functools import wraps

# Dummy user for demonstration
# TEMPORARY LOGIN CREDENTIALS - DELETE WHEN ACTUAL FUNCTIONALITY IS IMPLEMENTED
USERS = {
    'admin': 'password123',
    'user': 'testpass',
    'John Doe': '1234'  # TEMP: REMOVE THIS USER LATER
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def register_login_routes(app):
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'GET':
            return render_template('login.html')
        username = request.form.get('username')
        password = request.form.get('password')
        if username in USERS and USERS[username] == password:
            session['user'] = username
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Invalid username or password.'})

    @app.route('/logout')
    def logout():
        session.pop('user', None)
        return redirect(url_for('login'))
