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
from flask_simple_geoip import SimpleGeoIP
from flask_socketio import SocketIO,emit




#flask-session-0.3.2
cloud_url = "mongodb+srv://Ab990618:Ab990618@cluster0.ztgu2.mongodb.net/hospital_post?retryWrites=true&w=majority"
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'hospital'
socketio = SocketIO(app)
#Session(app)
DEBUG=True
#uri = "mongodb://0.0.0.0:27017"
uri = cloud_url
client = pymongo.MongoClient([uri])
database_post = client['posts']
database_hospital = client['hospital_api']
database_surgery = client['surgery']
collection_surgery = database_surgery["surgeries"]
collection_surgery_comment = database_surgery["comments"]
collection_post = database_post['posts']
collection_post_comment = database_post['comments']
collection_post_reply = database_post['replys']
collection_hospital = database_hospital['hospital_db_1']
collection_hospital_comment = database_hospital['hospital_comment_db_1']
app.config['MONGO_DBNAME'] = 'user_db_1'
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
#app.config['MONGO_URI'] = 'mongodb://0.0.0.0:27017/user_db_1'
app.config['MONGO_URI'] = 'mongodb+srv://Ab990618:Ab990618@cluster0.ztgu2.mongodb.net/user_db_1?retryWrites=true&w=majority'
mongo = PyMongo(app)
app.config.update(GEOIPIFY_API_KEY='at_8XlbpnW37c6IHAEYEn94MjBY1Oe8D')
simple_geoip = SimpleGeoIP(app)

#socketio.init_app(app)


#use this if linking to a reaact app on the same server
#app = Flask(__name__, static_folder='./build', static_url_path='/')

def Reverse(lst): 
    return [ele for ele in reversed(lst)] 

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
        users = mongo.db.users
        login_user = users.find_one({'username' : session.get('username')})
        if not session.get("username") is None:
            notification = login_user["notification"]
            return render_template('mainpage.html', username = session.get('username'), notification = notification)
        else:
            return render_template('mainpage.html', username = session.get('username'))

@app.route('/posts/', methods=['GET','POST'])
def posts():
    if request.method == 'GET':
        posts = collection_post.find({})
        return render_template('posts.html', post_database = posts)

@app.route('/api/find_post/<post_id>', methods = ['GET'])
def api_find_post_id(post_id):
    post = collection_post.find_one({"_id": ObjectId(str(post_id))})
    comment_list_id = post["comment_list"]

    comment_list_id_2 = []
    for item in comment_list_id:
        comment_list_id_2.append(str(item))
    #comment_list_id = sorted(comment_list_id_2, key=lambda x: x[1] , reverse=True)
    comment_list_id = Reverse(comment_list_id)

    comment_list_content = []
    for comment in comment_list_id:
        comment_content = collection_post_comment.find_one({"_id": ObjectId(str(comment))})
        #reply_list_id = sorted(comment_content["reply_list"]["_id"] , key=lambda x: x[1])
        
        reply_list = comment_content["reply_list"]
        reply_list_2 = []
        for item in reply_list:
            reply_list_2.append(str(item))
        #reply_list_id = sorted(reply_list_2, key=lambda x: x[1] , reverse=True)
        reply_list_id = Reverse(reply_list_2)
     
        reply_list_content = []
        for reply in reply_list_id:
            reply_content = collection_post_reply.find_one({"_id": ObjectId(str(reply))})
            reply_list_content.append(reply_content)
        
        comment_list_content.append({
            "content":comment_content,
            "reply": reply_list_content
        })

    like_list = post['like_list']
    visual_like_list = []
    users = mongo.db.users
    for user_id in like_list:
        user = users.find_one({'_id' : ObjectId(str(user_id)) })
        username = user['username']
        visual_like_list.append(username)
    
    like_number = post["like_number"]
    
    send_json = {
        "post": post,
        "comment": comment_list_content,
        "like_list": visual_like_list,
        "like_number": like_number
    }
    send_to_json = json.loads(json_util.dumps(send_json))
    return send_to_json

