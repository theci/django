from typing import Optional, List

from django.contrib import admin
from django.db.models.functions import ExtractYear
from django.utils import timezone

from hottrack.models import Song

# Django Admin의 리스트 페이지에서 곡들을 발매일 기준으로 편리하게 필터링하는 클래스
class ReleaseDateFilter(admin.SimpleListFilter):
    title = Song._meta.get_field("release_date").verbose_name # 필터의 제목을 release_date 필드의 verbose_name("발매일")로 설정
    parameter_name = "release_date_filter"

     # 필터링 옵션을 제공하는 함수
    def lookups(self, request, model_admin):
        year_list: List[int] = (
            Song.objects.annotate(year=ExtractYear("release_date")) # Song 모델의 release_date 필드를 기준으로 연도별 목록을 가져옴
            .values_list("year", flat=True)
            .order_by("-year")
            .distinct()
        )

        fixed_lookups = [ # 고정된 필터 항목을 정의
            ("this_month", "이번 달"),
        ]

        dynamic_lookups = [(year, f"{year}년") for year in year_list] # 동적으로 생성되는 필터 항목

        return fixed_lookups + dynamic_lookups
    
    # 필터링이 적용된 쿼리셋을 반환하는 함수
    def queryset(self, request, queryset):
        value: Optional[str] = self.value() # 사용자가 선택한 필터 옵션을 가져옵니다.

        if value == "this_month":
            now = timezone.now()
            return queryset.filter( # release_date의 연도와 월이 현재 연도와 월과 일치하는 곡들만 필터링하여 반환
                release_date__year=now.year,
                release_date__month=now.month,
            )
        elif value is not None: # release_date의 연도의 경우 현재 연도인 곡들만 필터링하여 반환
            return queryset.filter(release_date__year=value)

        return queryset
