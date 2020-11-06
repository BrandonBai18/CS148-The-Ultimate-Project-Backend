# myapp.py
''' 
    This file is based off of this tutorial: https://stackabuse.com/deploying-a-flask-application-to-heroku/ 
    Author: Chandra Krintz, 
    License: UCSB BSD -- see LICENSE file in this repository
'''

import os, json
from flask import Flask, request, jsonify, make_response, render_template, redirect, url_for, session
import pymongo
from flask_pymongo import PyMongo
import bcrypt
from flask_mongoengine import MongoEngine
from flask_user import login_required, UserManager, UserMixin
from flask_login import logout_user

app = Flask(__name__)
DEBUG=True
uri = "mongodb://0.0.0.0:27017"
client = pymongo.MongoClient([uri])
database = client['hospital_post']
collection = database['image_author_posts']
app.config['MONGO_DBNAME'] = 'tst_app'
app.config['MONGO_URI'] = 'mongodb://0.0.0.0:27017/tst_app'
mongo = PyMongo(app)


#use this if linking to a reaact app on the same server
#app = Flask(__name__, static_folder='./build', static_url_path='/')


### CORS section
@app.after_request
def after_request_func(response):
    if DEBUG:
        print("in after_request")
    origin = request.headers.get('Origin')
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Headers', 'x-csrf-token')
        response.headers.add('Access-Control-Allow-Methods',
                            'GET, POST, OPTIONS, PUT, PATCH, DELETE')
        if origin:
            response.headers.add('Access-Control-Allow-Origin', origin)
    else:
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        if origin:
            response.headers.add('Access-Control-Allow-Origin', origin)

    return response
### end CORS section

'''
Note that flask automatically redirects routes without a final slash (/) to one with a final slash (e.g. /getmsg redirects to /getmsg/). Curl does not handle redirects but instead prints the updated url. The browser handles redirects (i.e. takes them). You should always code your routes with both a start/end slash.
'''
@app.route('/api/getmsg/', methods=['GET'])
def respond():
    # Retrieve the msg from url parameter of GET request 
    # and return MESSAGE response (or error or success)
    msg = request.args.get("msg", None)

    if DEBUG:
        print("GET respond() msg: {}".format(msg))

    response = {}
    if not msg: #invalid/missing message
        response["MESSAGE"] = "no msg key found, please send a msg."
        status = 400
    else: #valid message
        response["MESSAGE"] = f"Welcome {msg}!"
        status = 200

    # Return the response in json format with status code
    return jsonify(response), status

@app.route('/api/keys/', methods=['POST']) 
def postit(): 
    '''
    Implement a POST api for key management.
    Note that flask handles request.method == OPTIONS for us automatically -- and calls after_request_func (above)after each request to satisfy CORS
    '''
    response = {}
    #only accept json content type
    if request.headers['content-type'] != 'application/json':
        return jsonify({"MESSAGE": "invalid content-type"}),400
    else:
        try:
            data = json.loads(request.data)
        except ValueError:
            return jsonify({"MESSAGE": "JSON load error"}),405
    acc = data['acckey']
    sec = data['seckey']
    if DEBUG:
        print("POST: acc={}, sec={}".format(acc,sec))
    if acc:
        response["MESSAGE"]= "Welcome! POST args are {} and {}".format(acc,sec)
        status = 200
    else:
        response["MESSAGE"]= "No acckey or seckey keys found, please resend."
        status = 400

    return jsonify(response), status

# Set the base route to be the react index.html
@app.route('/')
def index():
    return redirect('/mainpage')
    """
    if session.get('username') == None:
        return 'no one sign in'
    if 'username' in session:
        return 'You are logged in as ' + session['username']
    return "<h1>Welcome to our server !!</h1>",200
    """

    #use this instead if linking to a raact app on the same server
    #make sure and update the app = Flask(...) line above for the same
    #return app.send_static_file('index.html') 

@app.route('/posts/', methods=['GET','POST'])
def posts():
    if request.method == 'GET':
        posts = collection.find({})
        return render_template('posts.html', post_database = posts)

@app.route('/mainpage/', methods=['GET','POST'])
def mainpage():
    if request.method == 'GET':
        return render_template('mainpage.html', username = session['username'])

@app.route('/write/', methods=['GET','POST'])
def write():
    if request.method == 'GET':
        if not session.get("username") is None:
            return render_template('write.html')
        else:
            return "U need to login first"

    if request.method == 'POST':
        if not session.get("username") is None:
            Title = request.form.get("Title")
            Text = request.form.get("Text")
            Image = request.form.get("Image")

            users = mongo.db.users
            login_user = users.find_one({'username' : session.get("username")})
            login_username = session.get('username')
            new_post = {
                "title": Title,
                "text": Text,
                "image": Image,
                "author": login_username
            }
            collection.insert(new_post)
            return redirect('/posts')
        else:
            return "U need to login first"
    return "U need to login first"




@app.route('/register/', methods=['GET','POST'])
def register():

    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'username' : request.form['username']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
            users.insert({'username' : request.form['username'], 'password' : hashpass})
            session['username'] = request.form['username']
            return redirect('/mainpage')
        
        return 'That username already exists!'

    return render_template('register.html')


@app.route('/login/', methods=['GET','POST'])
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

@app.route("/logout")
def logout():
    if not session.get("username") is None:
        session['username'] = None
    return redirect('/mainpage')

@app.route("/id/<username>")
def other_user_page(username):
    posts = collection.find({"author": username})
    return render_template('other_user_page.html', username = username, post_database =posts)

@app.route("/id_profile/<username>")
def login_user_page(username):
    if not session.get("username") is None:
        users = mongo.db.users
        login_user = users.find_one({'username' : session.get('username')})
        posts = collection.find({"author": login_user['username']})
        return render_template('login_user_page.html', username = login_user['username'], id = login_user['_id'], post_database = posts)


@app.route("/viewmore")
def viewmore():
    return render_template('viewmore.html')


def main():
    '''The threaded option for concurrent accesses, 0.0.0.0 host says listen to all network interfaces (leaving this off changes this to local (same host) only access, port is the port listened on -- this must be open in your firewall or mapped out if within a Docker container. In Heroku, the heroku runtime sets this value via the PORT environment variable (you are not allowed to hard code it) so set it from this variable and give a default value (8118) for when we execute locally.  Python will tell us if the port is in use.  Start by using a value > 8000 as these are likely to be available.
    '''
    app.secret_key = 'hospital'
    localport = int(os.getenv("PORT", 8118))
    app.run(threaded=True, host='0.0.0.0', port=localport)
    #app.run(threaded=True, port=localport)
    
if __name__ == '__main__':
    main()

