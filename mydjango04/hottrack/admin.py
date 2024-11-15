from django.contrib import admin
from django.utils.html import format_html

from .filters import ReleaseDateFilter
from .models import Song
from .utils.melon import get_likes_dict


@admin.register(Song) # @admin.register(Song)는 Song 모델에 대해 SongAdmin 클래스를 등록하는 데 사용됩니다. Song 모델을 Django 관리자(Admin) 사이트에서 관리할 수 있도록 연결하는 역할
class SongAdmin(admin.ModelAdmin):
    search_fields = ["name", "artist__name", "album__name"]  # search_fields는 Django 관리자에서 검색 기능을 정의하는 부분입니다.
    list_display = [ # list_display는 Django 관리자가 곡 목록을 표시할 때 각 행에 표시할 필드를 정의합니다
        "cover_image_tag",
        "name",
        "artist",
        "album",
        "genre_html",
        "like_count",
        "release_date",
    ]
    list_filter = ["genre_set", ReleaseDateFilter] # genre_set(장르)과 ReleaseDateFilter(발매일 필터)를 사용하여, 관리자가 곡들을 필터링할 수 있게 합니다.
    actions = ["update_like_count"] # actions는 선택한 항목에 대해 관리자가 실행할 수 있는 작업으로 선택된 곡들의 좋아요 수를 업데이트하는 작업입니다.


    # 이 메서드들은 관리자가 곡을 추가, 변경, 삭제할 수 있는지에 대한 권한을 설정
    def has_add_permission(self, request): # 곡을 추가할 수 없게 설정.
        return False

    def has_change_permission(self, request, obj=None): # 곡을 수정할 수 없게 설정.
        return False

    def has_delete_permission(self, request, obj=None): # 곡을 삭제할 수 없게 설정.
        return False

    # def has_view_permission(self, request, obj=None):
    #     return super().has_view_permission(request, obj)

    # 관리자 페이지에서 표시할 쿼리셋을 정의하는 메서드
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.prefetch_related("genre_set") # 장르와 관계가 있는 genre_set을 미리 가져오도록 하여, 쿼리 성능을 최적화하는 역할을 합니다.. prefetch_related는 M2M(다대다) 관계를 처리할 때 성능을 개선하는 데 유용합니다.
        return qs

    @admin.display(description="장르")
    def genre_html(self, song): # genre_html 메서드는 곡의 장르를 HTML 형식으로 반환합니다.
        genre_qs = song.genre_set.all()
        return ", ".join(genre.name for genre in genre_qs) # 장르 이름들을 쉼표로 구분한 문자열로 반환합니다.

    # 관리자에서 선택한 곡들의 좋아요 수를 업데이트하는 메서드
    def update_like_count(self, request, queryset): 
        melon_uid_list = queryset.values_list("id", flat=True) # 선택된 곡들의 id를 리스트로 가져옵니다. flat의 역할은 튜플이 아닌 리스트로 필드의 값을 반환하는 것
        likes_dict = get_likes_dict(melon_uid_list) # get_likes_dict 함수로 멜론에서 각 곡의 좋아요 수를 가져옵니다. melon_uid_list는 곡들의 멜론 ID 리스트입니다.

        changed_count = 0
        for song in queryset:
            if song.like_count != likes_dict.get(song.id):
                song.like_count = likes_dict.get(song.id)
                # song.save()  # 모델의 모든 필드에 대해서 업데이트를 수행
                # song.save(update_fields=["like_count"])
                changed_count += 1

        Song.objects.bulk_update( # 곡들의 좋아요 수(like_count)가 업데이트되어야 할 경우, bulk_update를 사용하여 배치 방식으로 한 번에 업데이트합니다.
            queryset,
            fields=["like_count"],
        )

        self.message_user(request, f"{changed_count} 곡의 좋아요 갱신 완료") # 관리자는 changed_count에 따라 갱신된 곡의 수를 메시지로 표시합니다.

    # @staticmethod
    # def cover_image(song):
    #     return format_html('<img src="{}" style="width: 50px;" />', song.cover_url)