@app.route('/api/find_comment/<comment_id>', methods = ['GET'])
def api_find_comment_id(comment_id):
    comment = collection_post_comment.find_one({"_id": ObjectId(str(comment_id))})
    reply_list_id = comment["reply_list"]
    reply_list_content = []
    for reply in reply_list_id:
        reply_content = collection_post_reply.find_one({"_id": ObjectId(str(reply))})
        reply_list_content.append(reply_content)
    send_json = {
        "comment": comment,
        "reply": reply_list_content
    }
    send_to_json = json.loads(json_util.dumps(send_json))
    return send_to_json
    
    

@app.route('/api/posts', methods = ['GET','POST'])
def api_posts():
    if request.method == 'GET':
        posts = collection_post.find({}).sort("_id", -1)
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
            collection_post.insert(new_post)
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
    hospitals = response_json['hospital']
    surgerys = response_json['surgery']

    time_now = datetime.datetime.now()
    date_time = time_now.strftime("%m/%d/%Y")
    #login_username = session.get('username')
    new_post = {
        "title": Title,
        "text": Text,
        "image": Image,
        "author": login_username,
        "time": date_time,
        "comment_list": [],
        "like_list": []
    }
    post_id = collection_post.insert_one(new_post).inserted_id
    send_json = {}
    
    send_json['check'] = 'True'
    send_to_json = json.loads(json_util.dumps(send_json))


    for hospital in hospitals:
        hospital_id = collection_hospital.find_one({"name": hospital.upper()})
        new_list = hospital_id["post_list"]
        new_list.append(post_id)
        collection_hospital.update_one({"name": hospital},{"$set": {"post_list": new_list}})

    for surgery in surgerys:
        surgery_id = collection_surgery.find_one({"name": surgery})
        new_list = surgery_id["list"]
        new_list.append(post_id)
        collection_surgery.update_one({"name": surgery},{"$set": {"list": new_list}})
    

    return send_to_json

@app.route('/api/all_hospitals')
def all_hospitals():
    all_hospitals = []
    for hospital in collection_hospital.find():
        all_hospitals.append(hospital['name'])
    send_json = {
        "hospitals": all_hospitals
    }
    send_to_json = json.loads(json_util.dumps(send_json))
    return send_to_json

@app.route('/api/all_surgerys')
def all_surgerys():
    all_surgerys = []
    for surgery in collection_surgery.find():
        all_surgerys.append(surgery['name'])
    send_json = {
        "surgerys": all_surgerys
    }
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
                'company': None,
                'follower': {
                    'number': 0,
                    'list': []
                },
                'following': {
                    'number': 0,
                    'list': []
                },
                'notification': {
                    "number": 0,
                    "list": []
                }
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
                'company': None,
                'follower': {
                    'number': 0,
                    'list': []
                },
                'following': {
                    'number': 0,
                    'list': []
                },
                'notification': {
                    "number": 0,
                    "list": []
                }

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

    if session.get("username") is None:
        return render_template('other_user_page.html', username = username, post_database = posts, user = user, check_follow = 0)
    if username == session.get("username"):
        return redirect("/id_profile/"+username)

    posts = collection_post.find({"author": username})
    users = mongo.db.users
    user = users.find_one({'username' : username})
    login_user = users.find_one({'username' : session.get("username")})
    check_follow = 0


    if not (username in login_user["following"]["list"]) and not (username in login_user["follower"]["list"]) :
        check_follow = 0
    elif (username in login_user["following"]["list"]) and not (username in login_user["follower"]["list"]) :
        check_follow = 1
    elif (username in login_user["following"]["list"]) and (username in login_user["follower"]["list"]) :
        check_follow = 2
    elif not (username in login_user["following"]["list"]) and (username in login_user["follower"]["list"]) :
        check_follow = 3
    return render_template('other_user_page.html', username = username, post_database = posts, user = user, check_follow = check_follow)

