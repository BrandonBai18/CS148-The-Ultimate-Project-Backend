import os, json
from flask import Flask, request, jsonify, make_response, render_template, redirect, url_for, session
import pymongo
from flask_pymongo import PyMongo
import bcrypt
from flask_mongoengine import MongoEngine
from flask_user import login_required, UserManager, UserMixin
from flask_login import logout_user
from flask_session import Session
from bson import json_util, ObjectId
from bson.objectid import ObjectId
import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint

app_1 = Blueprint('app_1', __name__)
cloud_url = "mongodb+srv://Ab990618:Ab990618@cluster0.ztgu2.mongodb.net/hospital_post?retryWrites=true&w=majority"
Session(app_1)
DEBUG=True
#uri = "mongodb://0.0.0.0:27017"
uri = cloud_url
client = pymongo.MongoClient([uri])
database = client['hospital_post']
collection = database['post_db_1']
collection_comment = database['comment_db_1']
app_1_ROOT = os.path.dirname(os.path.abspath(__file__))
#app_1.config['MONGO_URI'] = 'mongodb://0.0.0.0:27017/user_db_1'
mongo = PyMongo(app_1)
@app_1.route('/login/', methods=['GET','POST'])
def login():

    if request.method == "POST":
        users = mongo.db.users
        login_user = users.find_one({'username' : request.form['username']})

        if login_user:
            if bcrypt.hashpw(request.form['password'].encode('utf-8'), login_user['password']) == login_user['password']:
                session['username'] = request.form['username']
                return redirect('/mainpage')

        return 'Invalid username/password combination'
    
    return render_template('login.html')

@app_1.route('/api/login/', methods=['GET','POST'])
def api_login():

    response_json = request.get_json(force = True)
    users = mongo.db.users
    #login_user = users.find_one({'username' : request.form['username']})
    login_user = users.find_one({'username' : response_json['username']})
    send_json = {}
    if login_user:
        if bcrypt.hashpw(response_json['password'].encode('utf-8'), login_user['password']) == login_user['password']:
            session['username'] = response_json['username']
            send_json['check'] = response_json['username']
            send_json['picture'] = login_user['picture']
            send_to_json = json.loads(json_util.dumps(send_json))
            print("already login -----------")
            return send_to_json
    send_json['check'] = "not login"
    send_to_json = json.loads(json_util.dumps(send_json))
    return send_to_json