from flask import Flask, redirect, url_for, render_template, request, session
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
import random
import os
import re

app = Flask(__name__)
app.secret_key = "hello"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Posts-Users.sqlite3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_PERMANENT"] = False
app.permanent_session_lifetime = timedelta(minutes=5)
app.config["SESSION_TYPE"] = "filesystem"

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40))
    password = db.Column(db.String(16))
    posts = db.relationship('Post', backref='user')


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(1000))
    poster_id = db.Column(db.Integer, db.ForeignKey('user.id'))


@app.route("/")
def home():
    content = "Test"
    # getting files
    os.chdir(os.getcwd() + "/static")
    file_list = os.listdir()
    for file in file_list:
        if re.search("(([^.]+)$)", file).group() not in "jpgjpeg":
            file_list.remove(file)
    image = random.choice(file_list)
    os.chdir(os.getcwd()[:os.getcwd().index("/static")])
    return render_template("index.html", content=content, image=image)


@app.route("/create_user", methods=["GET", "POST"])
def create_user():
    content = ""
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]
        confirmed_password = request.form["confirmed_password"]
        if password != confirmed_password:
            return render_template("create_user.html", content="Invalid!")
        else:
            db.session.add(User(username=username, password=password))
            db.session.commit()
        for user in User.query.all():
            content += user.username
            content += ""
            content += user.password
            return content
    else:
        return render_template("create_user.html", content="")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session.keys():
        return redirect(url_for("profile_screen", username=session["username"]))
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]
        for user in User.query.all():
            test_user = user.username
            test_password = user.password
            if username == test_user and password == test_password:
                session["username"] = username
                session["password"] = password
                return redirect(url_for("profile_screen", username=username))
        return "invalid password"

    return render_template("login.html")


@app.route("/database", methods=["POST", "GET"])
def return_database():
    if request.method == 'POST':
        for user in User.query.all():
            if 'all' in request.form.getlist(user.username):
                db.session.delete(user)
                db.session.commit()
    return render_template("show_database.html", content=create_table())


@app.route("/profile/<username>")
def profile_screen(username):
    if "username" not in session.keys():
        return redirect(url_for("login"))
    else:
        if username == "default":
            return redirect(url_for("profile_screen", username=session["username"]))
    return render_template("profile.html", username=username)


def create_table():
    table = """
    <table class="table">
        <thead>
            <tr>
              <th scope="col">Id</th>
              <th scope="col">Username</th>
              <th scope="col">Password</th>
              <th scope="col">Delete</th>
            </tr>
      </thead>
        """
    row = 1
    for user in User.query.all():
        table += "<tr>\n" \
            + "<th scope=""row"">" + str(user.id) + "</td>\n" \
            + "<td>" + user.username + "</td>\n" + "<td>" \
            + user.password + "</td>\n" \
            + "<td>" + "<div class=""form-check"">\n" \
            + "<input class=""form-check-input"" type=""checkbox"" value=""all""  name= " \
            + "\"" + str(user.username) + "\"" + ">" \
            + "<label class=""form-check-label"">" + "Delete User" \
            + "</label>\n</div>\n</td>\n"
        row += 1
    table += "</tbody>\n</table>\n"
    return table


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