@app.route("/api/id/<username>")
def api_other_user_page(username):
    posts = collection_post.find({"author": username})
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
        posts = collection_post.find({"author": login_user['username']})
        return render_template('login_user_page.html', user = login_user, post = posts)
        

@app.route("/api/id_profile/<username>")
def api_login_user_page(username):
    #if not session.get("username") is None:
    users = mongo.db.users
    #login_user = users.find_one({'username' : session.get('username')})
    login_user = users.find_one({'username' : username})
    posts = collection_post.find({"author": login_user['username']})
    response = {}
    response["posts"] = posts
    response["profile"] = login_user
    page_sanitized = json.loads(json_util.dumps(response))
    return page_sanitized

@app.route("/follow/<follow_username>")
def follow_user(follow_username):
    if not session.get("username") is None:
        users = mongo.db.users
        login_user = users.find_one({'username' : session.get('username')})
        follow_user = users.find_one({'username' : follow_username})
        login_user_following = login_user['following']
        follow_user_follower = follow_user['follower']

        if session.get("username") in follow_user_follower['list']:
            return "u already followed him"

        login_user_following['number'] += 1
        login_user_following['list'].append(follow_user["username"])
        follow_user_follower['number'] += 1
        follow_user_follower['list'].append(login_user['username'])
        users.update_one({"username": follow_user["username"]},{"$set":{"follower": follow_user_follower}})
        users.update_one({"username": login_user['username']},{"$set":{"following": login_user_following}})

        new_notification = {
                "number": 0,
                "list": []
            }
        post_author_notification = follow_user['notification']
        new_notification["number"] = post_author_notification["number"] + 1
        new_notification["list"] = post_author_notification["list"]
        new_notification["list"].append({
                "comment_id": 0,
                "type": "follow",
                "content": 0,
                "username": session.get("username"), 
                "reply_name": 0
            })
        users.update_one({"username": follow_username},{"$set": {"notification": new_notification}})



        url = "/id/" + follow_username
        return redirect(url)
    else:
        return "u need to login first"

@app.route("/unfollow/<follow_username>")
def unfollow_user(follow_username):
    if not session.get("username") is None:
        users = mongo.db.users
        login_user = users.find_one({'username' : session.get('username')})
        follow_user = users.find_one({'username' : follow_username})
        login_user_following = login_user['following']
        follow_user_follower = follow_user['follower']
        login_user_following['number'] += -1
        login_user_following['list'].remove(follow_user["username"])
        follow_user_follower['number'] += -1
        follow_user_follower['list'].remove(login_user['username'])
        users.update_one({"username": follow_user["username"]},{"$set":{"follower": follow_user_follower}})
        users.update_one({"username": login_user['username']},{"$set":{"following": login_user_following}})
        url = "/id/" + follow_username
        return redirect(url)
    else:
        return "u need to login first"

@app.route("/search_user", methods = ["GET", "POST"])
def search_user():
    search_name = request.form.get("username")
    users = mongo.db.users
    user_result = []
    for user in users.find():
        if search_name.lower() in user["username"].lower():
            user_result.append(user["username"])
    print(user_result)
    if len(user_result) == 0:
        return "cannot find the user"
    else:
        return render_template("search_user_result.html", users = user_result)

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

@app.route("/api/personalize/",methods = ['POST'])
def api_personalize():
    users = mongo.db.users
    response_json = request.get_json(force = True)
    username = response_json["username"]
    picture = response_json['picture']
    gender = response_json['gender']
    birthday = response_json['birthday']
    rela_sta = response_json['rela_sta']
    location = response_json['location']
    hometown = response_json['hometown']
    school = response_json['school']
    company = response_json['company']
    users.update_one({"username": username},{"$set": {"picture":picture}})
    users.update_one({"username": username},{"$set": {"gender":gender}})
    users.update_one({"username": username},{"$set": {"birthday":birthday}})
    users.update_one({"username": username},{"$set": {"rela_sta":rela_sta}})
    users.update_one({"username": username},{"$set": {"location":location}})
    users.update_one({"username": username},{"$set": {"hometown":hometown}})
    users.update_one({"username": username},{"$set": {"school":school}})
    users.update_one({"username": username},{"$set": {"company":company}})
    return_json = {
        "check": "True"
    }
    return_json = json.loads(json_util.dumps(return_json))
    return return_json
    



    
    

