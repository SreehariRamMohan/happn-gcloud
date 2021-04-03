
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
#  from flask_pymongo import PyMongo, ObjectId

import requests
import os

PORT = "5000"
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# MongoDB
#  connectionString = "mongodb+srv://hackPrinceton:" + str(os.environ.get("HAPPEN_MONGO_PASSWORD")) + "@cluster0.gor2j.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
#  app.config["MONGO_URI"] = connectionString
#  mongo = PyMongo(app)
#  db = mongo.db

@app.route("/accountSignup", methods=["POST"])
@cross_origin()
def signup(): 
    data = request.json["messag"]
    return jsonify({"returnedMessage": data}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

