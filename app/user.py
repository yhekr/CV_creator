from flask_login import UserMixin
from flask import url_for


class User(UserMixin):
    def get_from_database(self, user_id, db):
        self.__user = db.getUser(user_id)
        return self

    def create(self, user):
        self.__user = user
        return self

    def get_id(self):
        return str(self.__user['id'])

    def get_name(self):
        return self.__user['name'] if self.__user else "No name"

    def get_resume(self):
        if not self.__user:
            return "You don't have CV"
        elif self.__user['resume'] == None:
            return "You don't have CV"
        else:
            return self.__user['resume']

    def get_avatar(self, app):
        img = None
        if not self.__user['avatar']:
            try:
                with app.open_resource(app.root_path + url_for('static', filename='images/default.png'), "rb") as f:
                    img = f.read()
            except FileNotFoundError as e:
                print("No avatar: "+str(e))
        else:
            img = self.__user['avatar']
 
        return img

    def format_verify(self, filename):
        format = filename.rsplit('.', 1)[1]
        if format == "png" or format == "PNG":
            return True
        return False