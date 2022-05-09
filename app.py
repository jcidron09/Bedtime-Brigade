from flask import Flask, redirect, url_for, render_template, request, session, flash, send_from_directory
from datetime import timedelta
import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import random
import os
import re
import shutil


app = Flask(__name__)
UPLOAD_FOLDER = "static/Archives"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
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
    caption = db.Column(db.String(255))
    date = db.Column(db.String(20))
    timestamp = db.Column(db.String(20))
    poster = db.Column(db.Integer, db.ForeignKey('user.id'))


@app.route("/")
def home():
    content = "Test"
    file_list = os.listdir("static/Archives")
    for file in file_list:
        if re.search("(([^.]+)$)", file).group() not in "png jpg jpeg":
            file_list.remove(file)
    image = "Archives/" + random.choice(file_list)
    print(image)
    return render_template("index.html", content=content, image=image)


@app.route("/create_user", methods=["GET", "POST"])
def create_user():
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
        return render_template("login.html", content="Invalid Password")
    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile_screen(username):
    if request.method == "POST":
        session.pop("user", None)
        return redirect(url_for("login"))
    else:
        if "user" not in session.keys():
            return redirect(url_for("login"))
        else:
            for user in User.query.all():
                if user.username == session["user"]:
                    username = session['user']
                    alias = session["alias"] 
                    if user.admin == True:
                       username = "<h1 class=\"admin username\">" +"(@" + username +")"
                       alias ="<h1 class=\"admin username\">" + alias + "</h1>"
                    else:
                      username = "<h1>" + "(@" + session["user"] +")" + "</h1>" 
                      alias = "<h1>" + session["alias"] + "</h1>"                      
                    return render_template("profile.html", title_username=session['user'],alias=alias, username=username, content=user_posts(session['user']))


@app.route("/archives", methods=['GET', 'POST'])
def archives():
    return render_template("archives.html", gallery=create_gallery())


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)

@app.route("/create_post", methods=['POST', 'GET'])
def create_post():
    if 'user' not in session.keys():
        return redirect(url_for("login"))
    else:
        if request.method == 'POST':
            # check if the post request has the file part
            if 'file' not in request.files:
                return redirect(request.url)
            file = request.files['file']
            # If the user does not select a file, the browser submits an
            # empty file without a filename.
            if file.filename == '':
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                this_post = Post(image=filename, caption=request.form['caption'], date=datetime.datetime.now().strftime("%x"), timestamp=datetime.datetime.now().strftime("%X"), poster=session['user'])
                db.session.add(this_post)
                db.session.commit()
                return render_template("create_post.html", content="POST")
        if request.method == 'GET':
            return render_template("create_post.html", content="GET")


@app.route("/database", methods=["POST", "GET"])
def show_database():
    if request.method == 'POST':
        for user in User.query.all():
            username = user.username
            if 'delete_user' in request.form.getlist(user.username):
                db.session.delete(user)
            if 'make_admin' in request.form.getlist(user.username):
                current_user = User.query.filter_by(username=username).first()
                current_user.admin = True
            if 'remove_admin' in request.form.getlist(user.username):
                current_user = User.query.filter_by(username=username).first()
                current_user.admin = False
        for post in Post.query.all():
            if 'delete_post' in request.form.getlist(post.timestamp):
              db.session.delete(post)
        db.session.commit()
    else:
      if 'user' not in session.keys():
        return redirect(url_for("login"))
      else:
        username = session['user']
        current_user = User.query.filter_by(username=username).first()
        if current_user.admin == False:
          return redirect(url_for("login"))
        else:
          return render_template("show_database.html", user_table=create_user_table(), post_table=create_post_table())
    return render_template("show_database.html",user_table=create_user_table(), post_table=create_post_table())



def create_gallery():
    gallery = "\t\t\t<div class=\"row\">\n"
    for post in Post.query.all():
        gallery += "\t\t\t\t<div class=\"col-lg-4 mb-4 mb-lg-0\">\n"
        gallery += "\t\t\t\t\t<img\n"
        gallery += "\t\t\t\t\t\tsrc=\"static/" + "Archives/" + post.image + "\"\n"
        print(post.image)
        gallery += "\t\t\t\t\t\tclass=\"w-100 shadow-1-strong rounded mb-4\"\n"
        gallery += "\t\t\t\t\t\twidth=\"25%\"\n"
        gallery += "\t\t\t\t\t/>\n"
        gallery += "\t\t\t\t\t<h6>" + post.poster + "</h6>"
        gallery += "\t\t\t\t\t<p>" + post.caption + "</p>"
        gallery += "\t\t\t\t</div>\n"
    gallery += "\t\t\t</div>"
    return gallery


def create_user_table():
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


def create_post_table():
    table = """
    <table class="table">
        <thead>
            <tr>
              <th scope="col">Id</th>
              <th scope="col">Image</th>
              <th scope="col">Caption</th>
              <th scope="col">Date</th>
              <th scope="col">Timestamp</th>
              <th scope="col">Poster</th>
            </tr>
        </thead>
    """
    for post in Post.query.all():
        table += "<tr>\n" \
            + "<th scope=""row"">" + str(post.id) + "</td>\n" \
            + "<td>" + post.image + "</td>\n" \
            + "<td>" + post.date + "</td\n>" \
            + "<td>" + post.caption + "</td\n>" \
            + "<td>" + post.timestamp + "</td>\n" \
            + "<td>" + post.poster + "</td>\n" \
            + "<td>" + "<div class=""form-check"">\n" \
            + "<input class=""form-check-input"" type=""checkbox"" value=""delete_post""  name= " \
            + "\"" + str(post.timestamp) + "\"" + ">" \
            + "<label class=""form-check-label"">" + "Delete POST" \
            + "</label>\n</div>\n</td>\n"
      
    table += "</tbody>\n</table>\n"
    return table

def user_posts(username):
  posts = "Posts: "
  for post in Post.query.all():
    for user in User.query.filter_by(username=username):
      table = """
    <table class="table">
        <thead>
            <tr>
              <th scope="col">Id</th>
              <th scope="col">Image</th>
              <th scope="col">Date</th>
              <th scope="col">Caption</th>
              <th scope="col">Timestamp</th>
              <th scope="col">Poster</th>
            </tr>
        </thead>
    """
    for post in Post.query.all():
      if post.poster == username:
        table += "<tr>\n" \
            + "<th scope=""row"">" + str(post.id) + "</td>\n" \
            + "\t\t<td>" + post.image + "</td>\n" \
            + "\t\t<td>" + post.date + "</td\n>" \
            + "\t\t<td>" + post.caption + "</td\n>" \
            + "\t\t<td>" + post.timestamp + "</td>\n" \
            + "\t\t<td>" + post.poster + "</td>\n"
    table += "</tbody>\n</table>\n"
    return table
  
  return posts

  
if __name__ == "__main__":
    db.create_all()
    print(user_posts("Jooshua"))
    app.run(host="0.0.0.0", debug=True)
