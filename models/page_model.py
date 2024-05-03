from ..utils.util import range_to_list, ranges_to_number_list, remove_range_duplicates
from ..utils.util import numbers_to_ranges
from ..models.workbook_model import validate_id, register_pages
from ..extensions import db
from sqlalchemy.exc import SQLAlchemyError


class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    workbook_id = db.Column(db.Integer, db.ForeignKey('workbook.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.UniqueConstraint('number', 'workbook_id', name='_number_workbook_uc'),
    )


def set_completed_state_by_ranges(user_id, workbook_id, ranges_data):
    try:
        error_response, status_code = validate_id(user_id, workbook_id)
        if error_response:
            return error_response, status_code
        
        combined_ranges = remove_range_duplicates(ranges_data)
        numbers = ranges_to_number_list(combined_ranges)
        
        new_pages = []
        for number in numbers:
            page = Page.query.filter_by(number=number, workbook_id=workbook_id, is_deleted=False).first()
            if page:
                page.completed = True
            else:
                new_page = Page(number=number, completed=True, workbook_id=workbook_id)
                new_pages.append(new_page)
                db.session.add(new_page)
        
        db.session.commit()

        register_pages(workbook_id, new_pages)

        return {'message': 'Page set completed successfully.'}, 200
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"SQLAlchemyError occurred: {e}")
        return {'error': 'Database error.'}, 500
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred: {e}")
        return {'error': 'Internal server error.'}, 500

    

def get_completed_page_percentage(assignment):
    """
    Calculate the percentage of completed pages among the assignment's page ranges.
    """
    total_pages = 0
    completed_pages = 0

    for page_range in assignment.assignment_page_ranges:
        # ページ範囲内の全ページ数を計算
        if page_range.is_deleted == True:
            continue

        total_pages += page_range.end - page_range.start + 1
        
        # ページ範囲内の完了したページ数を計算
        completed_pages += Page.query.filter(
            Page.number >= page_range.start,
            Page.number <= page_range.end,
            Page.workbook_id == assignment.workbook_id,
            Page.completed == True,  # 完了したページのみをカウント
        ).count()

    if total_pages == 0:
        return 0  # ゼロ割を防ぐためにガード節を追加
    
    # 完了したページの割合を計算して返す
    return (completed_pages / total_pages) * 100


def get_incomplete_page_ranges(assignment):
    """
    課題範囲のうち、未完了のページの範囲リストを作成します。
    具体的には未完了ページが連続している、開始番号と終了番号の組み合わせのリストです。
    課題範囲外では連続が途切れます。
    """
    # もし課題が存在しない場合や課題範囲が空の場合は空リストを返す
    
    if not assignment or not assignment.assignment_page_ranges:
        return []

    # 課題に関連するすべてのページ範囲を取得し、開始番号で昇順に並べ替える
    page_ranges = sorted(assignment.assignment_page_ranges, key=lambda x: x.start)

    incomplete_numbers = []

    for page_range in page_ranges:
        if page_range.is_deleted == True:
            continue

        for page_number in range(page_range.start, page_range.end + 1):
            page = Page.query.filter_by(number=page_number, workbook_id=assignment.workbook_id, is_deleted=False).first()
            is_incomplete = page is None or not page.completed
            if is_incomplete:
                incomplete_numbers.append(page_number)

    incomplete_ranges = numbers_to_ranges(incomplete_numbers)

    return incomplete_ranges
