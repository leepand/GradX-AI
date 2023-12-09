from datetime import datetime
from datetime import timezone
from datetime import timedelta
from hashlib import sha1
import os

import sqlite3
import streamlit as st

SHA_TZ = timezone(
    timedelta(hours=8),
    name="Asia/Shanghai",
)


def number_format(number):
    return "{:,}".format(number)


def get_file_size(file_path):
    # 获取文件大小（以字节为单位）
    file_size = os.path.getsize(file_path)
    print("文件大小（字节）:", file_size)

    # 获取文件大小（以可读格式显示）
    file_size_readable = os.path.getsize(file_path)
    size_suffixes = ["B", "KB", "MB", "GB", "TB"]
    index = 0
    while file_size_readable >= 1024 and index < len(size_suffixes) - 1:
        file_size_readable /= 1024
        index += 1
    file_size_readable = f"{file_size_readable:.2f} {size_suffixes[index]}"
    return file_size_readable


def get_week_day():
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(hours=11)
    beijing_now = utc_now.astimezone(SHA_TZ)

    return beijing_now.weekday()


def get_bj_day():
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(hours=11)
    beijing_now = utc_now.astimezone(SHA_TZ)
    _bj = beijing_now.strftime("%Y-%m-%d")  # 结果显示：'2017-10-07'

    return _bj


def get_yestoday_bj():
    current_date = get_bj_day()  # '2023-07-11'
    date_format = "%Y-%m-%d"
    current_datetime = datetime.strptime(current_date, date_format)
    previous_datetime = current_datetime - timedelta(days=1)
    previous_date = previous_datetime.strftime(date_format)
    return previous_date


def get_lastn_date_bj(n):
    current_date = get_bj_day()  # '2023-07-11'
    date_format = "%Y-%m-%d"
    current_datetime = datetime.strptime(current_date, date_format)
    previous_datetime = current_datetime - timedelta(days=n)
    previous_date = previous_datetime.strftime(date_format)
    return previous_date


def get_bj_day_time():
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(hours=11)
    beijing_now = utc_now.astimezone(SHA_TZ)
    _bj = beijing_now.strftime("%Y-%m-%d %H:%M:%S")  # 结果显示：'2017-10-07'

    return _bj


def safe_div(a, b):
    """Returns a if b is nil, else divides a by b.
    When scaling, sometimes a denominator might be nil. For instance, during standard scaling
    the denominator can be nil if a feature has no variance.
    """
    return a / b if b else 0.0


def create_connection(db_file):
    """create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        print("error connecting to db")
        st.write(e)

    return conn
