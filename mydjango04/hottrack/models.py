# hottrack/models.py

from __future__ import annotations

from datetime import date
from typing import Dict
from urllib.parse import quote

from django.conf import settings
from django.db import models
from django.db.models.functions import Upper
from django.urls import reverse
from django.utils.html import format_html
from django.utils.text import slugify


class Artist(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Album(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Upper("name"),
                name="hottrack_genre_name_unique",
            )
        ]


class Song(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    slug = models.SlugField(max_length=100, allow_unicode=True, blank=True)
    rank = models.PositiveSmallIntegerField()
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    cover_url = models.URLField()
    lyrics = models.TextField()
    genre_set = models.ManyToManyField(Genre, blank=True)

    release_date = models.DateField(verbose_name="발매일")
    like_count = models.PositiveIntegerField()

    class Meta:
        indexes = [
            models.Index(fields=["slug"]),
        ]

    def save(self, *args, **kwargs):
        self.slugify()
        super().save(*args, **kwargs)

    def slugify(self, force=False):
        if force or not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)

            slug_max_length = self._meta.get_field("slug").max_length
            self.slug = self.slug[:slug_max_length]

    def get_absolute_url(self) -> str:
        return reverse(
            "hottrack:song_detail",  # song_date_detail에서 변경
            args=[
                self.release_date.year,
                self.release_date.month,
                self.release_date.day,
                self.slug,
            ],
        )

    @property
    def cover_image_tag(self):
        return format_html('<img src="{}" style="width: 50px;" />', self.cover_url)

    @property
    def melon_detail_url(self) -> str:
        melon_uid = quote(str(self.id))
        return f"https://www.melon.com/song/detail.htm?songId={melon_uid}"

    @property
    def youtube_search_url(self) -> str:
        search_query = quote(f"{self.name}, {self.artist.name}")
        return f"https://www.youtube.com/results?search_query={search_query}"

    @classmethod
    def from_dict(cls, data: Dict) -> Song:
        instance = cls(
            id=data.get("곡일련번호"),
            rank=int(data.get("순위")),
            name=data.get("곡명"),
            cover_url=data.get("커버이미지_주소"),
            lyrics=data.get("가사"),
            release_date=date.fromisoformat(data.get("발매일")),
            like_count=int(data.get("좋아요")),
        )
        instance.slugify()
        return instance


class Comment(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hottrack_comment_set",
        related_query_name="hottrack_comment",
    )
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
