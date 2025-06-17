from models import db
from models.users import User
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

class UserRepository:
    @staticmethod
    def create_user(username, password, role):
        password_hash = generate_password_hash(password)
        user = User(username=username, password_hash=password_hash, role=role)
        db.session.add(user)
        try:
            db.session.commit()
            return user, None
        except IntegrityError:
            db.session.rollback()
            return None, 'Username already exists.'
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def get_user_by_username(username):
        return User.query.filter_by(username=username).first()

    @staticmethod
    def get_all_users():
        return User.query.all()

    @staticmethod
    def delete_user(user_id):
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return True
        return False
