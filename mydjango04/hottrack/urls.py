from django.urls import path, re_path
from . import converters  # noqa
from . import views

app_name = "hottrack"

urlpatterns = [
    path(route="", view=views.index, name="index"),
    path(route="<int:pk>/", view=views.song_detail, name="song_detail"),
    # Song 모델에서 melon_uid 필드를 id 기본키로 변경했기에 melon_uid 인자 지원이 필요없어졌습니다.
    re_path(
        route=r"^export\.(?P<format>(csv|xlsx))$", view=views.export, name="export"
    ),
    path(route="<int:pk>/cover.png", view=views.cover_png, name="cover_png"),
    path(
        route="archives/<int:year>/",
        view=views.SongYearArchiveView.as_view(),
        name="song_archive_year",
    ),
    path(
        route="archives/<int:year>/<int:month>/",
        view=views.SongMonthArchiveView.as_view(),
        name="song_archive_month",
    ),
    path(
        route="archives/<int:year>/<int:month>/<int:day>/",
        view=views.SongDayArchiveView.as_view(),
        name="song_archive_day",
    ),
    path(
        route="archives/today/",
        view=views.SongTodayArchiveView.as_view(),
        name="song_archive_today",
    ),
    path(
        route="archives/<int:year>/week/<int:week>/",
        view=views.SongWeekArchiveView.as_view(),
        name="song_archive_week",
    ),
    re_path(
        route=r"^archives/(?P<date_list_period>year|month|day|week)?/?$",
        view=views.SongArchiveIndexView.as_view(),
        name="song_archive_index",
    ),
    re_path(
        route=r"^(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<slug>[-\w]+)/$",
        view=views.SongDateDetailView.as_view(),
        name="song_detail",  # 앞서 위치한 song_detail과 같은 이름이지만, 인자 구성이 다릅니다.
    ),
]
