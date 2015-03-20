import os
import uuid
import psycopg2, psycopg2.extras
from flask import Flask, session
from flask.ext.socketio import SocketIO, emit

app = Flask(__name__, static_url_path='')
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
app.debug = True

socketio = SocketIO(app)


messages = []
users = {}

def connectToDB():
  connectionString = 'dbname=chat user=postgres password=Rollingrock19 host=localhost'
  try:
    return psycopg2.connect(connectionString)
  except:
    print("Can't connect to database")

def updateRoster():
    names = []
    for user_id in  users:
        print users[user_id]['username']
        if len(users[user_id]['username'])==0:
            names.append('Anonymous')
        else:
            names.append(users[user_id]['username'])
    emit('roster', names, broadcast=True)
    

@socketio.on('connect', namespace='/chat')
def test_connect():
    session['uuid']=uuid.uuid1()
    session['username']='starter name'
    print 'connected'
    users[session['uuid']]={'username':'New User'}
    updateRoster()
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    get = "SELECT messages, username FROM messages JOIN users ON messages.user_id = users.user_id"
    cur.execute(get)
    answers = cur.fetchall()
    messages = []
   
    for answer in answers:
        tmp = {'text': answer['messages'], 'name': answer['username']}
        messages.append(tmp)

    for message in messages:
        emit('message', message)

@socketio.on('message', namespace='/chat')
def new_message(message):
    tmp = {'text':messages, 'name':users[session['uuid']]['username']}
    messages.append(tmp)
    conn =connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    user = session['id']
    message_insert = "INSERT INTO messages (user_id, messages) VALUES(%s, %s)";
    cur.execute(message_insert, (user, message))
    conn.commit()
    emit('message', tmp, broadcast=True)
    
@socketio.on('identify', namespace='/chat')
def on_identify(message):
    print 'identify' + message
    users[session['uuid']]={'username':message}
    updateRoster()


@socketio.on('login', namespace='/chat')
def on_login(info):
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    user = info['username']
    passw = info['password']
    login_execution = "SELECT * FROM users WHERE username = %s AND password = crypt(%s, password)"
    cur.execute(login_execution, (user, passw))
    output = cur.fetchone()
    
    if output:
        users[session['uuid']]={'username': user}
        session['id'] = output[0]
        session['username'] = output[1]
        updateRoster()
        print 'successful login'
    else:
        print' unsuccessful login'
        

@socketio.on('search', namespace='/chat')
def on_search(searchInput):
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    search_execution = "SELECT username, messages FROM messages JOIN users ON messages.user_id = users.id WHERE message LIKE %s OR username LIKE %s"
    cur.execute(search_execution % searchInput)
    outputs = cur.fetchall()
    results = []
    
    for result in outputs:
        tmp = {'text': result['messages'], 'name': result['username']}
        results.append(tmp)

    for result in results:
        emit('result', result)
    
@socketio.on('disconnect', namespace='/chat')
def on_disconnect():
    print 'disconnect'
    if session['uuid'] in users:
        del users[session['uuid']]
        updateRoster()

@app.route('/')
def hello_world():
    print 'in hello world'
    return app.send_static_file('index.html')

@app.route('/js/<path:path>')
def static_proxy_js(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(os.path.join('js', path))
    
@app.route('/css/<path:path>')
def static_proxy_css(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(os.path.join('css', path))
    
@app.route('/img/<path:path>')
def static_proxy_img(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(os.path.join('img', path))
    
if __name__ == '__main__':
    print "A"

    socketio.run(app, host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)))
     
