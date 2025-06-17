from db.user_repository import UserRepository

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
