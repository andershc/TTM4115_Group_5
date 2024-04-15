from flask import Flask, request, jsonify
from flask_cors import CORS
import paho.mqtt.client as mqtt

import json

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

CHARGERS_DB_PATH = "server/db/chargers.json"
USERS_DB_PATH = "server/db/users.json"

app = Flask(__name__)
CORS(app)


@app.route("/login", methods=["POST"])
def login():
    email = request.json.get("email")
    password = request.json.get("password")
    foundUser = None

    # Get user from database
    with open(USERS_DB_PATH, "r") as f:
        data = json.load(f)
        for user in data["users"]:
            if user["email"] == email:
                foundUser = user

    # Check if user exists and password is correct
    if foundUser and foundUser["password"] == password:
        return jsonify(user)
    else:
        return jsonify({"error": "Invalid email or password"}), 401


@app.route("/register", methods=["POST"])
def register():
    email = request.json.get("email")
    password = request.json.get("password")
    name = request.json.get("name")
    foundUser = None

    # Get user from database
    with open(USERS_DB_PATH, "r") as f:
        data = json.load(f)
        for user in data["users"]:
            if user["email"] == email:
                foundUser = user

    # Check if user exists
    if foundUser:
        return jsonify({"error": "User already exists"}), 400
    else:
        newUser = {"email": email, "password": password, "name": name}
        data["users"].append(newUser)

        with open(USERS_DB_PATH, "w") as f:
            json.dump(data, f, indent=4)

        return jsonify(newUser)


@app.route("/chargers", methods=["GET"])
def getChargers():
    with open(CHARGERS_DB_PATH, "r") as f:
        chargers = json.load(f)
    return jsonify(chargers)


@app.route("/charger", methods=["GET"])
def getCharger():
    id = request.args.get("id")
    with open(CHARGERS_DB_PATH, "r") as f:
        chargers = json.load(f)
    for charger in chargers["chargers"]:
        if type(id) == str:
            id = int(id)
        if charger["id"] == id:
            return jsonify(charger)
    return jsonify({"error": "Charger not found"}), 404