@app.route("/viewmore/<post_id>", methods = ["POST", "GET"])
def viewmore(post_id):
    if request.method == "GET":
        post = collection_post.find_one({"_id": ObjectId(str(post_id))})
        comment_list = post['comment_list']
        visual_comment = []
        for comment in comment_list:
            each_comment = collection_post_comment.find_one({"_id": ObjectId(str(comment))})
            visual_comment.append({
                "content": each_comment['content'],
                "username": each_comment["username"],
                "num_of_reply": len(each_comment["reply_list"]),
                "comment_id": ObjectId(str(comment))
            })

        return render_template('viewmore.html', post = post, comment_list = visual_comment, _id = ObjectId(str(post_id)))
    
@app.route("/viewmore/<post_id>/<reply_name>/<comment_id>", methods = ["POST"])
def viewmore_reply(post_id, reply_name, comment_id):
    if session.get("username") == None:
        return "U need to sign in first"

    if reply_name != "no_reply":
        comment = request.form.get("comment")
        username = session.get('username')
        reply_id = collection_post_reply.insert_one({"content": comment, "username": username, "reply_name": reply_name, "like_list": []}).inserted_id
        reply_comment = collection_post_comment.find_one({"_id": ObjectId(str(comment_id))})
        new_list = []
        new_list = reply_comment["reply_list"]
        new_list.append(reply_id)
        collection_post_comment.update_one({"_id": ObjectId(str(comment_id))}, {"$set": {"reply_list": new_list}})
        #comment_list.append({'_id':ObjectId(str(just_inserted_id)),'content': comment, 'username': username, 'reply_name': reply_name})

        if (session.get("username") != reply_name ):
            post_author_username = reply_name
            users = mongo.db.users
            post_author = users.find_one({"username": post_author_username})
            post_author_notification = post_author['notification']
            new_notification = {
                "number": 0,
                "list": []
            }

            new_notification["number"] = post_author_notification["number"] + 1
            new_notification["list"] = post_author_notification["list"]
            #new_notification["list"].append(post_id)
            new_notification["list"].append({
                "comment_id": comment_id,
                "type": "reply",
                "content": comment,
                "username": username, 
                "reply_name": reply_name
            })
            users.update_one({"username": post_author_username},{"$set": {"notification": new_notification}})

        next_page = "/viewmore/" + str(post_id)
        return redirect(next_page)
        
    else:

        comment = request.form.get("comment")
        username = session.get('username')
        comment_id = collection_post_comment.insert_one({"content": comment, "username": username, "reply_list": [], "list_list": []}).inserted_id

        post = collection_post.find_one({"_id": ObjectId(str(post_id))})
        comment_list = post['comment_list']
        comment_list.append(comment_id)

        if (session.get("username") != post["author"] ):
            post_author_username = post["author"]
            users = mongo.db.users
            post_author = users.find_one({"username": post_author_username})
            post_author_notification = post_author['notification']
            new_notification = {
                "number": 0,
                "list": []
            }
            new_notification["number"] = post_author_notification["number"] + 1
            new_notification["list"] = post_author_notification["list"]
            new_notification["list"].append({
                "post_id": post_id,
                "type": "comment",
                "content": comment,
                "username": username, 
                "reply_name": None
            })
            users.update_one({"username": post_author_username},{"$set": {"notification": new_notification}})

        collection_post.update_one({"_id": ObjectId(str(post_id))},{"$set": {"comment_list": comment_list}})

        next_page = "/viewmore/" + str(post_id)
        return redirect(next_page)

            
