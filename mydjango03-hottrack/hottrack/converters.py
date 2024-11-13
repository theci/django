# hottrack/converters.py

from datetime import date
from django.urls import register_converter


class DateConverter:
    # year: 2000 ~ 2099
    # month: 1, 2, 3, 4, 5, 6, 7, 8, 9, 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12
    # day : 1, 2, 3, .. 9, 01, 02, 03, .. 09, 10, 11, 12, .. 30, 31
    # 이 정규식은 날짜 형식(YYYY/MM/DD)을 유효한 값만 받도록 설정
    regex = r"20\d{2}/([1-9]|0[1-9]|1[0-2]){1,2}/([1-9]|0[1-9]|[12][0-9]|3[01]){1,2}"
    # regex = r"\d{4}/\d{1,2}/\d{1,2}"

    def to_python(self, value: str) -> date: # URL에서 전달받은 문자열(value)을 date 객체로 변환. ex) 2023/09/08 -> date(2023, 9, 8)
        year, month, day = map(int, value.split("/"))
        return date(year, month, day)

    def to_url(self, value: date) -> str: # date 객체를 URL 형식으로 변환. ex) date(2023, 9, 8) -> 2023/09/08 
        return f"{value.year}/{value.month:02d}/{value.day:02d}"


# Django에 DateConverter 등록
register_converter(DateConverter, "date")
# DateConverter를 Django에 등록하여, URL 경로에서 date 형식을 사용할 수 있도록 만듭니다. 
# path(route="archives/<date:release_date>/")와 같은 URL 패턴에서 release_date가 DateConverter에 의해 날짜로 변환됩니다.


