from datetime import datetime
from datetime import timezone
from datetime import timedelta
from hashlib import sha1


SHA_TZ = timezone(
    timedelta(hours=8),
    name="Asia/Shanghai",
)


def number_format(number):
    return "{:,}".format(number)


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


def get_bj_day_time():
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(hours=11)
    beijing_now = utc_now.astimezone(SHA_TZ)
    _bj = beijing_now.strftime("%Y-%m-%d %H:%M:%S")  # 结果显示：'2017-10-07'

    return _bj