@app.route("/reply_to_comment/<comment_id>/<reply_name>", methods = ["GET", "POST"])
def reply_to_comment(comment_id, reply_name):
    if request.method == "GET":
        comment = collection_post_comment.find_one({"_id": ObjectId(str(comment_id)) })
        reply_list = comment["reply_list"]
        visual_reply_list = []
        for reply in reply_list:
            each_reply = collection_post_reply.find_one({"_id": ObjectId(str(reply)) })
            visual_reply_list.append({
                "username": each_reply["username"],
                "reply_name": each_reply["reply_name"],
                "content": each_reply["content"]
            })
        return render_template("reply_to_comment.html", reply_list = visual_reply_list, comment_id = comment_id)
    else:
        comment = request.form.get("reply")
        username = session.get('username')
        reply_id = collection_post_reply.insert_one({"content": comment, "username": username, "reply_name": reply_name, "like_list": []}).inserted_id
        reply_comment = collection_post_comment.find_one({"_id": ObjectId(str(comment_id))})
        new_list = []
        new_list = reply_comment["reply_list"]
        new_list.append(reply_id)
        collection_post_comment.update_one({"_id": ObjectId(str(comment_id))}, {"$set": {"reply_list": new_list}})
        #comment_list.append({'_id':ObjectId(str(just_inserted_id)),'content': comment, 'username': username, 'reply_name': reply_name})

        if (session.get("username") != reply_name ):
            post_author_username = reply_name
            users = mongo.db.users
            post_author = users.find_one({"username": post_author_username})
            post_author_notification = post_author['notification']
            new_notification = {
                "number": 0,
                "list": []
            }

            new_notification["number"] = post_author_notification["number"] + 1
            new_notification["list"] = post_author_notification["list"]
            #new_notification["list"].append(post_id)
            new_notification["list"].append({
                "comment_id": comment_id,
                "type": "reply",
                "content": comment,
                "username": username, 
                "reply_name": reply_name
            })
            users.update_one({"username": post_author_username},{"$set": {"notification": new_notification}})

        next_page = "/reply_to_comment/" + comment_id + "/" + reply_name
        return redirect(next_page)
        
@app.route("/api/click_like/<type>/<item_id>/<user_id>", methods = ["GET"])
def click_like(type, item_id, user_id):
    #response_json = request.get_json(force = True)
    #type = response_json["type"]
    #item_id = response_json["item_id"]
    #user_id = response_json["user_id"]
    if type == "post":
        item = collection_post.find_one({"_id": ObjectId(str(item_id))})
    elif type == "comment":
        item = collection_post_comment.find_one({"_id": ObjectId(str(item_id))})
    elif type == "reply":
        item = collection_post_reply.find_one({"_id": ObjectId(str(item_id)) })


    item_like_list = item["like_list"]
    item_like_number = item["like_number"]
    if user_id in item_like_list:
        item_like_list.remove(user_id)
        item_like_number += -1
    else:
        item_like_list.append(user_id)
        item_like_number += 1
    

    if type == "post":
        collection_post.update_one({"_id": ObjectId(str(item_id))}, {"$set": {"like_list": item_like_list}})
        collection_post.update_one({"_id": ObjectId(str(item_id))}, {"$set": {"like_number": item_like_number}})
    elif type == "comment":
        collection_post_comment.update_one({"_id": ObjectId(str(item_id))}, {"$set": {"like_list": item_like_list}})
        collection_post_comment.update_one({"_id": ObjectId(str(item_id))}, {"$set": {"like_number": item_like_number}})
    elif type == "reply":
        collection_post_reply.update_one({"_id": ObjectId(str(item_id)) }, {"$set": {"like_list": item_like_list}})
        collection_post_reply.update_one({"_id": ObjectId(str(item_id))}, {"$set": {"like_number": item_like_number}})
    
    send_json = { }
    send_json['check'] = "True"
    send_to_json = json.loads(json_util.dumps(send_json))
    return send_to_json



@app.route("/notification", methods = ["GET", "POST"])
def notification():
    users = mongo.db.users
    login_user = users.find_one({'username' : session.get('username')})
    notification = login_user["notification"]
    if (notification['number'] == 0):
        return "You dont have any notification"
    else:
        notification_list = notification["list"]
        notification_content_list = []
        clear_notification: {
            "number": 0,
            "list": []
        }
        users.update_one({'username' : session.get('username')},{"$set": {"notification": {"number": 0, "list": [] } }})
        return render_template("notification.html", notification_list = notification_list)




