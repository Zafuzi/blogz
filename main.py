from flask import Flask, request, render_template, url_for, redirect, session
from livereload import Server, shell
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)
app.debug = True
app.secret_key = '\x02\x95\xa1j\xe5\x18\x8d\x95\x8b\xce\x0e5\x12\xf3\xa3%\x18\xba$\x9f\xe8>\xb8\xe6'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blog:mypassword@localhost:8889/blog'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
db.create_all()

server = Server(app)
server.watch('/templates/*.html', '/static/styles/*.css', 'main.py')

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(120))
    body = db.Column(db.Text())
    private = db.Column(db.Boolean())
    def __init__(self, id, title, body, private):
        self.title = title
        self.body = body
        self.user_id = id
        self.private = private

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25))
    password = db.Column(db.String(25))
    blogs = db.relationship('Post', backref='blogs')

    def __init__(self, username, password):
        self.username = username
        self.password = password
    
posts = Post.query.all()


@app.before_request
def require_login():
    allowed_routes = ['index', 'post', 'static', 'login', 'register']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')
    if 'id' not in session and 'username' in session:
        user = User.query.filter_by(username = session['username']).first()
        session['id'] = user.id

@app.route("/styles")
def styles():
    """ Routes static stylesheet assest """
    return url_for('static', filename='style.css')

@app.route('/', methods=['GET'])
def index():
    posts = Post.query.filter_by(private=0).all()
    return render_template('index.html', 
                                title="Blog", 
                                posts=list(reversed(posts)))

@app.route('/newpost', methods=['POST', 'GET'])
def newpost():
    titleOK = True
    bodyOK = True
    if request.method == 'POST':
        titleOK = False
        bodyOK = False
        form = request.form.to_dict()
        title = form['title']
        body = form['body']

        if 'public' in form:
            private = 0
        else:
            private = 1

        if title and body:
            if len(title) > 0 and len(body) > 0:
                new_post = Post(session['id'], title, body, private)
                db.session.add(new_post)
                db.session.commit()
                titleOK = True
                bodyOK = True
                id = new_post.id
                return redirect(str.format('/post?id={0}', id))

    return render_template('newpost.html', 
                                title="Blog | Newpost", 
                                titleOK = titleOK, 
                                bodyOK = bodyOK)

@app.route('/post')
def viewPost(id=0):
    id = request.args.get('id')
    post = ""
    if id:
        post = Post.query.get(id)

    return render_template('blog.html', 
                                title= str.format("Blog | Post {0}", id ), 
                                post = post)

@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        form = request.form.to_dict()
        username = form['username']
        password = form['password']
        user = User.query.filter_by(username = username, password = password).first()
        if user != None:
            session['username'] = username
            session['id'] = user.id
            return redirect('/user')
        else:
            return render_template('login.html')
    else:
        return render_template('login.html')

@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        form = request.form.to_dict()
        username = form['username']
        password = form['password']
        password2 = form['password2']
        user = User.query.filter_by(username = username).first() is None
        if user and password == password2:
            session['username'] = username
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            return redirect('/user')
        else:
            return render_template('register.html')
    else:
        return render_template('register.html')

@app.route('/logout')
def logout():
    del session['username']
    del session['id']
    return redirect('/')

@app.route("/user")
def user(id=0):
    id = request.args.get('id')
    print("ID: ", id)
    if id != 0 and id is not None:
        print("id is not None")
        user = User.query.filter_by(id = id).first()
        if user:
            username = user.username
            posts = Post.query.filter_by(user_id = user.id, private = 0).all()
            return render_template('user.html', 
                                username = username, 
                                title= str.format("Blog | User {0}", username), 
                                posts = posts)
    else:
        username = session['username']
        if username is not None:
            user = User.query.filter_by(username = username).first()
            id = user.id
            posts = Post.query.filter_by(user_id = user.id).all()
            return render_template('user.html', 
                                        username = username, 
                                        title= str.format("Blog | u/{0}", "Zach"), 
                                        posts = list(reversed(posts)))
        else:
            return render_template('user.html', 
                                        username="User Not Found", 
                                        title= str.format("Blog | User {0}", "User not found"), 
                                        posts = [])

if __name__ == '__main__':
    server = Server(app.wsgi_app)
    server.serve()
