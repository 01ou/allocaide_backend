# api/task.py

from flask import Blueprint, jsonify, request
from backend.utils.token import token_required
from backend.models.task_model import add_task, get_all_tasks, set_finish_state, db_delete_task

bp = Blueprint('task', __name__)


@bp.route('/create_task', methods=['POST'])
@token_required
def create_task(user_id):
    data = request.json
    
    if not data:
        return jsonify({'message': 'No data provided'}), 400
    
    add_task(user_id, data)

    return jsonify({'message' : 'Task added successfully.'}), 200


@bp.route('/get_tasks')
@token_required
def get_tasks(user_id):
    result, status_code = get_all_tasks(user_id)
    return jsonify(result), status_code
    

@bp.route('/set_task_finish_state', methods=['POST'])
@token_required
def set_task_finish_state(user_id):
    data = request.get_json()
    task_id = data.get('task_id')
    completed = data.get('completed')

    response, status_code = set_finish_state(user_id, task_id, completed)

    return jsonify(response), status_code


@bp.route('/delete_task', methods=['POST'])
@token_required
def delete_task(use_id):
    data = request.get_json()
    task_id = data.get('task_id')
    response, status_code = db_delete_task(use_id, task_id)

    return jsonify(response), status_code

