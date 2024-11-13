from django.contrib import admin
from django.utils.html import format_html

from .models import Song
from .utils.melon import get_likes_dict


@admin.register(Song)   # 데코레이터를 통해 Song 모델을 Django admin에 등록
class SongAdmin(admin.ModelAdmin):
    search_fields = ["name", "artist_name", "album_name"]  # 검색 기능에서 사용할 필드를 설정
    list_display = [ # 관리 페이지에서 보여줄 필드를 설정
        "cover_image_tag",
        "name",
        "artist_name",
        "album_name",
        "genre",
        "like_count",
        "release_date",
    ]
    list_filter = ["genre", "release_date"] # 장르와 발매일로 필터링할 수 있도록 설정
    actions = ["update_like_count"] # 선택된 항목에 대해 수행할 수 있는 함수 정의

    def update_like_count(self, request, queryset):
        melon_uid_list = queryset.values_list("melon_uid", flat=True) # 선택된 곡들의 melon_uid를 가져와서, 해당 곡들의 좋아요 수를 업데이트
        likes_dict = get_likes_dict(melon_uid_list)   # get_likes_dict 함수를 사용하여 각 곡의 melon_uid에 대한 좋아요 수를 가져옵니다.

        changed_count = 0
        for song in queryset:
            if song.like_count != likes_dict.get(song.melon_uid):
                song.like_count = likes_dict.get(song.melon_uid)
                # song.save()  # 모델의 모든 필드에 대해서 업데이트를 수행
                # song.save(update_fields=["like_count"])
                changed_count += 1

        Song.objects.bulk_update( # song.save() 대신 bulk_update를 사용하여 여러 곡의 like_count를 한 번에 업데이트
            queryset,
            fields=["like_count"],
        )

        self.message_user(request, f"{changed_count} 곡의 좋아요 갱신 완료")

    # @staticmethod
    # def cover_image(song):
    #     return format_html('<img src="{}" style="width: 50px;" />', song.cover_url)
