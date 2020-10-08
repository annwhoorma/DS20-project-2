from flask import Flask, render_template, request
import json
import requests

ok = "<3"
notok = "</3"

ERROR_DEF = ""

CUR_DIR = "/root"
CUR_USER = "PUTIN"

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods = ["POST", "GET"])
def login():
    global CUR_DIR, CUR_USER
    
    CUR_USER = request.form.getlist('login')[0]
    password = request.form.getlist('password')[0]
    
    msg = json.dumps({"action" : "auth",
                      "args" : {"login" : CUR_USER,
                                "password" : password}})
    
    response = requests.get("http://0.0.0.0:8080", json = msg).json()
    
    if response["status"] == ok:
        free_space = response["args"]["free_space"]
        CUR_DIR = response["args"]["cur_dir"]
        return render_template("main.html",
                               name = CUR_USER,
                               free_space = free_space,
                               cur_dir = CUR_DIR)
    elif response["status"] == notok:
        return render_template("failed_login.html",
                               message = "Please go back and try again!",
                               message_2 = "Or you can create a new user right here!")
    else:
        return render_template("error.html", response = response)    
    
@app.route("/new_user", methods = ["POST", "GET"])
def new_user():
    global CUR_DIR, CUR_USER
    
    CUR_USER = request.form.getlist('login')[0]
    password = request.form.getlist('password')[0]
    
    msg = json.dumps({"action" : "new_user",
                      "args" : {"login" : CUR_USER,
                                "password" : password}})
    
    response = requests.get("http://0.0.0.0:8080", json = msg).json()
    
    if response["status"] == ok:
        free_space = response["args"]["free_space"]
        CUR_DIR = response["args"]["cur_dir"]
        return render_template("main.html", name = CUR_USER,
                               free_space = free_space,
                               cur_dir = CUR_DIR)
    elif response["status"] == notok:
        return render_template("failed_login.html",
                               message = "Such user already exists!",
                               message_2 = "")
    else:
        return render_template("error.html", response = response)   
    
@app.route("/read_dir", methods = ["POST", "GET"])
def read_dir():
    global CUR_DIR, CUR_USER
    
    target_dir = request.form.getlist('target_dir')[0]
    
    msg = json.dumps({"action" : "read_dir",
                      "args" : {"cur_dir" : CUR_DIR,
                                "target_dir" : target_dir}})
    
    response = requests.get("http://0.0.0.0:8080", json = msg).json()
    
    if response["status"] == ok:
        return render_template("main.html", name = CUR_USER,
                               cur_dir = CUR_DIR,
                               read_dir_output = response["args"]["dirs"])
    elif response["status"] == notok:
        return render_template("main.html", name = CUR_USER,
                               cur_dir = CUR_DIR,
                               read_dir_error = response["args"]["error"])
    else:
        return render_template("error.html", response = response)  
    
@app.route("/open_dir", methods = ["POST", "GET"])
def open_dir():
    global CUR_DIR, CUR_USER
    
    target_dir = request.form.getlist('target_dir')[0]
    
    msg = json.dumps({"action" : "open_dir",
                      "args" : {"cur_dir" : CUR_DIR,
                                "target_dir" : target_dir}})
    
    response = requests.get("http://0.0.0.0:8080", json = msg).json()
    
    if response["status"] == ok:
        CUR_DIR = target_dir
        return render_template("main.html", name = CUR_USER,
                               cur_dir = CUR_DIR)
    elif response["status"] == notok:
        return render_template("main.html", name = CUR_USER,
                               cur_dir = CUR_DIR,
                               open_dir_error = response["args"]["error"])
    else:
        return render_template("error.html", response = response)  
    
@app.route("/make_dir", methods = ["POST", "GET"])
def make_dir():
    global CUR_DIR, CUR_USER
    
    new_dir = request.form.getlist('new_dir')[0]
    
    msg = json.dumps({"action" : "make_dir",
                      "args" : {"cur_dir" : CUR_DIR,
                                "new_dir" : new_dir}})
    
    response = requests.get("http://0.0.0.0:8080", json = msg).json()
    
    if response["status"] == ok:
        return render_template("main.html", name = CUR_USER,
                               cur_dir = CUR_DIR)
    elif response["status"] == notok:
        return render_template("main.html", name = CUR_USER,
                               cur_dir = CUR_DIR,
                               make_dir_error = response["args"]["error"])
    else:
        return render_template("error.html", response = response)  
    
