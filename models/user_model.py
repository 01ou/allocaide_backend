#models/user.py

import hashlib
from ..extensions import db
from ..utils.model_util import validate_password


USERNAME_LENGTH = 100
PASSWORD_LENGTH = 100

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)
    is_deleted = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<User %r>' % self.username


def add_user(username, password):
    # ユーザー名とパスワードがどちらも提供されていることを確認する
    if not username or not password:
        return {'error': 'Username and password are required.'}, 400, None
    
    if len(username) > USERNAME_LENGTH:
        return {'error': 'Username is too long.'}, 400, None
    elif len(password) > PASSWORD_LENGTH:
        return {'error': 'Password is too long.'}, 400, None
    
    # ユーザー名の重複をチェックする
    if User.query.filter_by(username=username, is_deleted=False).first():
        return {'error': 'Username already exists.'}, 409, None
    
    valid, message, error_code = validate_password(password)
    if not valid:
        return {'error': f'Invalid password.{message}'}, error_code, None
    
    # パスワードをハッシュ化する
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return {'message': 'User created successfully.'}, 200, new_user


def verify_user(username, password):
    # ユーザー名とパスワードがどちらも提供されていることを確認する
    if not username or not password:
        return {'error': 'Username and password are required.'}, 400, None
    
    # ユーザーが存在するかを確認する
    user = User.query.filter_by(username=username, is_deleted=False).first()
    not_match_message = 'The login information does not match the account information in the system.'
    if not user:
        return {'error': not_match_message}, 404, None
    
    # 入力されたパスワードをハッシュ化してデータベース内のハッシュと比較する
    hashed_input_password = hashlib.sha256(password.encode()).hexdigest()
    if user.password != hashed_input_password:
        return {'error': not_match_message}, 404, None
    
    # ユーザーが認証された場合は、成功メッセージを返す
    return {'message': 'User authenticated successfully.'}, 200, user



def get_user_by_id(id):
    if not id:
        return {'error': 'ID is required.'}, 400

    user = User.query.get(id)
    if not user:
        return {'error': 'User not found.'}, 404
    
    # ユーザーオブジェクトの属性を辞書に変換して返す
    user_data = {
        'id': user.id,
        'username': user.username,
        # 必要に応じて他の属性も追加
    }
    return user_data, 200



