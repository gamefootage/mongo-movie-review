import os
from flask import (
  Flask, flash, render_template, redirect, request, session, url_for
)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import flask_pymongo
import pymongo
from pymongo.message import update
from werkzeug import useragents
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
  import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/movies")
def get_movies():
  movies = list(mongo.db.movies.find())
  return render_template("movies.html", movies=movies)


@app.route("/login", methods=["POST", "GET"])
def login():
  if request.method == "POST":
    db_user = mongo.db.users.find_one({
      "username": request.form.get("username")
    })
    
    if db_user:
      if check_password_hash(
        db_user["password"], request.form.get("password")
      ):
        print(db_user["_id"])
        # store user info in session
        session["user"] = {
          "_id": str(db_user["_id"]),
          "username": db_user["username"],
          "profile_url": db_user["profile_url"]
        }
        return redirect(url_for('get_movies'))
      else:
          # incorrect password
          flash("Incorrect login details", "error")
          return redirect(url_for('login'))
    else: 
      # username not found
      flash("Incorrect login details", "error")
   
  return render_template("login.html")



@app.route("/register", methods=["GET", "POST"])
def register():
  if request.method == "POST":

    profile_url = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png"
    new_user = {
      "username": request.form.get("username").lower(),
      "password": generate_password_hash(request.form.get("password")),
      "profile_url": profile_url
    }
    mongo.db.users.insert_one(new_user)
    db_user = mongo.db.users.find_one({
      "username": new_user["username"]
    })

    # put new user into sesssion cookie
    session["user"] = {
      "_id": str(db_user["_id"]),
      "username": db_user["username"],
      "profile_url": db_user["profile_url"]
    }
    flash("Regisration Successful!")
    return redirect(url_for('get_movies'))

  return render_template("register.html")


@app.route("/profile", methods=["GET", "POST"])
def show_profile():
  if request.method == "POST":
    print(session["user"]["_id"])
    mongo.db.users.update_one({ "_id": ObjectId(session["user"]["_id"]) },
      {
        "$set": { "profile_url": request.form.get("profile_url") }
      }
    )
   
    db_user = mongo.db.users.find_one({"_id": ObjectId(session["user"]["_id"]) })
    print(db_user)

    if db_user:
      session["user"] = {
        "_id": str(db_user["_id"]),
        "username": db_user["username"],
        "profile_url": db_user["profile_url"]
      }
      flash("Profile image changed successfully")
      return redirect(url_for('get_movies'))
    else:
      flash("Error updating user profile. Please try again")

  user = session["user"]
  if user:
    return render_template("profile.html", user=user)
  else:
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
  session["user"] = {}
  return redirect(url_for('login'))


@app.route("/delete/<movie_id>/")
def delete_movie(movie_id):
  user_id = session["user"]["_id"]
  # Only allow user to delte if user submitted the movie
  result = mongo.db.movies.delete_one({
    "_id": ObjectId(movie_id), 
    "submitted_by": ObjectId(user_id)
  })

  print(result)

  if result.deleted_count > 0:
    flash("Movie successfully deleted")
  else:
    flash("You do not have the correct permissions to delete this movie")

  return redirect(url_for('get_movies'))



@app.route("/edit/<movie_id>", methods=["GET", "POST"])
def edit_movie(movie_id):
  if request.method == "GET":
    if movie_id == 'form':
      movie_id = request.args.get("edit_movie_id")

    user_id = session["user"]["_id"]
    movie = mongo.db.movies.find_one({
      "_id": ObjectId(movie_id),
      "submitted_by": ObjectId(user_id)
    })

    if not movie:
      flash("You don't have the correct permissions to edit this movie")
    else:
      return render_template("edit_movie.html", movie=movie)
  elif request.method == "POST":
    user_id = session["user"]["_id"]
    movie = mongo.db.movies.find_one({
      "_id": ObjectId(movie_id),
      "submitted_by": ObjectId(user_id)
    })

    edit = {
      "title": request.form.get('title'),
      "description": request.form.get('description'),
      "starring": request.form.get("starring").split(","),
      "cover_image_url": request.form.get("cover_image_url"),
      "director": request.form.get("director")
    }
    result = mongo.db.movies.update_one({ "_id": ObjectId(movie_id) },
      {
        "$set": edit
      }
    )
    if result.modified_count > 0:
      flash("Movie successfully edited")
      return redirect(url_for('get_movies'))
    else:
      flash("Error updating movie. Please try again")
      return render_template("edit_movie.html", movie=movie)


  return redirect(url_for('get_movies'))
  

@app.route("/add-review/<movie_id>", methods=["POST", "GET"])
def add_review(movie_id):
  new_review = {
    "reviewer": request.form.get("reviewer"), 
    "review": request.form.get("review") 
  }
  result = mongo.db.movies.update_one(
    { "_id": ObjectId(movie_id) },
    { "$push": { "reviews": new_review } }
  )

  if result.modified_count > 0:
    flash("Review successfully added")
  else:
    flash("There was an error submitting your review. Please try again")

  return redirect(url_for('get_movies'))


if __name__ == "__main__":
  app.run(host=os.environ.get("IP"), 
          port=int(os.environ.get("PORT")), 
          debug=True)

#             REGISTER LOGIC
#  profile_url = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png"
#     new_user = {
#       "username": request.form.get("username").lower(),
#       "password": generate_password_hash(request.form.get("password")),
#       "profile_url": profile_url
#     }
#     mongo.db.users.insert_one(new_user)

#     # put new user into sesssion cookie
#     session["user"] = {
#       "username": request.form.get("username").lower(),
#       "profile_url": profile_url
#     }
#     flash("Regisration Successful!")
#     return redirect(url_for('get_movies'))