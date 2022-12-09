from flask import Flask, render_template, request, flash, session, redirect, url_for, abort
from app import app

import sqlite3
import os
from flask import Flask, render_template, request, g, make_response

from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from .user import User
from .FDataBase import FDataBase

MAX_CONTENT_LENGTH = 1024 * 1024

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "you should be authorised"
login_manager.login_message_category = "success"

@login_manager.user_loader
def load_user(user_id):
    print("load_user")
    return User().get_from_database(user_id, dbase)


def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def create_db():
    db = connect_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()

def get_db():
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db

dbase = None
@app.before_request
def before_request():
    global dbase
    db = get_db()
    dbase = FDataBase(db)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()

@app.route("/")
def index():
    return render_template('index.html', menu=dbase.getMenu())

@app.route("/add_resume", methods=["POST", "GET"])
@login_required
def add_resume():
    if request.method == "POST":
        resume = "My name is " + str(request.form['name']) + " " + str(
            request.form['surname']) + ', I am ' + str(request.form['age']) +\
                 ' years old. This is information about me: ' + str(
            request.form['other'])
        res = dbase.updateUserResume(current_user.get_id(),
                                     resume)
        if not res:
            flash('Error', category='error')
        else:
            flash('Success', category='success')

    return render_template('add_post.html', title="New resume")


@app.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    if request.method == "POST":
        user = dbase.getUserByEmail(request.form['email'])
        if user and check_password_hash(user['psw'], request.form['psw']):
            userlogin = User().create(user)
            rm = True if request.form.get('remainme') else False
            login_user(userlogin, remember=rm)
            return redirect(request.args.get("next") or url_for("profile"))
        flash("Wrong login or password", "error")

    return render_template("login.html", title="Log in")

@app.route('/view_cv')
def view_cv():
    return render_template('view_cv.html', title="My CV")


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        if len(request.form['name']) > 4 and len(request.form['email']) > 4 \
            and len(request.form['psw']) > 4 and request.form['psw'] == request.form['psw2']:
            hash = generate_password_hash(request.form['psw'])
            res = dbase.addUser(request.form['name'], request.form['email'], hash)
            if res:
                flash("Success", "success")
                return redirect(url_for('login'))
            else:
                flash("Error", "error")
        else:
            flash("Error", "error")

    return render_template("register.html", title="Log in")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You logged out", "success")
    return redirect(url_for('login'))


@app.route('/profile')
def profile():
    return render_template('profile.html', title="My account")

@app.route('/userava')
@login_required
def userava():
    img = current_user.get_avatar(app)
    if not img:
        return ""
 
    h = make_response(img)
    h.headers['Content-Type'] = 'image/png'
    return h

@app.route('/upload', methods=["POST", "GET"])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and current_user.format_verify(file.filename):
            try:
                img = file.read()
                res = dbase.updateUserAvatar(img, current_user.get_id())
                if not res:
                    flash("Error", "error")
                    return redirect(url_for('profile'))
                flash("Success", "success")
            except FileNotFoundError as e:
                flash("Error", "error")
        else:
            flash("Error", "error")
 
    return redirect(url_for('profile'))


@app.errorhandler(404)
def pageNotFount(error):
    return render_template('page404.html', title="Page not found 404"), 404

if __name__ == "__main__":
    app.run(debug=True)
