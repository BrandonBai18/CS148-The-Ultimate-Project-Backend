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
from flask_session import Session
from bson import json_util, ObjectId
from bson.objectid import ObjectId
import datetime
from werkzeug.utils import secure_filename
#flask-session-0.3.2
cloud_url = "mongodb+srv://Ab990618:Ab990618@cluster0.ztgu2.mongodb.net/hospital_post?retryWrites=true&w=majority"
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'hospital'
Session(app)
DEBUG=True
#uri = "mongodb://0.0.0.0:27017"
uri = cloud_url
client = pymongo.MongoClient([uri])
database = client['hospital_post']
collection = database['post_db_1']
collection_comment = database['comment_db_1']
app.config['MONGO_DBNAME'] = 'user_db_1'
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
#app.config['MONGO_URI'] = 'mongodb://0.0.0.0:27017/user_db_1'
app.config['MONGO_URI'] = 'mongodb+srv://Ab990618:Ab990618@cluster0.ztgu2.mongodb.net/user_db_1?retryWrites=true&w=majority'
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



@app.route('/mainpage/', methods=['GET','POST'])
def mainpage():
    if request.method == 'GET':
        return render_template('mainpage.html', username = session.get('username'))

@app.route('/posts/', methods=['GET','POST'])
def posts():
    if request.method == 'GET':
        posts = collection.find({})
        return render_template('posts.html', post_database = posts)


@app.route('/api/posts', methods = ['GET','POST'])
def api_posts():
    if request.method == 'GET':
        posts = collection.find({})
        response = {}
        #for post in posts:
        #    new_num = "post_" + str(num)
        #    response[new_num] = post
        #    num = num + 1
        response["posts"] = posts
        response_json = json.loads(json_util.dumps(response))
        return response_json

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
            time_now = datetime.datetime.now()
            date_time = time_now.strftime("%m/%d/%Y")
            print(time_now)
            users = mongo.db.users
            login_user = users.find_one({'username' : session.get("username")})
            login_username = session.get('username')
            new_post = {
                "title": Title,
                "text": Text,
                "image": Image,
                "author": login_username,
                "time": date_time,
                "comment_list": []
            }
            collection.insert(new_post)
            return redirect('/posts')
        else:
            return "U need to login first"
    return "U need to login first"

@app.route('/api/write/', methods=['GET','POST'])
def api_write():
    #if not session.get("username") is None:
    response_json = request.get_json(force = True)
    
    Title = response_json['title']
    Text = response_json['text']
    Image = response_json['image']
    login_username = response_json['author']

    time_now = datetime.datetime.now()
    date_time = time_now.strftime("%m/%d/%Y")
    #login_username = session.get('username')
    new_post = {
        "title": Title,
        "text": Text,
        "image": Image,
        "author": login_username,
        "time": date_time,
        "comment_list": []
    }
    collection.insert(new_post)
    send_json = {}
    
    send_json['check'] = 'True'
    send_to_json = json.loads(json_util.dumps(send_json))
    return send_to_json

@app.route('/register/', methods=['GET','POST'])
def register():

    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'username' : request.form['username']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
            users.insert({
                'username' : request.form['username'],
                'password' : hashpass,
                'picture': "https://cdn5.vectorstock.com/i/thumb-large/82/59/anonymous-user-flat-icon-vector-18958259.jpg",
                'gender': None,
                'birthday': None,
                'rela_sta': None,
                'location': None,
                'hometown': None,
                'school': None,
                'company': None
                })
            session['username'] = request.form['username']
            return redirect('/mainpage')
        
        return 'That username already exists!'

    return render_template('register.html')

    """
    个人简介
    性别
    生日
    星座
    感情状况
    情绪爱好: 电影 音乐 图书
    所在地
    家乡
    学校
    公司
    昵称:
    """
@app.route('/api/register/', methods=['GET','POST'])
def api_register():
    if request.method == 'POST':
        users = mongo.db.users
        response_json = request.get_json(force = True)
        username = response_json['username']
        password = response_json['password']
        existing_user = users.find_one({'username' : username})
        send_json = {}
        if existing_user is None:
            hashpass = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            users.insert({
                'username' : username, 
                'password' : hashpass,
                'picture': "https://cdn5.vectorstock.com/i/thumb-large/82/59/anonymous-user-flat-icon-vector-18958259.jpg",
                'gender': None,
                'birthday': None,
                'rela_sta': None,
                'location': None,
                'hometown': None,
                'school': None,
                'company': None
            })
            session['username'] = username
            send_json['check'] = username
            send_json['picture'] = "https://cdn5.vectorstock.com/i/thumb-large/82/59/anonymous-user-flat-icon-vector-18958259.jpg"
            send_to_json = json.loads(json_util.dumps(send_json))
            return send_to_json
        
        send_json['check'] = None
        send_to_json = json.loads(json_util.dumps(send_json))
        return send_to_json
    


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

