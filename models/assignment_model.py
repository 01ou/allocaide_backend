import json
from datetime import datetime

from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound

from ..extensions import db
from backend.utils.util import (
    remove_range_duplicates, 
    convert_to_isoformat, 
    get_completed_fraction, 
    get_now_tokyo_time,
    is_not_empty,
)
from backend.utils.model_util import (
    validate_range_format,
    ranges_data_to_ranges_list,
    dict_to_range_list
)
from backend.models.workbook_model import (
    validate_id, 
    get_workbook_matching_user_id, 
    get_workbook_for_user,
    get_assignments,
)
from backend.models.page_model import (
    get_completed_page_percentage,
    get_incomplete_page_ranges
)


# 課題-ページ範囲間の中間テーブルのモデル
assignment_page_range_link = db.Table('assignment_page_range_link',
    db.Column('assignment_id', db.Integer, db.ForeignKey('assignment.id', ondelete='CASCADE'), primary_key=True),
    db.Column('page_range_id', db.Integer, db.ForeignKey('page_range.id', ondelete='CASCADE'), primary_key=True)
)


class PageRange(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    start = db.Column(db.Integer, nullable=False)
    end = db.Column(db.Integer, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    workbook_id = db.Column(db.Integer, db.ForeignKey('workbook.id', ondelete='CASCADE'), nullable=False)
    deadline = db.Column(db.DateTime)
    supplementary = db.Column(db.Text)
    assignment_page_ranges = db.relationship('PageRange', secondary=assignment_page_range_link, lazy='subquery', cascade='all, delete', backref=db.backref('assignments', lazy=True))
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime)
    is_deleted = db.Column(db.Boolean, default=False)


def add_assignment_with_confirmation(user_id, data):
    try:
        # ワークブックIDを取得
        workbook_id = data.get('workbook_id')
        if not workbook_id:
            return {'error': 'Workbook ID is required.'}, 400
        
        # ユーザーIDとワークブックIDのバリデーションをチェック
        error_response, status_code = validate_id(user_id, workbook_id)
        if error_response:
            return error_response, status_code
        
        # デッドラインを取得して日付オブジェクトに変換
        deadline_str = data.get('deadline')
        if not deadline_str:
            return {'error': 'Deadline is required.'}, 400
        try:
            deadline = datetime.fromisoformat(deadline_str)
        except ValueError:
            return {'error': 'Invalid deadline format. Please provide a valid ISO format datetime.'}, 400
        
        # ワークブックIDとデッドラインが重複する課題のIDを取得
        existing_assignment_id = get_assignment_id_duplicate(workbook_id, deadline)
        
        # 追加タイプを取得
        add_type = data.get('add_type')
        
        # 追加タイプに応じて処理を分岐
        if add_type == 'new' or not existing_assignment_id:
            # 新規課題を追加する場合
            return add_assignment(user_id, workbook_id, deadline, data)
        elif add_type == 'try':
            # 重複する課題がある場合はIDを返す
            return existing_assignment_id, 202
        else:
            return {'error': 'Invalid additional type.'}, 400

    except SQLAlchemyError as e:
        # データベースエラーが発生した場合はロールバックしてエラーを返す
        db.session.rollback()
        return {'error': 'Database error occurred.'}, 500
    except Exception as e:
        # その他の例外が発生した場合はロールバックしてエラーを返す
        db.session.rollback()
        return {'error': str(e)}, 500


def add_assignment(user_id, workbook_id, deadline, data):
    try:
        error_response, status_code = validate_id(user_id, workbook_id)
        if error_response:
            return error_response, status_code

        supplementary = data.get('supplementary')

        new_assignment = Assignment(workbook_id=workbook_id, deadline=deadline, supplementary=supplementary)
        db.session.add(new_assignment)
        db.session.commit()

        range_data = data.get('assignment_page_ranges', [])
        update_page_range_with_old_range(user_id, workbook_id, new_assignment, range_data)

        return {'message': 'Assignment added successfully.'}, 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500

    
def merge_assignment_data(user_id, data):
    try:
        workbook_id = data.get('workbook_id')
        merge_target_assignment_id = data.get('merge_target_assignment_id')

        if not workbook_id:
            return {'error': 'Workbook ID is required.'}, 400
        
        if not merge_target_assignment_id:
            return {'error': 'Merge target assignment ID is required.'}, 400

        error_response, status_code = validate_id(user_id, workbook_id)
        if error_response:
            return error_response, status_code

        existing_assignment = get_existing_assignment(merge_target_assignment_id)

        if not existing_assignment:
            return {'error': 'Merge target assignment not found.'}, 404

        new_supplementary = data.get('supplementary', '')
        new_assignment_page_ranges = data.get('assignment_page_ranges', [])

        merged_supplementary = merge_supplementary(existing_assignment.supplementary, new_supplementary)
        merged_ranges = merge_assignment_page_ranges(existing_assignment.assignment_page_ranges, new_assignment_page_ranges)

        existing_assignment.supplementary = merged_supplementary

        # 更新日時をアップデート
        now_time = get_now_tokyo_time()
        existing_assignment.updated_at = now_time

        db.session.commit()

        update_page_range_by_array(existing_assignment, merged_ranges, True)

        return {'message': 'Assignment merged successfully.'}, 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500


def get_existing_assignment(merge_target_assignment_id):
    try:
        existing_assignment = Assignment.query.filter_by(id=merge_target_assignment_id, is_deleted=False).one()
        return existing_assignment
    except NoResultFound:
        return None

def merge_supplementary(existing_supplementary_text, new_supplementary_text):
    """
    既存の補足情報と新しい補足情報をマージする関数。

    :param existing_supplementary_text: 既存の補足情報のテキスト
    :param new_supplementary_text: 新しい補足情報のテキスト
    :return: マージされた補足情報のテキスト
    """
    if is_not_empty(existing_supplementary_text) and is_not_empty(new_supplementary_text):
        return '\n'.join([existing_supplementary_text, new_supplementary_text])
    else:
        return existing_supplementary_text + new_supplementary_text

def merge_assignment_page_ranges(existing_ranges_data, new_ranges):
    existing_ranges_array = ranges_data_to_ranges_list(existing_ranges_data)
    new_ranges_array = dict_to_range_list(new_ranges)
    return remove_range_duplicates(existing_ranges_array + new_ranges_array)


def get_assignment_id_duplicate(workbook_id, deadline):
    # ワークブックIDとデッドラインが一致する課題が存在するかをクエリでチェックする
    existing_assignments = Assignment.query.filter_by(workbook_id=workbook_id, deadline=deadline, is_deleted=False).all()
    existing_assignment_ids = [int(assignment.id) for assignment in existing_assignments]
    return existing_assignment_ids


def get_all_assignment(user_id):
    # ユーザーが所有するすべてのワークブックを取得

    workbooks_id = get_workbook_matching_user_id(user_id)
    assignments = []
    for workbook_id in workbooks_id:
        # ワークブックに関連するすべての課題を取得
        workbook = get_workbook_for_user(user_id, workbook_id)
        workbook_title = workbook.title
        workbook_assignments = get_assignments(user_id, workbook_id)

        for assignment in workbook_assignments:
            if assignment.is_deleted == True:
                continue

            # 課題ごとに完了したページの割合を計算し、データに追加
            active_page_ranges_data = get_active_page_ranges(assignment)
            assignment_page_ranges = ranges_data_to_ranges_list(active_page_ranges_data)
            incomplete_page_ranges = get_incomplete_page_ranges(assignment)
            completion_percentage = get_completed_page_percentage(assignment)
            completed_fraction = get_completed_fraction(incomplete_page_ranges, assignment_page_ranges)

            assignment_data = {
                'id': assignment.id,
                'type': 'assignment',
                'workbook_id': assignment.workbook_id,
                'workbook_title': workbook_title,
                'deadline': convert_to_isoformat(assignment.deadline),
                'supplementary': assignment.supplementary,
                'assignment_page_ranges': assignment_page_ranges,
                'incomplete_page_ranges': incomplete_page_ranges,
                'completion_percentage': completion_percentage,
                'completed_fraction': completed_fraction,
                'created_at': convert_to_isoformat(assignment.created_at),
                'updated_at': convert_to_isoformat(assignment.updated_at),
            }
            assignments.append(assignment_data)

    return json.dumps(assignments), 200


def update_page_range_by_array(assignment, page_ranges_array, delete_existing_ranges=False):
    try:
        # page_ranges_array の形式を確認
        if not isinstance(page_ranges_array, list):
            return {'error': 'Page ranges must be provided as a list.'}, 400

        new_page_ranges = []
        for page_range in page_ranges_array:
            # 各ページ範囲の形式を確認
            if not isinstance(page_range, list) or len(page_range) != 2:
                return {'error': 'Each page range must be provided as a list containing start and end values.'}, 400
            
            new_page_range = PageRange(start=page_range[0], end=page_range[1])
            new_page_ranges.append(new_page_range)

        db.session.add_all(new_page_ranges)
        db.session.commit()

        if delete_existing_ranges:
            # 既存のページ範囲を削除
            assignment.assignment_page_ranges.clear()
        
        assignment.assignment_page_ranges.extend(new_page_ranges)
        db.session.commit()

        return {'message': 'Page ranges added successfully.'}, 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'error': str(e)}, 500