@app.route("/del_dir", methods = ["POST", "GET"])
def del_dir():
    global CUR_DIR, CUR_USER
    
    del_dir = request.form.getlist('del_dir')[0]
    
    msg = json.dumps({"action" : "make_dir",
                      "args" : {"cur_dir" : CUR_DIR,
                                "del_dir" : del_dir}})
    
    response = requests.get("http://0.0.0.0:8080", json = msg).json()
    
    if response["status"] == ok:
        return render_template("main.html", name = CUR_USER,
                               cur_dir = CUR_DIR)
    elif response["status"] == notok:
        return render_template("main.html", name = CUR_USER,
                               cur_dir = CUR_DIR,
                               del_dir_error = response["args"]["error"])
    else:
        return render_template("error.html", response = response)  
    
@app.route("/create_file", methods = ["POST", "GET"])
def create_file():
    global CUR_DIR, CUR_USER
    
    filename = request.form.getlist('filename')[0]
    
    msg = json.dumps({"action" : "create_file",
                      "args" : {"cur_dir" : CUR_DIR,
                                "filename" : filename}})
    
    response = requests.get("http://0.0.0.0:8080", json = msg).json()
    
    if response["status"] == ok:
        return render_template("main.html", name = CUR_USER,
                               cur_dir = CUR_DIR)
    elif response["status"] == notok:
        return render_template("main.html", name = CUR_USER,
                               cur_dir = CUR_DIR,
                               create_file_error = response["args"]["error"])
    else:
        return render_template("error.html", response = response)  
    
@app.route("/delete_file", methods = ["POST", "GET"])
def delete_file():
    global CUR_DIR, CUR_USER
    
    filename = request.form.getlist('filename')[0]
    
    msg = json.dumps({"action" : "delete_file",
                      "args" : {"cur_dir" : CUR_DIR,
                                "filename" : filename}})
    
    response = requests.get("http://0.0.0.0:8080", json = msg).json()
    
    if response["status"] == ok:
        return render_template("main.html", name = CUR_USER,
                               cur_dir = CUR_DIR)
    elif response["status"] == notok:
        return render_template("main.html", name = CUR_USER,
                               cur_dir = CUR_DIR,
                               delete_file_error = response["args"]["error"])
    else:
        return render_template("error.html", response = response)  
    
@app.route("/info_file", methods = ["POST", "GET"])
def info_file():
    global CUR_DIR, CUR_USER
    
    filename = request.form.getlist('filename')[0]
    
    msg = json.dumps({"action" : "info_file",
                      "args" : {"cur_dir" : CUR_DIR,
                                "filename" : filename}})
    
    response = requests.get("http://0.0.0.0:8080", json = msg).json()
    
    if response["status"] == ok:
        return render_template("main.html", name = CUR_USER,
                               cur_dir = CUR_DIR,
                               info_file_output = response["args"])
    elif response["status"] == notok:
        return render_template("main.html", name = CUR_USER,
                               cur_dir = CUR_DIR,
                               info_file_error = response["args"]["error"])
    else:
        return render_template("error.html", response = response)  
    
@app.route("/copy_file", methods = ["POST", "GET"])
def copy_file():
    global CUR_DIR, CUR_USER
    
    filename = request.form.getlist('filename')[0]
    dest_dir = request.form.getlist('dest_dir')[0]
    
    msg = json.dumps({"action" : "copy_file",
                      "args" : {"cur_dir" : CUR_DIR,
                                "filename" : filename,
                                "dest_dir" : dest_dir}})
    
    response = requests.get("http://0.0.0.0:8080", json = msg).json()
    
    if response["status"] == ok:
        return render_template("main.html", name = CUR_USER,
                               cur_dir = CUR_DIR)
    elif response["status"] == notok:
        return render_template("main.html", name = CUR_USER,
                               cur_dir = CUR_DIR,
                               copy_file_error = response["args"]["error"])
    else:
        return render_template("error.html", response = response)  
    
@app.route("/move_file", methods = ["POST", "GET"])
def move_file():
    global CUR_DIR, CUR_USER
    
    filename = request.form.getlist('filename')[0]
    dest_dir = request.form.getlist('dest_dir')[0]
    
    msg = json.dumps({"action" : "move_file",
                      "args" : {"cur_dir" : CUR_DIR,
                                "filename" : filename,
                                "dest_dir" : dest_dir}})
    
    response = requests.get("http://0.0.0.0:8080", json = msg).json()
    
    if response["status"] == ok:
        return render_template("main.html", name = CUR_USER,
                               cur_dir = CUR_DIR)
    elif response["status"] == notok:
        return render_template("main.html", name = CUR_USER,
                               cur_dir = CUR_DIR,
                               copy_file_error = response["args"]["error"])
    else:
        return render_template("error.html", response = response)  
    
if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 1234)