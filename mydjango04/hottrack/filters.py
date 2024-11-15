from typing import Optional, List

from django.contrib import admin
from django.db.models.functions import ExtractYear
from django.utils import timezone

from hottrack.models import Song

# Django Admin의 리스트 페이지에서 곡들을 발매일 기준으로 편리하게 필터링하는 클래스
# admin.SimpleListFilter는 Django Admin에서 리스트 필터링을 위한 간단한 방법을 제공하는 클래스입니다.
class ReleaseDateFilter(admin.SimpleListFilter):
    title = Song._meta.get_field("release_date").verbose_name # 필터의 제목을 release_date 필드의 verbose_name("발매일")로 설정
    parameter_name = "release_date_filter" # URL에서 필터의 매개변수 이름을 정의합니다. 이 경우 release_date_filter라는 이름으로 URL에 필터를 적용합니다.

     # 필터링 옵션을 제공하는 함수
    def lookups(self, request, model_admin):
        year_list: List[int] = (
            Song.objects.annotate(year=ExtractYear("release_date")) # release_date 필드에서 연도만 추출하여 year라는 별칭을 부여합니다.
            .values_list("year", flat=True) # year 값만 가져옵니다.
            .order_by("-year") # 연도를 내림차순으로 정렬하여 가장 최근 연도부터 시작합니다.
            .distinct() #  중복된 연도는 제거합니다.
        )

        fixed_lookups = [ # 고정된 필터 항목을 정의
            ("this_month", "이번 달"),
        ]

        dynamic_lookups = [(year, f"{year}년") for year in year_list] # year_list에서 가져온 연도 목록을 바탕으로 동적으로 필터 항목을 생성. 예를 들어, 2023년, 2022년 등의 항목을 만들어 필터 옵션으로 추가합니다.

        return fixed_lookups + dynamic_lookups # fixed_lookups와 dynamic_lookups를 합쳐서 필터의 옵션 목록을 반환합니다.
    
    # 필터링이 적용된 쿼리셋을 반환하는 함수
    def queryset(self, request, queryset):
        value: Optional[str] = self.value() # 사용자가 선택한 필터 옵션의 값을 가져옵니다. self.value()를 사용하여 필터 값(this_month 또는 연도)을 가져옵니다.

        if value == "this_month": # 사용자가 "이번 달"을 선택한 경우입니다. timezone.now()로 현재 날짜와 시간을 가져오고, 이를 기반으로 이번 달에 발매된 곡들을 필터링합니다.
            now = timezone.now()
            return queryset.filter( # release_date의 연도와 월이 현재 연도와 월과 일치하는 곡들만 필터링하여 반환
                release_date__year=now.year,
                release_date__month=now.month,
            )
        elif value is not None: # release_date의 연도의 경우 현재 연도인 곡들만 필터링하여 반환
            return queryset.filter(release_date__year=value)

        return queryset # 선택된 필터 값이 없거나, 기본 상태일 경우에는 필터링을 하지 않고 원본 쿼리셋을 그대로 반환합니다.
