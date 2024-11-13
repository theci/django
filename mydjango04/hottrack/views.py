import datetime
import json
from io import BytesIO
from typing import Literal
from urllib.request import urlopen

import pandas as pd
from django.conf import settings

from django.db.models import QuerySet, Q
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.views.generic import (
    DetailView,
    ListView,
    YearArchiveView,
    MonthArchiveView,
    DayArchiveView,
    TodayArchiveView,
    WeekArchiveView,
    ArchiveIndexView,
    DateDetailView,
)

from hottrack.models import Song
from hottrack.utils.cover import make_cover_image

# Song 모델의 데이터를 가져와서 필터링하고 페이징 처리하여 hottrack/index.html 템플릿에 전달
class IndexView(ListView):
    model = Song
    template_name = "hottrack/index.html"
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset() # 부모 클래스인 ListView의 get_queryset 메서드를 호출하여 기본 쿼리셋을 가져옵니다. 기본적으로 Song.objects.all()을 반환

        # self.kwargs는 URL에서 전달된 동적 매개변수들을 담고 있는 딕셔너리
        release_date = self.kwargs.get("release_date") # URL에서 전달된 release_date라는 동적 URL 매개변수를 가져옵니다
        if release_date:
            qs = qs.filter(release_date=release_date)

        query = self.request.GET.get("query", "").strip() # URL의 GET 파라미터에서 query 값을 가져옵니다. "query"는 사용자가 검색어를 입력한 값
        if query:
            qs = qs.filter(
                Q(name__icontains=query)
                | Q(artist__name__icontains=query)
                | Q(album__name__icontains=query)
            )

        # 데이터베이스 쿼리 최적화 기법으로, Song 모델과 관련된 artist 모델을 한 번의 쿼리로 미리 가져옵니다. 
        # 이는 Song 객체를 가져올 때, 관련된 artist 정보를 별도의 쿼리 없이 미리 로드하여 N+1 쿼리 문제를 방지
        # 즉, 각 Song 객체에 대한 artist 정보를 가져오는 데 필요한 추가적인 데이터베이스 쿼리가 없어집니다.
        qs = qs.select_related("artist")

        return qs # 이 쿼리셋은 템플릿에 전달되어, hottrack/index.html에서 렌더링


index = IndexView.as_view() # IndexView 클래스 기반 뷰를 호출 가능한 뷰 함수로 변환합니다. 이 함수는 실제로 URL과 연결될 수 있으며, 해당 URL로 요청이 들어올 때 IndexView가 처리하게 됩니다.



# def index(request: HttpRequest, release_date: datetime.date = None) -> HttpResponse:
#     query = request.GET.get("query", "").strip()
#
#     song_qs: QuerySet[Song] = Song.objects.all()
#
#     if release_date:
#         song_qs = song_qs.filter(release_date=release_date)
#
#     if query:
#         song_qs = song_qs.filter(
#             Q(name__icontains=query)
#             | Q(artist__name__icontains=query)
#             | Q(album__name__icontains=query)
#         )
#
#     return render(
#         request=request,
#         template_name="hottrack/index.html",
#         context={
#             "song_list": song_qs,
#             "query": query,
#         },
#     )


class SongDetailView(DetailView):
    model = Song

    # Song 모델에서 melon_uid 필드를 id 기본키로 변경했기에 melon_uid 인자 지원이 필요없어졌습니다.


song_detail = SongDetailView.as_view()

