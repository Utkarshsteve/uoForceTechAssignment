from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    posts = db.relationship('Post', backref='user', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_public = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    likes = db.relationship('Like', backref='post', lazy=True)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)


# User APIs
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.username for user in users]), 200

@app.route('/users', methods=['POST'])
def create_user():
    username = request.json.get('username')
    password = request.json.get('password')
    is_admin = request.json.get('is_admin', False)
    try:
        user = User(username=username, password=password, is_admin=is_admin)
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'User created successfully.'}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Username already exists.'}), 400

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({'username': user.username, 'is_admin': user.is_admin}), 200

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    if not user.is_admin and user.id != current_user.id:
        return jsonify({'message': 'You are not authorized to update this user.'}), 401
    username = request.json.get('username', user.username)
    password = request.json.get('password', user.password)
    is_admin = request.json.get('is_admin', user.is_admin)
    user.username = username
    user.password = password
    user.is_admin = is_admin
    db.session.commit()
    return jsonify({'message': 'User updated successfully.'}), 200

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if not user.is_admin and user.id != current_user.id:
        return jsonify({'message': 'You are not authorized to delete this user.'}), 401
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully.'}), 200



# Post/Blog APIs
@app.route('/posts', methods=['GET'])
def get_posts():
    posts = Post.query.all()
    result = []
    for post in posts:
        likes_count = Like.query.filter_by(post_id=post.id).count()
        result.append({'title': post.title, 'content': post.content, 'is_public': post.is_public, 'likes': likes_count})
    return jsonify(result), 200

@app.route('/posts', methods=['POST'])
def create_post():
    title = request.json.get('title')
    content = request.json.get('content')
    is_public = request.json.get('is_public', True)
    user_id = request.json.get('user_id')
    post = Post(title=title, content=content, is_public=is_public, user_id=user_id)
    db.session.add(post)
    db.session.commit()
    return jsonify({'message': 'Post created successfully.'}), 201

@app.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = Post.query.get_or_404(post_id)
    if not post.is_public and post.user_id != current_user.id:
        return jsonify({'message': 'You are not authorized to view this post.'}), 401
    likes_count = Like.query.filter_by(post_id=post.id).count()
    return jsonify({'title': post.title, 'content': post.content, 'is_public': post.is_public, 'likes': likes_count}), 200

@app.route('/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        return jsonify({'message': 'You are not authorized to update this post.'}), 401
    title = request.json.get('title', post.title)
    content = request.json.get('content', post.content)
    is_public = request.json.get('is_public', post.is_public)
    post.title = title
    post.content = content
    post.is_public = is_public
    db.session.commit()
    return jsonify({'message': 'Post updated successfully.'}), 200


# Like APIs
@app.route('/likes', methods=['POST'])
def like_post():
    post_id = request.json.get('post_id')
    user_id = request.json.get('user_id')
    like = Like.query.filter_by(post_id=post_id, user_id=user_id).first()
    if like is None:
        like = Like(post_id=post_id, user_id=user_id)
        db.session.add(like)
        db.session.commit()
        return jsonify({'message': 'Post liked successfully.'}), 201
    else:
        db.session.delete(like)
        db.session.commit()
        return jsonify({'message': 'Post unliked successfully.'}), 200

@app.route('/likes/<int:like_id>', methods=['PUT'])
def update_like(like_id):
    like = Like.query.get_or_404(like_id)
    if like.user_id != current_user.id:
        return jsonify({'message': 'You are not authorized to update this like.'}), 401
    like.post_id = request.json.get('post_id', like.post_id)
    like.user_id = request.json.get('user_id', like.user_id)
    db.session.commit()
    return jsonify({'message': 'Like updated successfully.'}), 200

@app.route('/likes/<int:like_id>', methods=['DELETE'])
def delete_like(like_id):
    like = Like.query.get_or_404(like_id)
    if like.user_id != current_user.id:
        return jsonify({'message': 'You are not authorized to delete this like.'}), 401
    db.session.delete(like)
    db.session.commit()
    return jsonify({'message': 'Like deleted successfully.'}), 200

@app.route('/likes/<int:post_id>', methods=['GET'])
def get_likes(post_id):
    likes = Like.query.filter_by(post_id=post_id).all()
    return jsonify([{'user_id': like.user_id} for like in likes]), 200

if __name__ == '__main__':
    app.debug = True
    app.run()