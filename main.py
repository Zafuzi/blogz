from flask import Flask, request, render_template, url_for, redirect
from livereload import Server, shell
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)
app.debug = True

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blog:mypassword@localhost:8889/blog'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
db.create_all()

server = Server(app)
server.watch('/templates/*.html', '/static/styles/*.css', 'main.py')

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.Text())
    def __init__(self, title, body):
        self.title = title
        self.body = body
    
posts = Post.query.all()

@app.route("/styles")
def styles():
    """ Routes static stylesheet assest """
    return url_for('static', filename='style.css')

@app.route('/', methods=['POST', 'GET'])
def index():
    posts = Post.query.all()
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        new_post = Post(title, body)
        db.session.add(new_post)
        db.session.commit()
        posts = Post.query.all()
    return render_template('index.html',title="Blog", posts=list(reversed(posts)))

@app.route('/newpost', methods=['POST', 'GET'])
def newpost():
    titleOK = True
    bodyOK = True
    if request.method == 'POST':
        titleOK = False
        bodyOK = False
        title = request.form['title']
        body = request.form['body']

        if title and body:
            if len(title) > 0 and len(body) > 0:
                new_post = Post(title, body)
                db.session.add(new_post)
                db.session.commit()
                titleOK = True
                bodyOK = True
                print("ID: %i" % new_post.id)
                id = new_post.id
                return redirect(str.format('/post?id={0}', id))

    return render_template('newpost.html', title="Blog | Newpost", titleOK = titleOK, bodyOK = bodyOK)

@app.route('/post')
def viewPost(id=0):
    id = request.args.get('id')
    post = ""
    if id:
        post = Post.query.get(id)
        print("ID:", id)
    return render_template('blog.html', title= str.format("Blog | Post {0}", id ), post = post)

if __name__ == '__main__':
    server = Server(app.wsgi_app)
    server.serve()
