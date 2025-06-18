from db.user_repository import UserRepository
from models.users import User, Role
from models import db

class UserService:
    @staticmethod
    def create_user(username, password, role):
        return UserRepository.create_user(username, password, role)

    @staticmethod
    def get_user_by_username(username):
        return UserRepository.get_user_by_username(username)

    @staticmethod
    def get_all_users():
        return UserRepository.get_all_users()

    @staticmethod
    def delete_user(user_id):
        return UserRepository.delete_user(user_id)

    @staticmethod
    def search_users(query):
        # Search by partial username or role name
        return User.query.join(Role).filter(
            (User.username.ilike(f"%{query}%")) | (Role.name.ilike(f"%{query}%"))
        ).all()

    @staticmethod
    def delete_users(user_ids):
        try:
            for user_id in user_ids:
                user = User.query.get(user_id)
                if user:
                    db.session.delete(user)
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            return False, str(e)