@app.route('/api/login/', methods=['GET','POST'])
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
    


@app.route("/logout")
def logout():
    if not session.get("username") is None:
        session['username'] = None
    return redirect('/mainpage')


@app.route("/api/logout")
def api_logout():
    session['username'] = None

@app.route("/api/check_status")
def api_check_status():
    send_json = {}
    if not session.get("username") is None:
        send_json['check'] = session.get("username")
        send_to_json = json.loads(json_util.dumps(send_json))
        print("already login -----------")
        return send_to_json
    else: 
        send_json['check'] = None
        send_to_json = json.loads(json_util.dumps(send_json))
        print("not login -----------")
        return send_to_json

@app.route("/id/<username>")
def other_user_page(username):
    posts = collection.find({"author": username})
    users = mongo.db.users
    user = users.find_one({'username' : username})
    return render_template('other_user_page.html', username = username, post_database = posts, user = user)

@app.route("/api/id/<username>")
def api_other_user_page(username):
    posts = collection.find({"author": username})
    response = {}
    #for post in posts:
    #    new_num = "post_" + str(num)
    #    response[new_num] = post
    #    num = num + 1
    response["posts"] = posts
    page_sanitized = json.loads(json_util.dumps(response))
    return page_sanitized
    
@app.route("/id_profile/<username>")
def login_user_page(username):
    if not session.get("username") is None:
        users = mongo.db.users
        login_user = users.find_one({'username' : session.get('username')})
        posts = collection.find({"author": login_user['username']})
        return render_template('login_user_page.html', user = login_user, post = posts)
        

@app.route("/api/id_profile/<username>")
def api_login_user_page(username):
    #if not session.get("username") is None:
    users = mongo.db.users
    #login_user = users.find_one({'username' : session.get('username')})
    login_user = users.find_one({'username' : username})
    posts = collection.find({"author": login_user['username']})
    response = {}
    response["posts"] = posts
    response["profile"] = login_user
    page_sanitized = json.loads(json_util.dumps(response))
    return page_sanitized

@app.route("/personalize/<username>", methods = ['GET', 'POST'])
def personalize(username):
    if request.method == "GET":
        users = mongo.db.users
        login_user = users.find_one({'username' : username})
        return render_template('personalize.html', user = login_user)
    """
    if request.method == "POST":
        users = mongo.db.users
        login_user = users.find_one({'username' : username})
        login_user.update_one()
    """


@app.route("/personalize/<username>/<element>",methods = ['GET', 'POST'])
def personalize_element(username,element):
        users = mongo.db.users
        login_user = users.find_one({'username' : username})
        if element == 'gender':
            if request.method == 'GET':
                return render_template('gender.html', user = login_user)
            if request.method == 'POST':
                users.update_one({"username": username},{"$set": {"gender": request.form.get("gender")}})
                next_page = "/personalize/" + username
                return redirect(next_page)

        
        if element == 'birthday':
            if request.method == 'GET':
                return render_template('birthday.html', user = login_user)
            if request.method == 'POST':
                users.update_one({"username": username},{"$set": {"birthday": request.form.get("birthday")}})
                next_page = "/personalize/" + username
                return redirect(next_page)

        if element == 'rela_sta':
            if request.method == 'GET':
                return render_template('rela_sta.html', user = login_user)
            if request.method == 'POST':
                users.update_one({"username": username},{"$set": {"rela_sta": request.form.get("rela_sta")}})
                next_page = "/personalize/" + username
                return redirect(next_page)

        if element == 'location':
            if request.method == 'GET':
                return render_template('location.html', user = login_user)
            if request.method == 'POST':
                users.update_one({"username": username},{"$set": {"location": request.form.get("location")}})
                next_page = "/personalize/" + username
                return redirect(next_page)

        if element == 'hometown':
            if request.method == 'GET':
                return render_template('hometown.html', user = login_user)
            if request.method == 'POST':
                users.update_one({"username": username},{"$set": {"hometown": request.form.get("hometown")}})
                next_page = "/personalize/" + username
                return redirect(next_page)

        if element == 'school':
            if request.method == 'GET':
                return render_template('school.html', user = login_user)
            if request.method == 'POST':
                users.update_one({"username": username},{"$set": {"school": request.form.get("school")}})
                next_page = "/personalize/" + username
                return redirect(next_page)

        if element == 'company':
            if request.method == 'GET':
                return render_template('company.html', user = login_user)
            if request.method == 'POST':
                users.update_one({"username": username},{"$set": {"company": request.form.get("company")}})
                next_page = "/personalize/" + username
                return redirect(next_page)

        if element == 'picture':
            if request.method == 'GET':
                return render_template('picture.html', user = login_user)
            if request.method == 'POST':
                """
                target = os.path.join(APP_ROOT, 'user_profile_images/')  #folder path
                if not os.path.isdir(target):
                    os.mkdir(target)     # create folder if not exits
                #user_picture_collection = database.mongo.db.user_pictures  # database table name
                for upload in request.files.getlist("picture"): #multiple image handel
                    filename = secure_filename(upload.filename)
                    destination = "/".join([target, filename])
                    upload.save(destination)
                    #user_picture_collection.insert({'picture': filename})   #insert into database mongo db
                    users.update_one({"username": username},{"$set": {"picture": filename}})
                next_page = "/personalize/" + username
                return redirect(next_page)
                """
                users.update_one({"username": username},{"$set": {"picture": request.form.get("picture")}})
                next_page = "/personalize/" + username
                return redirect(next_page)

    
    

