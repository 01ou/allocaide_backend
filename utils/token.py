from flask import jsonify, request, current_app
import jwt, datetime
from functools import wraps
from datetime import datetime, timedelta, timezone

# アクセストークンの有効期限（例: 1時間）
ACCESS_TOKEN_EXPIRATION = timedelta(hours=1)
# リフレッシュトークンの有効期限（例: 7日）
REFRESH_TOKEN_EXPIRATION = timedelta(days=7)


def generate_access_token(user_id):
    secret_key = current_app.config['SECRET_KEY']
    expiration_time = datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRATION
    exp_timestamp = int(expiration_time.timestamp())
    payload = {
        'user_id': user_id,
        'exp': exp_timestamp
    }
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token


def generate_refresh_token(user_id):
    secret_key = current_app.config['SECRET_KEY']
    expiration_time = datetime.now(timezone.utc) + REFRESH_TOKEN_EXPIRATION
    exp_timestamp = int(expiration_time.timestamp())
    payload = {
        'user_id': user_id,
        'exp': exp_timestamp
    }
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token



def token_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or token == 'Bearer null':
            return jsonify({'error': 'Token not found.'}), 401
        
        try:
            token_parts = token.split()
            if len(token_parts) != 2:
                raise jwt.InvalidTokenError('Invalid token format')
            
            payload = jwt.decode(token_parts[1], current_app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = payload.get('user_id')
            if user_id is None:
                raise jwt.InvalidTokenError('User ID not found in token payload')

            # 元の関数に user_id を渡して実行
            return func(user_id, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({'error': str(e)}), 401
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
    return wrapper