@app.route("/api/viewmore/<post_id>")
def api_viewmore(post_id):
    post = collection_post.find_one({"_id": ObjectId(str(post_id))})
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
        if element == 'zip_code':
            return_hospitals = []
            zip_code = request.form.get('zip_code')
            for hospital in collection_hospital.find():
                if zip_code == hospital['properties']['ZIP']:
                    return_hospitals.append(hospital['properties']['NAME'])
                    return render_template('hospital_name.html', hospitals = return_hospitals)
            return "cannot find by zip code"
        if element == 'name':
            return_hospitals = []
            name = request.form.get('name')
            for hospital in collection_hospital.find():
                if name.lower() in hospital['properties']['NAME'].lower():
                    return_hospitals.append(hospital['properties']['NAME'])

            if len(return_hospitals) == 0:
                return "name not found"
            else:
                return render_template('hospital_name.html', hospitals = return_hospitals)
    return "what happended?"

@app.route("/api/hospital/<element>", methods = ["GET", "POST"])
def api_hospital(element):
    if request.method == "GET":
        return render_template('hospital.html')
    else:
        response_json = request.get_json(force = True)
        return_hospitals = { 
                "hospital": []
            }
        if element == 'zip_code':
            zip_code = response_json['element']
            print(zip_code)
            for hospital in collection_hospital.find():
                if str(zip_code) == str(hospital['properties']['ZIP']):
                    print("yes")
                    return_hospitals["hospital"].append(hospital)
                    send_to_json = json.loads(json_util.dumps(return_hospitals))
                    return send_to_json
            send_to_json = json.loads(json_util.dumps(return_hospitals))
            return send_to_json
        if element == 'name':
            name = response_json['element']
            for hospital in collection_hospital.find():
                if name.lower() in hospital['properties']['NAME'].lower():
                    return_hospitals["hospital"].append(hospital)

            if len(return_hospitals) == 0:
                send_to_json = json.loads(json_util.dumps(return_hospitals))
                return send_to_json
            else:
                send_to_json = json.loads(json_util.dumps(return_hospitals))
                return send_to_json
    return "what happended?"

@app.route("/hospital/viewmore/<hos_name>", methods = ["GET", "POST"])
def hospital_viewmore(hos_name):
    if request.method == "GET":
        with open('Hospitals.json', 'r') as file_1:
            data=file_1.read()
        hos_info = json.loads(data)
        if len(hos_name) == 5:
            for hospital in hos_info['features']:
                if hospital['properties']['ZIP'] == hos_name:
                    result_hospital = hospital
                    break
            return render_template("hospital_viewmore.html", hospital = result_hospital)
        else:
            for hospital in hos_info['features']:
                if hos_name.lower() in hospital['properties']['NAME'].lower():
                    result_hospital = hospital
                    break
            return render_template("hospital_viewmore.html", hospital = result_hospital)
    
    else:
        if session.get("username") == None:
            return "U need to sign in first"
        else:
            comment = request.form.get("comment")
            username = session.get('username')
            just_inserted_id = collection_hospital_comment.insert_one({"content": comment, "username": username}).inserted_id

            hospital = collection_hospital.find_one({"_id": ObjectId(str(hospital_id))})
            comment_list = hospital['comment_list']
            comment_list.append({'_id':ObjectId(str(just_inserted_id)),'content': comment, 'username': username})

            collection_hospital.update_one({"_id": ObjectId(str(hospital_id))},{"$set": {"comment_list": comment_list}})
            next_page = "/hospital/viewmore/" + str(hospital_id)
            return redirect(next_page)
            

        #return str(hos_info['features'][0]['properties']['NAME'])

