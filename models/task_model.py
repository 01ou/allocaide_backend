import json
from datetime import datetime, timezone
from ..extensions import db

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    supplementary = db.Column(db.Text)
    deadline = db.Column(db.DateTime)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)  # 外部キー制約をCASCADEに変更
    is_deleted = db.Column(db.Boolean, default=False)

def get_all_tasks(user_id):
    # データベースからすべてのタスクを取得
    tasks = Task.query.filter_by(user_id=user_id, is_deleted=False).all()
    
    if not tasks:
        return [], 404
    
    # タスクを辞書に変換
    tasks_list = []
    for task in tasks:
        task_data = {
            'id': task.id,
            'type': 'task',
            'title': task.title,
            'supplementary': task.supplementary,
            'deadline': task.deadline.isoformat() if task.deadline else None,  # Noneの場合はISO 8601形式の文字列に変換しない
            'completed': task.completed,
        }
        tasks_list.append(task_data)
    
    # 辞書をJSON文字列に変換
    return json.dumps(tasks_list), 200


def add_task(user_id, data):
    if not user_id:
        return {'error': 'id is empty.'}, 400
    
    if not data:
        return {'error': 'data is empty.'}, 400

    title = data.get('title')
    supplementary = data.get('supplementary')
    
    # deadlineが存在するか、有効なISO 8601形式の日付文字列であるかを確認する
    deadline_str = data.get('deadline')
    deadline = None
    if deadline_str:
        try:
            deadline = datetime.fromisoformat(deadline_str).astimezone(timezone.utc)
        except ValueError:
            return {'error': 'Invalid deadline format. Please provide a valid ISO 8601 date and time string.'}, 400

    completed = data.get('completed')

    # タスクを作成してデータベースに追加
    new_task = Task(title=title, supplementary=supplementary, deadline=deadline, completed=completed, user_id=user_id)
    db.session.add(new_task)
    db.session.commit()

    # タスクの追加が成功したことを示すメッセージを返す
    return {'message': 'Task added successfully.'}, 200


def set_finish_state(use_id, id, state):
    error_response, status_code = validate_id(use_id, id)
    if error_response:
        return error_response, status_code
    
    task = Task.query.get(id)
    
    if task:
        task.completed = state
        db.session.commit()
        return {'message': 'Task finish state updated successfully'}, 200
    else:
        return {'error': 'Task not found'}, 404


def db_delete_task(user_id, task_id):
    task_to_delete = Task.query.filter_by(id=task_id, is_deleted=False).first()
    if not task_to_delete:
        return {'error': 'task not found.'}, 404

    error_response, status_code = validate_id(user_id, task_id)
    if error_response:
        return error_response, status_code

    error_response, status_code = validate_id(user_id, task_id)
    if error_response:
        return error_response, status_code

    try:
        task_to_delete.is_deleted = True
        db.session.commit()
        return {'message': 'task deleted successfully.'}, 200
    except Exception as e:
        db.session.rollback()
        return {'error': f"Failed to delete task: {str(e)}"}, 500
    

'''
    error_response, status_code = validate_id(user_id, workbook_id)
    if error_response:
        return error_response, status_code
'''
def validate_id(user_id, task_id):
    if not user_id:
        return {'error': 'User ID is empty.'}, 400

    if not task_id:
        return {'error': 'task ID is empty.'}, 400
    
    task = Task.query.filter_by(id=task_id, user_id=user_id, is_deleted=False).first()
    if not task:
        return {'error': 'User ID and task ID do not match.'}, 400

    return None, None