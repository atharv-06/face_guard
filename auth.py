# auth.py
from flask_login import LoginManager, UserMixin
from models import User

login_manager = LoginManager()
login_manager.login_view = "login"

class UserLogin(UserMixin):
    def __init__(self, user: User):
        self._user = user

    @property
    def id(self):
        return str(self._user.id)

    @property
    def username(self):
        return self._user.username

@login_manager.user_loader
def load_user(user_id):
    u = User.query.get(int(user_id))
    if u:
        return UserLogin(u)
    return None
