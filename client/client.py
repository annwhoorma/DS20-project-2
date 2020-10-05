from flask import Flask, render_template, request
import json
import requests

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods = ["POST", "GET"])
def login():
    login = request.form.getlist('login')[0]
    password = request.form.getlist('password')[0]
    
    msg = json.dumps({"action" : "auth", "args" : {"login" : login, "password" : password}})
    
    response = requests.get("http://0.0.0.0:8080", json = msg).json()
    
    if response["status"] == "ok":
        return render_template("main.html")
    elif response["status"] == "notok":
        return render_template("failed_login.html",
                               message = "Please go back and try again!",
                               message_2 = "Or you can create a new user right here!")
    else:
        return render_template("error.html", response = response)    
    
@app.route("/new_user", methods = ["POST", "GET"])
def new_user():
    login = request.form.getlist('login')[0]
    password = request.form.getlist('password')[0]
    
    msg = json.dumps({"action" : "new_user", "args" : {"login" : login, "password" : password}})
    
    response = requests.get("http://0.0.0.0:8080", json = msg).json()
    
    if response["status"] == "ok":
        return render_template("main.html")
    elif response["status"] == "notok":
        return render_template("failed_login.html",
                               message = "Such user already exists!",
                               message_2 = "")
    else:
        return render_template("error.html", response = response)    

if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 1234)