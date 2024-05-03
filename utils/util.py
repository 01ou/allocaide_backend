"""
Gather commonly used functions for your project in this folder. 
You can reuse these functions whenever you need to implement similar functionality. 
This practice reduces repetition in your code and enhances its maintainability.
このフォルダには、プロジェクト全体でよく使われる関数をまとめます。
同じ機能を再度実装する必要がある場合に、これらの関数を再利用できます。
これにより、コードの重複が減り、保守性が向上します。
"""

from datetime import datetime
import pytz


def range_to_list(start, end=None):
    """
    Convert a range of numbers to a list.

    Args:
        start (int): The starting number of the range.
        end (int, optional): The ending number of the range. If not provided, the range is considered to be from 0 to start.

    Returns:
        list: A list containing numbers from start to end (inclusive).
    """
    try:
        if end is None:
            end = start
            start = 0
        
        if start <= end:
            return list(range(start, end + 1))
        else:
            return list(range(start, end - 1, -1))
    except Exception as e:
        print(f'range_to_list Error: {e}')
        return []


def ranges_to_number_list(ranges):
    """
    Convert a list of ranges to a list of numbers.

    Args:
        ranges (list): A list of ranges, where each range is represented as a list containing two integers: [start, end].

    Returns:
        list: A list containing all the numbers from the provided ranges.
    """
    try:
        numbers = []
        for _range in ranges:
            numbers += range_to_list(_range[0], _range[1])
        return numbers
    except Exception as e:
        print(f'ranges_to_number_list Error: {e}')
        return []
    

def numbers_to_ranges(numbers):
    if not numbers:
        return []

    numbers.sort()
    ranges = []
    start = numbers[0]
    end = numbers[0]

    for i in range(1, len(numbers)):
        if numbers[i] == end + 1:
            end = numbers[i]
        else:
            ranges.append([start, end])
            start = numbers[i]
            end = numbers[i]

    ranges.append([start, end])

    return ranges
    

def get_ranges_length(ranges_array):
    total_length = 0
    error_message = None

    for _range in ranges_array:
        if len(_range) != 2:
            error_message = "Each range in the array must contain exactly two elements (start, end)."
            break

        start, end = _range
        if not isinstance(start, int) or not isinstance(end, int):
            error_message = "Start and end values in the range must be integers."
            break

        if start > end:
            error_message = "Start value cannot be greater than end value in a range."
            break

        length = end - start + 1
        if length < 0:
            error_message = "Invalid range: end value is less than start value."
            break

        total_length += length

    return total_length, error_message


def get_completed_fraction(incomplete_ranges_array, assignment_ranges_array):
    incomplete_length, incomplete_error = get_ranges_length(incomplete_ranges_array)
    assignment_length, assignment_error = get_ranges_length(assignment_ranges_array)

    if incomplete_error or assignment_error:
        return ''  # エラーがある場合は空の文字列を返す

    completed_length = assignment_length - incomplete_length
    return f'{completed_length}/{assignment_length}'


def remove_range_duplicates(range_array):
    range_array.sort(key=lambda x: x[0])  # 範囲リストを開始値でソートする

    merged_ranges = []

    for current_range in range_array:
        if not merged_ranges:  # 結果のリストが空の場合、現在の範囲を追加
            merged_ranges.append(current_range)
        else:
            last_merged_range = merged_ranges[-1]
            # 現在の範囲と前の結合された範囲を比較し、重なっているかどうかを確認
            if current_range[0] <= last_merged_range[1] + 1:
                # 重なっている場合は、範囲を結合する
                merged_ranges[-1] = [last_merged_range[0], max(last_merged_range[1], current_range[1])]
            else:
                # 重なっていない場合は、新しい範囲として追加
                merged_ranges.append(current_range)

    return merged_ranges


def get_now_tokyo_time():
    # UTCの現在時刻を取得
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

    # UTC時刻を東京のタイムゾーンに変換
    tokyo_timezone = pytz.timezone('Asia/Tokyo')
    now_tokyo = now_utc.astimezone(tokyo_timezone)
    
    return now_tokyo


def convert_to_isoformat(datetime_obj):
    try:
        if datetime_obj:
            return datetime_obj.isoformat()
        else:
            return None
    except AttributeError:
        # datetime_obj が datetime オブジェクトでない場合のエラーハンドリング
        return None


def is_not_empty(value):
    """
    値が空でないかどうかをチェックする関数。

    :param value: チェックする値
    :return: 空でない場合はTrue、空の場合はFalse
    """
    if value is None:
        return False
    elif isinstance(value, str) and value.strip() == '':
        return False
    elif isinstance(value, (list, dict)) and len(value) == 0:
        return False
    elif isinstance(value, dict) and len(value.keys()) == 0:
        return False
    else:
        return True