@app.route("/viewmore/<post_id>", methods = ["POST", "GET"])
def viewmore(post_id):
    if request.method == "GET":
        post = collection.find_one({"_id": ObjectId(str(post_id))})
        comment_list = post['comment_list']


        return render_template('viewmore.html', post = post, comment_list = comment_list, _id = ObjectId(str(post_id)))
    else:
        if session.get("username") == None:
            return "U need to sign in first"
        else:
            comment = request.form.get("comment")
            username = session.get('username')
            just_inserted_id = collection_comment.insert_one({"content": comment, "username": username}).inserted_id

            post = collection.find_one({"_id": ObjectId(str(post_id))})
            comment_list = post['comment_list']
            comment_list.append({'_id':ObjectId(str(just_inserted_id)),'content': comment, 'username': username})

            collection.update_one({"_id": ObjectId(str(post_id))},{"$set": {"comment_list": comment_list}})
            next_page = "/viewmore/" + str(post_id)
            return redirect(next_page)

            

        





@app.route("/api/viewmore/<post_id>")
def api_viewmore(post_id):
    post = collection.find_one({"_id": ObjectId(str(post_id))})
    #print(post.title)
    response = {}

    response["post"] = post
    response_json = json.loads(json_util.dumps(response))
    return response_json




@app.route("/hospital/<element>", methods = ["GET", "POST"])
def hospital(element):
    if request.method == "GET":
        return render_template('hospital.html')
    else:
        with open('Hospitals.json', 'r') as file_1:
            data=file_1.read()
        hos_info = json.loads(data)

        if element == 'zip_code':
            for hospital in hos_info['features']:
                if hospital['properties']['ZIP'] == request.form.get('zip_code'):
                    return hospital['properties']['NAME'].lower()
            return "zip code not found"

        if element == 'name':
            a = ""
            return_hospitals = []
            search_name = request.form.get('name')
            for hospital in hos_info['features']:
                if search_name.lower() in hospital['properties']['NAME'].lower():
                    return_hospitals.append(hospital['properties']['NAME'].lower())
                    #print("".join(hospital['properties']['NAME']))
            
            if len(return_hospitals) == 0:
                return "name not found"
            else:
                return render_template('hospital_name.html', hospitals = return_hospitals)


        

        #return str(hos_info['features'][0]['properties']['NAME'])





def main():
    '''The threaded option for concurrent accesses, 0.0.0.0 host says listen to all network interfaces (leaving this off changes this to local (same host) only access, port is the port listened on -- this must be open in your firewall or mapped out if within a Docker container. In Heroku, the heroku runtime sets this value via the PORT environment variable (you are not allowed to hard code it) so set it from this variable and give a default value (8118) for when we execute locally.  Python will tell us if the port is in use.  Start by using a value > 8000 as these are likely to be available.
    '''
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SECRET_KEY'] = 'hospital'
    app.secret_key = 'hospital'
    #Session(app)

    localport = int(os.getenv("PORT", 8118))
    app.run(threaded=True, host='0.0.0.0', port=localport)
    #app.run(threaded=True, port=localport)

if __name__ == '__main__':
    main()

 