def get_active_page_ranges(assignment):
    """
    論理削除されていないページ範囲のデータを取得する関数

    Args:
        assignment: Assignment オブジェクトまたはそれに類似するオブジェクト

    Returns:
        list: 論理削除されていない PageRange オブジェクトのリスト
    """
    active_page_ranges = []

    # assignment オブジェクトの存在と属性の確認
    if hasattr(assignment, 'assignment_page_ranges'):
        # is_deleted が False の要素だけを取得
        active_page_ranges = [r for r in assignment.assignment_page_ranges if hasattr(r, 'is_deleted') and not r.is_deleted]

    return active_page_ranges


def update_page_range_with_old_range(user_id, workbook_id, target_assignment, range_data):
    try:
        # レンジデータの形式を検証
        error_response, status_code = validate_range_format(range_data)
        if error_response:
            return error_response, status_code
        
        # ユーザーIDとワークブックIDを検証
        error_response, status_code = validate_id(user_id, workbook_id)
        if error_response:
            return error_response, status_code
        
        # ターゲットの課題が存在することを確認
        if not target_assignment:
            error_message = 'Target assignment not found'
            return {'error': error_message}, 404
        
        # 既存の範囲データを取得
        existing_ranges = target_assignment.assignment_page_ranges
        existing_range_array = ranges_data_to_ranges_list(existing_ranges)

        page_range_array = dict_to_range_list(range_data)
        
        # 範囲の重複を取り除く
        combined_ranges = remove_range_duplicates(page_range_array + existing_range_array)

        # 新しい範囲をデータベースに追加
        page_ranges = []
        for start, end in combined_ranges:
            new_range = PageRange(start=start, end=end)
            db.session.add(new_range)
            page_ranges.append(new_range)

        # ターゲットの課題に範囲を追加
        target_assignment.assignment_page_ranges.extend(page_ranges)
        db.session.commit()

        return {'message': 'Page ranges updated successfully'}, 200

    except SQLAlchemyError as e:
        # データベーストランザクションのロールバック
        db.session.rollback()
        error_message = 'Database error occurred'
        return {'error': error_message}, 500

    except Exception as e:
        # その他のエラーの場合もトランザクションをロールバック
        db.session.rollback()
        error_message = 'An unexpected error occurred'
        return {'error': error_message}, 500
    

def db_delete_assignment(user_id, assignment_id):
    assignment_to_delete = Assignment.query.filter_by(id=assignment_id, is_deleted=False).first()

    if not assignment_to_delete:
        return {'error': 'assignment not found.'}, 404
    
    workbook_id = assignment_to_delete.workbook_id

    error_response, status_code = validate_id(user_id, workbook_id)
    if error_response:
        return error_response, status_code

    try:
        assignment_to_delete.is_deleted = True

        ranges = assignment_to_delete.assignment_page_ranges
        for r in ranges:
            r.is_deleted = True

        db.session.commit()
        return {'message': 'assignment deleted successfully.'}, 200
    except Exception as e:
        db.session.rollback()
        return {'error': f"Failed to delete assignment: {str(e)}"}, 500
