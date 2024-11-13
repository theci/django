# Django에서 모든 모델에 대한 메타 정보를 저장하는 라이브러리
from django.contrib.contenttypes.fields import (GenericForeignKey,
                                                GenericRelation)
# enericForeignKey - content_type 필드(어떤 모델인지를 나타냄)와 object_id 필드(어떤 객체인지를 나타냄)를 함께 사용하여 특정 객체를 가리킵니다.
# GenericRel - 특정 객체가 자신과 관련된 여러 개의 GenericForeignKey 객체들을 조회할 수 있게 해줍니다.
# GenericRelation - 주어진 객체가 다른 모델들에 의해 참조되는 관계를 조회할 수 있게 해줍니다.

from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.urls import reverse


class Post(models.Model):
    class Status(models.TextChoices): # 게시글의 상태를 정의하는 열거형
        DRAFT = "D", "초안"
        PUBLISHED = "P", "발행"

    title = models.CharField(max_length=100)
    content = models.TextField(blank=True)
    status = models.CharField(
        max_length=1, choices=Status.choices, default=Status.DRAFT
    )
    photo = models.ImageField(blank=True)
    is_public = models.BooleanField(default=False)
    created_date = models.DateField(auto_now_add=True)

    ip = models.GenericIPAddressField() # 게시글 작성자의 IP 주소를 저장하는 필드

    # Generic Relation에서는 1측에 관계를 정의하므로, 모델 클래스에 직접적으로 필드를 정의
    # 이 필드명으로 Comment에 대한 related_name, related_query_name 역할을 같이 수행
    comment_set = GenericRelation(to="Comment", related_query_name="post")

    tag_set = models.ManyToManyField( # 게시글과 관련된 태그를 관리하는 다대다 관계입니다. blog.Tag 모델과 연결
        "blog.Tag",
        blank=True,
        related_name="weblog_post_set",
        related_query_name="weblog_post",
    )

    def get_absolute_url(self) -> str: # 게시글의 상세 페이지 URL을 반환
        return reverse("weblog:post_detail", args=[self.pk]) # reverse를 사용하여 URL을 동적으로 생성


@receiver(pre_delete, sender=Post) # Post 모델 인스턴스가 삭제되기 전에 호출되는 함수
def set_value_or_delete(sender, instance: Post, **kwargs):
    instance.comment_set.update(object_id=5)


class Article(models.Model): # Article 모델은 블로그의 다른 유형의 게시글을 나타냅니다
    title = models.CharField(max_length=100)
    comment_set = GenericRelation(to="Comment", related_query_name="article") # Comment 모델과의 제네릭 관계를 정의


class Comment(models.Model):
    content_type = models.ForeignKey(to=ContentType, on_delete=models.CASCADE) # ContentType 모델은 Django의 내장 모델로, 다른 모델들의 "유형"을 관리합
    object_id = models.PositiveIntegerField() # object_id 필드는 content_type이 참조하는 객체의 ID를 저장하는 필드. 양의 정수만 허용
    # on_delete 옵션을 지원하지 않습니다. CASCADE 정책으로만 동작합니다.
    content_object = GenericForeignKey(ct_field="content_type", fk_field="object_id")
    message = models.TextField()
    rating = models.SmallIntegerField( # rating 필드는 댓글에 대한 평점을 저장하는 필드
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
    )
