#!flask/bin/python
from flask import Flask, request, redirect, render_template, session
from helloworld.utils import (
    save_user_data,
    upload_picture,
    get_user,
    get_image_list,
    compare_faces,
    get_file_url,
    get_user_by_image,
    filter_data,
    delete_picture,
)
import os
from helloworld.flaskrun import flaskrun


app = Flask(__name__)

app.config["SECRET_KEY"] = "221714a843f5b44f8b9e71cf77b87ba7d2020140d4641df9"


# Route for the login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user"):
        return redirect("/")

    if request.method == "POST":
        email = request.form["email"]

        user_info = get_user(email)

        if user_info:
            session["user"] = user_info
            return redirect("/")

        else:
            return redirect("/signup")

    return render_template("login.html")


# Route for the signup page
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        file = request.files["profile_picture"]
        data = {**request.form}

        data["profile_picture"] = upload_picture(file)
        save_user_data(data)
        return redirect("/login")

    return render_template("signup.html")


@app.route("/find_by_picture", methods=["POST", "GET"])
def find_by_picture():
    if not session.get("user"):
        return redirect("/login")
    result = []

    if request.method == "POST":
        file = request.files["file"]
        key = "temp"
        upload_picture(file, key=key)
        file_path = os.path.join(key, file.filename)

        target_images = get_image_list()
        users_images_url = []

        # Compare faces with each image
        for target_image in target_images:
            if not target_image.startswith(key):
                face_matches = compare_faces(file_path, target_image)
                if face_matches:
                    users_images_url.append(
                        get_file_url(target_image),
                    )

        delete_picture(file_path)

        result = []
        for url in users_images_url:
            user_info = get_user_by_image(url)
            if user_info:
                result.append(user_info)

    return render_template("result.html", result=result)


@app.route("/find_by_details", methods=["POST", "GET"])
def find_by_details():
    if not session.get("user"):
        return redirect("/login")

    result = []

    if request.method == "POST":
        data = request.form.to_dict()

        data = {
            key: value
            for key, value in data.items()
            if value is not None and value != ""
        }

        result = filter_data(data)

    return render_template("result.html", result=result)


@app.route("/")
def index():
    if not session.get("user"):
        return redirect("/login")
    user_info = session["user"]
    return render_template("index.html", user=user_info)


if __name__ == "__main__":
    flaskrun(app)