@app.route("/viewmore/hospital/<name>", methods = ["GET", "POST"])
def viewmore_hospital(name):
    if request.method == "GET":
        hospital = collection_hospital.find_one({'name': name.upper()})
        #print(hospital)
        comment_list = hospital['comment_list']
        return render_template('viewmore_hospital.html', hospital = hospital, comment_list = comment_list, hospital_name = hospital['name'])
    else:
        if session.get("username") == None:
            return "U need to sign in first"
        else:
            comment = request.form.get("comment")
            username = session.get('username')
            just_inserted_id = collection_hospital_comment.insert_one({"content": comment, "username": username}).inserted_id

            hospital = collection_hospital.find_one({"name": name})
            comment_list = hospital['comment_list']
            comment_list.append({'_id':ObjectId(str(just_inserted_id)),'content': comment, 'username': username})

            collection_hospital.update_one({"name": name},{"$set": {"comment_list": comment_list}})
            next_page = "/viewmore/hospital/" + name
            return redirect(next_page)


@app.route("/api/viewmore/hospital/<name>", methods = ["GET", "POST"])
def api_viewmore_hospital(name):
    if request.method == "GET":
        hospital = collection_hospital.find_one({'name': name.upper()})
        #print(hospital)
        send_to_json = json.loads(json_util.dumps(hospital))
        return send_to_json
    else:
        response_json = request.get_json(force = True)
        comment = response_json["comment"]
        username = response_json['username']
        just_inserted_id = collection_hospital_comment.insert_one({"content": comment, "username": username}).inserted_id
        hospital = collection_hospital.find_one({"name": name})
        comment_list = hospital['comment_list']
        comment_list.append({'_id':ObjectId(str(just_inserted_id)),'content': comment, 'username': username})
        collection_hospital.update_one({"name": name},{"$set": {"comment_list": comment_list}})

        hospital = collection_hospital.find_one({'name': name.upper()})
        send_to_json = json.loads(json_util.dumps(hospital))
        return send_to_json
        


@app.route("/surgery", methods = ["GET", "POST"])
def surgery():
    return render_template("surgery.html")

@app.route("/surgery/<name>", methods = ["GET"])
def surgery_name(name):
    posts = []
    result_surgery = collection_surgery.find_one({"name": name})
    result_surgery_list = result_surgery["list"]
    for post in result_surgery_list:
        posts.append(collection_post.find_one({"_id": post}))
    return render_template('surgery_viewmore.html', name = result_surgery["name"], posts = posts)

@app.route("/following_post")
def following_post():
    users = mongo.db.users
    login_username = session.get("username")
    login_user = users.find_one({"username": login_username})
    following_post = []
    for following in login_user["following"]["list"]:
        for posts in collection_post.find({"author": following}):
            following_post.append(posts)
    return render_template("following_post.html", posts = following_post)
    
@app.route("/friend_post")
def friend_post():
    users = mongo.db.users
    login_username = session.get("username")
    login_user = users.find_one({"username": login_username})
    friend_post = []
    for following in login_user["following"]["list"]:
        if following in login_user["follower"]["list"]:
            for posts in collection_post.find({"author": following}):
                friend_post.append(posts)
    return render_template("following_post.html", posts = friend_post)

@app.route('/get_location/hospital')
def get_location():
    geoip_data = simple_geoip.get_geoip_data()
    #return_json = jsonify(data=geoip_data)
    #zip_code = return_json.data.location.postalCode
    #return zip_code
    return jsonify(data=geoip_data)

@app.route('/api/surgery')
def api_surgery():
    result_list_id = []
    result_list_content = []
    all_post_list = []
    for surgery in collection_surgery.find():
        result_list_id += surgery["list"]

    for post in collection_post.find():
        all_post_list.append(post)
    
    all_post_list_reverse = Reverse(all_post_list)

    for post in all_post_list_reverse:
        if post["_id"] in result_list_id:
            result_list_content.append(post)
    
    result_json = {
        "surgery": result_list_content
    }
    send_to_json = json.loads(json_util.dumps(result_json))
    return send_to_json