# 데이터를 CSV 또는 XLSX 형식으로 파일로 다운로드할 수 있게 해주는 뷰
def export(request, format: Literal["csv", "xlsx"]):
    song_qs = Song.objects.all()
    df = pd.DataFrame(data=song_qs.values())

    export_file = BytesIO() # 이 객체를 사용하여 파일 내용을 메모리에서 생성하여 바이트 스트림을 처리하고 이를 HTTP 응답으로 반환

    if format == "csv":
        content_type = "text/csv"
        filename = "hottrack.csv"
        df.to_csv(path_or_buf=export_file, index=False, encoding="utf-8-sig")
    elif format == "xlsx":
        content_type = "application/vnd.ms-excel"
        filename = "hottrack.xlsx"
        df.to_excel(excel_writer=export_file, index=False)
    else:
        return HttpResponseBadRequest(f"Invalid format : {format}")

    response = HttpResponse(content=export_file.getvalue(), content_type=content_type) # export_file.getvalue()로 메모리에 생성된 파일을 응답 본문에 담습니다.
    response["Content-Disposition"] = 'attachment; filename="{}"'.format(filename) # Content-Disposition 헤더를 사용하여 브라우저가 해당 파일을 다운로드하도록 지정

    return response


def cover_png(request, pk):
    # 최대값 512, 기본값 256
    canvas_size = min(512, int(request.GET.get("size", 256)))

    song = get_object_or_404(Song, pk=pk)

    cover_image = make_cover_image(
        song.cover_url, song.artist.name, canvas_size=canvas_size
    )

    # param fp : filename (str), pathlib.Path object or file object
    # image.save("image.png")
    response = HttpResponse(content_type="image/png")
    cover_image.save(response, format="png")

    return response


class SongYearArchiveView(YearArchiveView):
    model = Song
    date_field = "release_date"  # 조회할 날짜 필드
    make_object_list = True


class SongMonthArchiveView(MonthArchiveView):
    model = Song
    # paginate_by = None
    date_field = "release_date"
    # 날짜 포맷 : "%m" (숫자, ex: "01", "1" 등), "%b" (디폴트, 월 이름의 약어, ex: "Jan", "Feb" 등)
    month_format = "%m"


class SongDayArchiveView(DayArchiveView):
    model = Song
    date_field = "release_date"
    month_format = "%m"


class SongTodayArchiveView(TodayArchiveView):
    model = Song
    date_field = "release_date"

    if settings.DEBUG:

        def get_dated_items(self):
            """지정 날짜의 데이터를 조회"""
            fake_today = self.request.GET.get("fake-today", "")
            try:
                year, month, day = map(int, fake_today.split("-", 3)) # fake-today 값에서 연도, 월, 일을 추출하여 정수형으로 변환
                return self._get_dated_items(datetime.date(year, month, day)) # 이를 datetime.date 객체로 변환하여 날짜를 생성
            except ValueError:
                # fake_today 파라미터가 없거나 날짜 형식이 잘못되었을 경우
                return super().get_dated_items()


class SongWeekArchiveView(WeekArchiveView):
    model = Song
    date_field = "release_date"
    # date_list_period = "week"
    # 템플릿 필터 date의 "W" 포맷은 ISO 8601에 따라 한 주의 시작을 월요일로 간주합니다.
    #  - 템플릿 단에서 한 주의 시작을 일요일로 할려면 커스텀 템플릿 태그 구현이 필요합니다.
    week_format = "%W"  # "%U" (디폴트, 한 주의 시작을 일요일), %W (한 주의 시작을 월요일)


class SongArchiveIndexView(ArchiveIndexView):
    model = Song
    # queryset = Song.objects.all()
    date_field = "release_date"  # 기준 날짜 필드
    paginate_by = 10  # 페이지 당 출력할 객체 수

    # date_list_period = "year"  # 단위 : year (디폴트), month, day, week
    def get_date_list_period(self):
        # URL Captured Value에 date_list_period가 없으면, date_list_period 속성을 활용합니다.
        return self.kwargs.get("date_list_period", self.date_list_period)

    # 이 메서드는 템플릿에 전달할 추가 데이터를 설정하는 메서드
    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["date_list_period"] = self.get_date_list_period() # 부모클래스에서 기본 데이터를 가져오고, 여기에 date_list_period 값을 추가하여 반환
        return context_data


class SongDateDetailView(DateDetailView):
    model = Song
    date_field = "release_date"
    month_format = "%m"
