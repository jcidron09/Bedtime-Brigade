from flask import Flask, redirect, url_for, render_template, request, session, flash, send_from_directory
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import random
import os
import re


app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
    alias = db.Column(db.String(20))
    password = db.Column(db.String(16))
    admin = db.Column(db.Boolean)
    posts = db.relationship('Post', backref='user')


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(1000))
    date = db.Column(db.String(20))
    timestamp = db.Column(db.String(20))
    poster_id = db.Column(db.Integer, db.ForeignKey('user.id'))


@app.route("/")
def home():
    content = "Test"
    # getting files
    os.chdir(os.getcwd() + "/static")
    file_list = os.listdir()
    for file in file_list:
        if re.search("(([^.]+)$)", file).group() not in "txtpngjpgjpeggif'":
            file_list.remove(file)
    image = random.choice(file_list)
    os.chdir(os.getcwd()[:os.getcwd().index("/static")])
    return render_template("index.html", content=content, image=image)


@app.route("/create_user", methods=["GET", "POST"])
def create_user():
    content = ""
    if request.method == 'POST':
        username = request.form["username"]
        alias = request.form["alias"]
        password = request.form["password"]
        confirmed_password = request.form["confirmed_password"]
        if password != confirmed_password:
            return render_template("create_user.html", content="Invalid!")
        else:
            for user in User.query.all():
                if username == user.username:
                    return render_template("create_user.html", content="Username is Taken")
            db.session.add(User(username=username, alias=alias, password=password, admin=False))
            db.session.commit()
            return redirect(url_for("login"))
    else:
        return render_template("create_user.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session.keys():
        return redirect(url_for("profile_screen", username=session["user"]))
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]
        for user in User.query.all():
            test_user = user.username
            test_password = user.password
            if username == test_user and password == test_password:
                session["user"] = username
                session["alias"] = user.alias
                return redirect(url_for("profile_screen", username=username))
        return "invalid password"
    return render_template("login.html")


@app.route("/database", methods=["POST", "GET"])
def show_database():
    if request.method == 'POST':
        for user in User.query.all():
            username = user.username
            if 'delete_user' in request.form.getlist(user.username):
                db.session.delete(user)
                db.session.commit()
            if 'make_admin' in request.form.getlist(user.username):
                db.session.query(User).filter(user.username == username).update({'admin': True})
                db.session.commit()
            if 'remove_admin' in request.form.getlist(user.username):
                db.session.query(User).filter(user.username == username).update({'admin': False})
                db.session.commit()
    return render_template("show_database.html", content=create_table())


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile_screen(username):
    username = ""
    alias = ""
    if request.method == "POST":
        session.pop("user", None)
        return redirect(url_for("login"))
    else:
        if "user" not in session.keys():
            return redirect(url_for("login"))
        else:
            for user in User.query.all():
                if user.username == session["user"]:
                    username = session["user"]
                    alias = session["alias"]
                    return render_template("profile.html", alias=alias, username=username)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# @app.route('/uploads/<name>')
# def download_file(name):
#    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


@app.route("/archives", methods=['GET', 'POST'])
def archives():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return render_template("archives.html", gallery=create_gallery("Archives"))


def create_gallery(directory):
    gallery = "\t\t\t<div class=\"row\">\n"
    file_list = os.listdir("static/Archives")
    for file in file_list:
        if re.search("(([^.]+)$)", file).group() not in "jpgjpegpnggifhiec":
            file_list.remove(file)
    for image in file_list:
        gallery += "\t\t\t\t<div class=\"col-lg-4 mb-4 mb-lg-0\">\n"
        gallery += "\t\t\t\t\t<img\n"
        gallery += "\t\t\t\t\t\tsrc=\"static/" + directory + "/" + image + "\"\n"
        gallery += "\t\t\t\t\t\tclass=\"w-100 shadow-1-strong rounded mb-4\"\n"
        gallery += "\t\t\t\t\t\twidth=\"25%\"\n"
        gallery += "\t\t\t\t\t/>\n"
        gallery += "\t\t\t\t</div>\n"
    gallery += "\t\t\t</div>"
    return gallery

def create_table():
    table = """
    <table class="table">
        <thead>
            <tr>
              <th scope="col">Id</th>
              <th scope="col">Username</th>
              <th scope="col">Alias</th>
              <th scope="col">Password</th>
              <th scope="col">Is Admin</th>
              <th scope="col">Make Admin</th>
              <th scope="col">Remove Admin</th>
              <th scope="col">Delete</th>
            </tr>
      </thead>
        """
    row = 1
    for user in User.query.all():
        table += "<tr>\n" \
            + "<th scope=""row"">" + str(user.id) + "</td>\n" \
            + "<td>" + user.username + "</td>\n" \
            + "<td>" + user.alias + "</td\n>" \
            + "<td>" + user.password + "</td>\n" \
            + "<td>" + str(user.admin) + "</td>\n" \
            + "<td>" + "<div class=""form-check"">\n" \
            + "<input class=""form-check-input"" type=""checkbox"" value=""make_admin""  name= " \
            + "\"" + str(user.username) + "\"" + ">" \
            + "<label class=""form-check-label"">" + "Make Admin" \
            + "</label>\n</div>\n</td>\n" \
            + "<td>" + "<div class=""form-check"">\n" \
            + "<input class=""form-check-input"" type=""checkbox"" value=""remove_admin""  name= " \
            + "\"" + str(user.username) + "\"" + ">" \
            + "<label class=""form-check-label"">" + "Remove Admin" \
            + "</label>\n</div>\n</td>\n" \
            + "<td>" + "<div class=""form-check"">\n" \
            + "<input class=""form-check-input"" type=""checkbox"" value=""delete_user""  name= " \
            + "\"" + str(user.username) + "\"" + ">" \
            + "<label class=""form-check-label"">" + "Delete User" \
            + "</label>\n</div>\n</td>\n"
        row += 1
    table += "</tbody>\n</table>\n"
    return table


if __name__ == "__main__":
    db.create_all()
    app.run(host="0.0.0.0", debug=True)
