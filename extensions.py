from flask_login import LoginManager 

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):

    #imported here to avoid circular imports with app.py

    from models import get_user_by_id 

    #return the user object after taking in the user ID as input, else None if there is no match.

    return get_user_by_id(user_id)


