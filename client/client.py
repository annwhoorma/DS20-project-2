from flask import Flask, render_template, request
import json
import requests

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/action", methods = ["POST", "GET"])
def action():
    login = request.form.getlist('login')[0]
    password = request.form.getlist('password')[0]
    
    msg = json.dumps({"action":"auth", "args":{"login":login, "password":password}})
    
    response = requests.get("http://0.0.0.0:8080", json=msg).json()
    
    print(response)
    
    
    return "You typed Login: {} and Pass: {}\nResponse: {}".format(login, password, response)

if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 1234)