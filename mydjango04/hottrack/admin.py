from django.contrib import admin
from django.utils.html import format_html

from .filters import ReleaseDateFilter
from .models import Song
from .utils.melon import get_likes_dict


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    search_fields = ["name", "artist__name", "album__name"]  # where
    list_display = [
        "cover_image_tag",
        "name",
        "artist",
        "album",
        "genre_html",
        "like_count",
        "release_date",
    ]
    list_filter = ["genre_set", ReleaseDateFilter]
    actions = ["update_like_count"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # def has_view_permission(self, request, obj=None):
    #     return super().has_view_permission(request, obj)

    # genre_html 메서드의 genre_set M2M 메서드 쿼리셋을 위해
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.prefetch_related("genre_set")
        return qs

    @admin.display(description="장르")
    def genre_html(self, song):
        genre_qs = song.genre_set.all()
        return ", ".join(genre.name for genre in genre_qs)

    def update_like_count(self, request, queryset):
        melon_uid_list = queryset.values_list("id", flat=True)
        likes_dict = get_likes_dict(melon_uid_list)

        changed_count = 0
        for song in queryset:
            if song.like_count != likes_dict.get(song.id):
                song.like_count = likes_dict.get(song.id)
                # song.save()  # 모델의 모든 필드에 대해서 업데이트를 수행
                # song.save(update_fields=["like_count"])
                changed_count += 1

        Song.objects.bulk_update(
            queryset,
            fields=["like_count"],
        )

        self.message_user(request, f"{changed_count} 곡의 좋아요 갱신 완료")

    # @staticmethod
    # def cover_image(song):
    #     return format_html('<img src="{}" style="width: 50px;" />', song.cover_url)