@app.route("/api/surgery/<_id>", methods = ["GET"])
def api_surgery_id(_id):
    posts = []
    result_surgery = collection_surgery.find_one({"_id": ObjectId(str(_id)) })
    print(result_surgery)
    result_surgery_list = result_surgery["list"]
    for post in result_surgery_list:
        posts.append(collection_post.find_one({"_id": ObjectId(str(post))}))
    posts = Reverse(posts)
    result_json = {
        "surgery": result_surgery,
        "post": posts
    }
    send_to_json = json.loads(json_util.dumps(result_json))
    return send_to_json

@app.route("/api/surgery/write_comment/<_id>", methods = ["POST"])
def api_surgery_write_comment(_id):
    response_json = request.get_json(force = True)
    surgery = collection_surgery.find_one({"_id": ObjectId(str(_id)) })
    surgery_safety = surgery["scores"]["safety"]
    surgery_expense = surgery["scores"]["expense"]
    comment_list = surgery["comment_list"]
    comment_len = len(comment_list) + 1

    safety = int(response_json["safety"])
    expense = int(response_json["expense"])
    content = response_json["safety"]
    username = response_json["username"]

    new_safety = (surgery_safety + safety) / (comment_len)
    new_expense = (surgery_expense + expense) / (comment_len)
    scores = {
        "safety": new_safety, 
        "expense": new_expense 
    }
    new_comment = {
        "username": username,
        "content": content,
        "safety": safety,
        "expense": expense
    }

    new_comment_list = comment_list
    new_comment_list.append(new_comment)

    collection_surgery.update_one({"_id": ObjectId(str(_id))},{"$set": {"scores": scores}})
    collection_surgery.update_one({"_id": ObjectId(str(_id))},{"$set": {"comment_list": new_comment_list}})

    response = {}
    response["check"] = "True"
    response_json = json.loads(json_util.dumps(response))
    return response_json

    
    
@socketio.on('my event')
def handle_my_custom_event(json):
      emit('my response', json, namespace='/chat')
    

def main():
    '''The threaded option for concurrent accesses, 0.0.0.0 host says listen to all network interfaces (leaving this off changes this to local (same host) only access, port is the port listened on -- this must be open in your firewall or mapped out if within a Docker container. In Heroku, the heroku runtime sets this value via the PORT environment variable (you are not allowed to hard code it) so set it from this variable and give a default value (8118) for when we execute locally.  Python will tell us if the port is in use.  Start by using a value > 8000 as these are likely to be available.
    '''
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SECRET_KEY'] = 'hospital'
    app.secret_key = 'hospital'
    #Session(app)

    localport = int(os.getenv("PORT", 8118))


    """
    users = mongo.db.users
    for user in users.find():
        users.update_one({"_id":ObjectId(str(user['_id']))},{ "$set": 
        {'following':{
                    'number': 0,
                    'list': []
                    } 
        }})
    """
    """
    FID = 1
    for hospital in collection_hospital.find():
        collection_hospital.update_one({"_id": ObjectId(str(hospital['_id'])) },{"$set": {"post_list": [] }})
        print(FID)
        FID += 1
    """

    

    #for surgery in collection_surgery.find():
        #collection_surgery.update_one({"_id": ObjectId(str(surgery['_id']))},{"$set": {"introduction": ""}})
        #collection_surgery.update_one({"_id": ObjectId(str(surgery['_id']))},{"$set": {"comment_list": []}})
    
    """
    users = mongo.db.users
    for user in users.find():
        users.update({"username": user['username']},{"$set": {"notification": 0}})
    """
    """
    collection_post.update_many({},{ "$set": {"like_number": 0} })
    collection_post_comment.update_many({},{ "$set": {"like_number": 0} })
    collection_post_reply.update_many({},{ "$set": {"like_number": 0} })
    """

    #app.run(threaded=True, host='0.0.0.0', port=localport)
    #app.run(threaded=True, port=localport)
    socketio.run(app,debug=True,host='0.0.0.0',port=localport)
    #socketio.run(app,host='127.0.0.1', port = '8')
if __name__ == '__main__':
    main()

 
