import sqlite3
import constants
from flask import Flask

app = Flask(__name__)

@app.route("/me")
def me():
    return "me"

@app.route("/login")
def login():
    return "login"

@app.route("/logout")
def logout():
    return "logout"

@app.route("/register")
def register():
    return "register"

@app.route("/chart")
def chart():
    return "chart"

@app.route("/future_value")
def future_value():
    return "future_value"

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"
