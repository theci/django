# hottrack/models.py

from __future__ import annotations

from datetime import date
from typing import Dict
from urllib.parse import quote

from django.db import models
from django.utils.html import format_html


class Song(models.Model):
    melon_uid = models.CharField(max_length=20, unique=True)
    rank = models.PositiveSmallIntegerField()
    album_name = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    artist_name = models.CharField(max_length=100)
    cover_url = models.URLField()
    lyrics = models.TextField()
    genre = models.CharField(max_length=100)
    release_date = models.DateField()
    like_count = models.PositiveIntegerField()

    @property
    def cover_image_tag(self):
        return format_html('<img src="{}" style="width: 50px;" />', self.cover_url)

    @property
    def melon_detail_url(self) -> str:
        melon_uid = quote(self.melon_uid)
        return f"https://www.melon.com/song/detail.htm?songId={melon_uid}"

    @property
    def youtube_search_url(self) -> str:
        search_query = quote(f"{self.name}, {self.artist_name}")
        return f"https://www.youtube.com/results?search_query={search_query}"


    # 이 메서드는 주어진 딕셔너리 데이터를 사용하여 Song 클래스의 인스턴스를 생성하는 팩토리 메서드입니다. 
    # cls 매개변수는 Song 클래스 자체를 참조하며, 이를 통해 클래스의 생성자를 호출하여 새 인스턴스를 생성합니다.
    @classmethod
    def from_dict(cls, data: Dict) -> Song:
        return cls(
            melon_uid=data.get("곡일련번호"),
            rank=int(data.get("순위")),
            album_name=data.get("앨범"),
            name=data.get("곡명"),
            artist_name=data.get("가수"),
            cover_url=data.get("커버이미지_주소"),
            lyrics=data.get("가사"),
            genre=data.get("장르"),
            release_date=date.fromisoformat(data.get("발매일")),
            like_count=int(data.get("좋아요")),
        )
