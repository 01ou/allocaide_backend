# api/workbook.py

from flask import Blueprint, jsonify, request
from backend.utils.token import token_required
from backend.models.workbook_model import add_workbook, get_all_workbooks, db_delete_workbook
from backend.models.page_model import set_completed_state_by_ranges
from backend.models.assignment_model import add_assignment_with_confirmation, merge_assignment_data, get_all_assignment, db_delete_assignment

bp = Blueprint('workbook', __name__)


@bp.route('/create_workbook', methods=['POST'])
@token_required
def create_workbook(user_id):
    data = request.json

    if not data:
        return jsonify({'message': 'No data provided'}), 400
    
    add_workbook(user_id, data)

    return jsonify({'message' : 'workbook added successfully.'}), 200


@bp.route('/get_workbooks')
@token_required
def get_workbooks(user_id):
    result, status_code = get_all_workbooks(user_id)
    return jsonify(result), status_code
    

@bp.route('/try_add_assignment', methods=['POST'])
@token_required
def try_add_assignment(user_id):
    data = request.json

    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    result, status_code = add_assignment_with_confirmation(user_id, data)

    return jsonify(result), status_code


@bp.route('/merge_assignment', methods=['POST'])
@token_required
def merge_assignment(user_id):
    data = request.json

    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    result, status_code = merge_assignment_data(user_id, data)

    return jsonify(result), status_code


@bp.route('/add_assignment', methods=['POST'])
@token_required
def add_assignment(user_id):
    data = request.json

    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    result, status_code = add_assignment_with_confirmation(user_id, data)

    return jsonify(result), status_code


@bp.route('/get_all_assignments')
@token_required
def get_all_assignments(user_id):
    result, status_code = get_all_assignment(user_id)
    return jsonify(result), status_code


@bp.route('/add_completed_page_ranges', methods=['POST'])
@token_required
def add_completed_page_ranges(user_id):
    data = request.json

    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    workbook_id = data.get('workbook_id')
    ranges_data = data.get('completed_ranges')
    result, status_code = set_completed_state_by_ranges(user_id, workbook_id, ranges_data)

    return jsonify(result), status_code


@bp.route('/delete_workbook', methods=['POST'])
@token_required
def delete_workbook(user_id):
    data = request.json

    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    workbook_id = data.get('workbook_id')
    result, status_code = db_delete_workbook(user_id, workbook_id)

    return jsonify(result), status_code


@bp.route('/delete_assignment', methods=['POST'])
@token_required
def delete_assignment(user_id):
    data = request.json

    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    assignment_id = data.get('assignment_id')
    result, status_code = db_delete_assignment(user_id, assignment_id)

    return jsonify(result), status_code