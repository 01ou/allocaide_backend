import json
from ..extensions import db


class Workbook(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    pages = db.relationship('Page', backref='workbook', lazy=True, cascade='all, delete-orphan', passive_deletes=True)
    assignments = db.relationship('Assignment', backref='workbook', lazy=True, cascade='all, delete-orphan', passive_deletes=True)
    is_deleted = db.Column(db.Boolean, default=False)

def add_workbook(user_id, data):
    if user_id is None:
        return {'error': 'User ID is required.'}, 400
    
    if not data:
        return {'error': 'Data is empty.'}, 400

    title = data.get('title')
    if not title:
        return {'error': 'Title is required.'}, 400

    try:
        new_workbook = Workbook(title=title, user_id=user_id)
        db.session.add(new_workbook)
        db.session.commit()
        return {'message': 'Workbook added successfully.'}, 200
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500
    

def register_pages(workbook_id, pages):
    try:
        workbook = Workbook.query.get(workbook_id, is_deleted=False)
        workbook.pages.extend(pages)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred while registering pages: {e}")
        return {'error': 'Internal server error.'}, 500


def get_all_workbooks(user_id):
    workbooks = Workbook.query.filter_by(user_id=user_id).all()
    if not workbooks:
        return [], 404

    workbooks_list = []
    for workbook in workbooks:
        if workbook.is_deleted == True:
            continue

        completed_page_ranges = get_completed_page_ranges(workbook.pages)
        workbook_data = {
            'id': workbook.id,
            'type': 'workbook',
            'title': workbook.title,
            'completed_page_ranges': completed_page_ranges,
        }
        workbooks_list.append(workbook_data)
    
    return json.dumps(workbooks_list), 200


def get_completed_page_ranges(pages):
    if not pages:
        return []
    
    # ページをnumberの昇順でソートする
    sorted_pages = sorted(pages, key=lambda x: x.number)
    
    completed_page_ranges = []

    previous_number = None
    start = None
    end = None

    # ソートされたページリストを反復処理
    for page in sorted_pages:
        number = page.number
        if not page.completed:
            # 完了していないページは無視する
            continue
        
        if previous_number is None:
            # 最初のページの場合、開始と終了の値を設定する
            previous_number = number
            start = number
            end = number
        elif number == previous_number + 1:
            # ページが連続している場合、範囲の終了値を更新する
            end = number
        else:
            # ページが連続していない場合、範囲をリストに追加し、新しい範囲を開始する
            completed_page_ranges.append([start, end])
            start = number
            end = number

        previous_number = number

    # 最後のページの範囲をリストに追加する
    if start is not None and end is not None:
        completed_page_ranges.append([start, end])

    return completed_page_ranges


def get_workbook_matching_user_id(user_id):
    workbooks = Workbook.query.filter_by(user_id=user_id, is_deleted=False).all()
    workbook_id = [workbook.id for workbook in workbooks]
    return workbook_id


def get_workbook_for_user(user_id, workbook_id):
    workbook = Workbook.query.filter_by(id=workbook_id, user_id=user_id).first()
    if workbook.is_deleted == True:
        return None
    
    return workbook


def get_assignments(user_id, workbook_id):
    workbook = get_workbook_for_user(user_id, workbook_id)

    if not workbook:
        return {'error': 'Workbook not found.'}, 404
    
    assignments = workbook.assignments
    return assignments


def db_delete_workbook(user_id, workbook_id):
    workbook_to_delete = get_workbook_for_user(user_id, workbook_id)

    if not workbook_to_delete:
        return {'error': 'Workbook not found.'}, 404

    try:
        assignments = get_assignments(user_id, workbook_id)

        for assignment in assignments:
            assignments.is_deleted = True
            ranges = assignment.assignment_page_ranges
            for r in ranges:
                r.is_deleted = True
        
        pages = workbook_to_delete.pages
        for page in pages:
            page.is_deleted = True

        workbook_to_delete.is_deleted = True
            
        db.session.commit()
        return {'message': 'Workbook deleted successfully.'}, 200
    except Exception as e:
        db.session.rollback()
        return {'error': f"Failed to delete workbook: {str(e)}"}, 500


'''
    error_response, status_code = validate_id(user_id, workbook_id)
    if error_response:
        return error_response, status_code
'''
def validate_id(user_id, workbook_id):
    if not user_id:
        return {'error': 'User ID is empty.'}, 400

    if not workbook_id:
        return {'error': 'Workbook ID is empty.'}, 400
    
    workbook = get_workbook_for_user(user_id, workbook_id)
    if not workbook:
        return {'error': 'User ID and workbook ID do not match.'}, 400

    return None, None