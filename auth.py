# auth.py
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from models import db, User

login_manager = LoginManager()
login_manager.login_view = "auth.login"

# small wrapper to adapt models.User to flask-login
class UserLogin(UserMixin):
    def __init__(self, user: User):
        self._user = user

    @property
    def id(self):
        return str(self._user.id)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_user(self):
        return self._user

@login_manager.user_loader
def load_user(user_id):
    u = User.query.get(int(user_id))
    if not u:
        return None
    return UserLogin(u)
