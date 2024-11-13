from django.urls import path, re_path
from . import converters  # noqa
from . import views

urlpatterns = [
    path(route="", view=views.index),
    path(route="archives/<date:release_date>/", view=views.index), # release_date는 date 형식의 URL 변환기를 사용하여 날짜를 파싱
    re_path(route=r"^export\.(?P<format>(csv|xlsx))$", view=views.export), # export.csv 또는 export.xlsx와 같은 URL을 처리, format이라는 이름의 URL 파라미터가 csv 또는 xlsx 값만 받을 수 있도록 제한
    path(route="<int:pk>/cover.png", view=views.cover_png), # pk라는 이름의 정수 형식 URL 파라미터를 받아 해당 pk에 맞는 커버 이미지를 cover.png로 반환하는 뷰 cover_png로 연결
]
