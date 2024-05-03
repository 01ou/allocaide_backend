import re


def validate_password(password):
    # 1. パスワードの長さが8文字以上であることを検証
    if len(password) < 8:
        return False, 'Password must be at least 8 characters long.', 400

    # 2. 使用できる文字の範囲を定義（英数字と一部の特殊文字）
    pattern = re.compile(r'^[A-Za-z0-9@#$%^&+=\-*]+$')
    
    # パスワードが指定されたパターンに一致するかどうかを検証
    if not pattern.match(password):
        return False, 'Please use only alphanumeric characters and @ # $ % ^ & + = - *', 400

    # 3. 英語大文字、英語小文字、数字、記号がすべて入っているかを検証
    has_upper = any(char.isupper() for char in password)
    has_lower = any(char.islower() for char in password)
    has_digit = any(char.isdigit() for char in password)
    has_symbol = any(char in '@#$%^&+=-*' for char in password)

    if not (has_upper and has_lower and has_digit and has_symbol):
        return False, 'Passwords must contain uppercase and lowercase letters, numbers, and symbols.', 400

    return True, None, 200


def validate_range_format(range_data):
    """
    Check if the format of each range item in range_data is valid.
    If invalid format is found, return error_response and status_code.
    """
    # range_dataがリストであることを確認
    if not isinstance(range_data, list):
        return {'error': 'Range data must be a list.'}, 400

    for range_item in range_data:
        if not isinstance(range_item, dict) or 'start' not in range_item or 'end' not in range_item:
            return {'error': 'Each range item must be a dictionary with keys "start" and "end".'}, 400
        if not isinstance(range_item['start'], int) or not isinstance(range_item['end'], int):
            return {'error': 'Start and end values of each range must be integers.'}, 400
        if range_item['start'] > range_item['end']:
            return {'error': 'Start value must be less than end value for each range.'}, 400
    return None, None


def ranges_data_to_ranges_list(ranges_data):
    try:
        return [[page_range.start, page_range.end] for page_range in ranges_data]
    except Exception as e:
        print(f'models.assignment_model.ranges_data_to_ranges_list Error: {e}')
        return []


def dict_to_range_list(ranges_dict):
    try:
        return [[range_dict['start'], range_dict['end']] for range_dict in ranges_dict]
    except Exception as e:
        print(f'models.assignment_model.ranges_data_to_ranges_list Error: {e}')
        return []