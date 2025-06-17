from models import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(16), nullable=False, default='user')  # 'user', 'viewer', 'admin'
    # Add more fields as needed (e.g., email, etc.)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def is_viewer(self):
        return self.role == 'viewer'

    def is_user(self):
        return self.role == 'user'

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'
