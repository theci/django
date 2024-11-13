# blog/models.py
from uuid import uuid4

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import UniqueConstraint, Q
from django.db.models.functions import Lower
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django_lifecycle import hook, BEFORE_UPDATE, LifecycleModelMixin, AFTER_UPDATE
# Django Lifecycle - Django 모델에서 특정 상태나 이벤트가 발생했을 때 자동으로 특정 동작을 트리거할 수 있는 기능을 제공
# 후크(hook)를 정의하고 그 시점에 자동으로 실행되는 동작을 설정

from core.model_fields import IPv4AddressIntegerField, BooleanYNField

# created_at과 updated_at 필드를 자동으로 관리하는 추상 기본 모델
class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)  # 객체가 처음 생성될 때만 최초 생성시각을 자동 저장
    updated_at = models.DateTimeField(auto_now=True)  # 객체가 수정될 때마다 매 수정시각을 자동 저장

    class Meta:
        abstract = True # 이 모델은 데이터베이스 테이블로 생성되지 않고, 다른 모델에서 상속받아 사용할 수 있습니다.


class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.name


class PostQuerySet(models.QuerySet):
    def published(self): # 상태가 **발행(PUBLISHED)**인 게시물을 필터링
        return self.filter(status=Post.Status.PUBLISHED)

    def draft(self): # 상태가 **초안(DRAFT)**인 게시물을 필터링
        return self.filter(status=Post.Status.DRAFT)

    def search(self, query: str): # title 필드에 query를 포함하는 게시물을 필터링
        return self.filter(title__contains=query)

    # def by_author(self, author):
    #     return self.filter(author=author)

    def create(self, **kwargs): # 게시물을 생성할 때 status를 **발행(PUBLISHED)**로 기본값 설정하여 생성
        kwargs.setdefault("status", Post.Status.PUBLISHED)
        return super().create(**kwargs)


# class PublishedPostManager(models.Manager):
#     def get_queryset(self):
#         qs = super().get_queryset()
#         qs = qs.filter(status=Post.Status.PUBLISHED)
#         return qs
#
#     def create(self, **kwargs):
#         kwargs.setdefault("status", Post.Status.PUBLISHED)
#         return super().create(**kwargs)


# LifecycleModelMixin - 모델에 생애주기 후크를 설정할 수 있도록 도와주는 믹스인입니다. 
# 이 믹스인을 모델에 추가하면, hook 데코레이터와 함께 모델의 상태 변화를 처리할 수 있는 메서드를 정의할 수 있습니다.
class Post(LifecycleModelMixin, models.Model):
    class Status(models.TextChoices):  # 문자열 선택지
        DRAFT = "D", "초안"  # 상수, 값, 레이블
        PUBLISHED = "P", "발행"

    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blog_post_set",
        related_query_name="blog_post",
    )
    title = models.CharField(max_length=100)
    slug = models.SlugField(
        max_length=120, allow_unicode=True, help_text="title 값으로부터 자동변환됩니다."
    )
    status = models.CharField(
        # 선택지 값 크기에 맞춰 최대 길이를 지정
        max_length=1,
        # choices 속성으로 사용할 수 있도록 2중 리스트로 반환
        # choices 속성은 모든 모델 필드에서 지원합니다.
        choices=Status.choices,
        # status 필드에 대한 모든 값 지정에는 상수로 지정하면 쿼리에 값으로 자동 변환
        default=Status.DRAFT,
    )
    content = models.TextField()
    tag_set = models.ManyToManyField(
        "Tag",
        blank=True,
        related_name="blog_post_set",
        related_query_name="blog_post",
        through="PostTagRelation",
        through_fields=("post", "tag"),
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 최초 생성시각을 자동 저장
    updated_at = models.DateTimeField(auto_now_add=True)  # 최초 생성시각을 자동 저장

    # published = PublishedPostManager()
    # objects = models.Manager()

    objects = PostQuerySet.as_manager()

    def __str__(self):
        # choices 속성을 사용한 필드는 get_필드명_display() 함수를 통해 레이블 조회를 지원합니다.
        return f"{self.title} ({self.get_status_display()})"

    # 게시물 제목을 기반으로 유니크한 슬러그를 자동 생성
    def slugify(self, force=False): 
        if force or not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
            self.slug = self.slug[:112]
            # 제목으로 만든 slug 문자열 뒤에 uuid를 붙여 slug의 유일성을 확보
            self.slug += "-" + uuid4().hex[:8]

    # content 필드가 변경될 때마다 updated_at을 갱신 
    #  hook은 특정 이벤트가 발생했을 때 실행될 메서드를 지정할 수 있게 해주는 데코레이터
    #  BEFORE_UPDATE - 필드 값이 업데이트되기 전에 실행
    @hook(BEFORE_UPDATE, when="content", has_changed=True)
    def on_changed_content(self):
        print("content 필드가 변경되었으니, updated_at을 갱신합니다.")
        self.updated_at = timezone.now()

    # AFTER_UPDATE: 필드 값이 업데이트된 후에 실행
    @hook(AFTER_UPDATE, when="status", was=Status.DRAFT, is_now=Status.PUBLISHED) # status가 초안에서 발행으로 변경될 때 이메일을 보내는 로직을 트리거
    def on_published(self): # status가 초안에서 발행으로 변경될 때 이메일을 보내는 로직을 트리거
        print("저자에게 이메일을 보냅니다.")

    # def save(self, *args, **kwargs):
    #     """save 시에 slug 필드를 자동으로 채워줍니다."""
    #     self.slugify()
    #     super().save(*args, **kwargs)

    class Meta: 
        constraints = [ # slug 필드에 유니크 제약을 설정
            UniqueConstraint(fields=["slug"], name="unique_slug"), 
        ]
        verbose_name = "포스팅" # 모델의 이름을 한글로 지정
        verbose_name_plural = "포스팅 목록"
        permissions = [ # "프리미엄 컨텐츠를 볼 수 있음"이라는 권한을 추가
            ("view_premium_post", "프리미엄 컨텐츠를 볼 수 있음"),
        ]


# 이 데코레이터는 Post 모델의 pre_save 신호에 대한 수신기를 정의
# Post 모델의 인스턴스가 저장되기 전에 자동으로 호출
@receiver(pre_save, sender=Post)
def pre_save_on_save(sender, instance: Post, **kwargs):
    print("pre_save_on_save() 메서드가 호출되었습니다.")
    instance.slugify()


# Post 모델에 대한 댓글을 저장하는 모델
class Comment(TimestampedModel):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()

# 사용자의 접속 정보를 기록하는 모델
class AccessLog(TimestampedModel):
    ip_generic = models.GenericIPAddressField(protocol="IPv4") # IPv4 형식의 IP 주소를 저장
    ip_int = IPv4AddressIntegerField() # IP 주소를 정수형으로 저장할 수 있는 커스텀 필드. core/model_fields.py 

# 기사와 같은 내용을 저장하는 모델
class Article(TimestampedModel):
    title = models.CharField(max_length=100)
    is_public_ch = models.CharField( # 공개 여부를 "Y"(예), "N"(아니오)로 저장하는 CharField
        max_length=1,
        choices=[
            ("Y", "예"),
            ("N", "아니오"),
        ],
        default="N",
    )
    is_public_yn = BooleanYNField(default=False) # BooleanYNField를 사용하여 True(공개) 또는 False(비공개) 값을 저장.

# 사용자 리뷰를 저장하는 모델
class Review(TimestampedModel, models.Model):
    message = models.TextField()
    rating = models.SmallIntegerField(
        # validators=[
        #     MinValueValidator(1),
        #     MaxValueValidator(5),
        # ],
    )

    def get_absolute_url(self) -> str:
        return reverse("blog:review_detail", args=[self.pk])

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(rating__gte=1, rating__lte=5),
                name="blog_review_rating_gte_1_lte_5",
            ),
        ]
        db_table_comment = "사용자 리뷰와 평점을 저장하는 테이블. 평점(rating)은 1에서 5 사이의 값으로 제한."


class Tag(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                # fields=["name"],
                name="blog_tag_name_unique",
            )
        ]
        indexes = [
            # models.Index(fields=["name"]),
            # (PostgreSQL ONLY) unique=True와 동일한 인덱스 만들기
            models.Index(
                fields=["name"],
                name="blog_tag_name_like",
                opclasses=["varchar_pattern_ops"],
            )
        ]

# Post와 Tag 간의 다대다 관계를 나타내는 모델
class PostTagRelation(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    # 관계 모델을 통해, 관계에 대한 추가 정보를 담을 수 있습니다.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint( # post와 tag의 조합에 대해 유니크 제약을 설정하여 중복된 태그 관계를 방지
                fields=["post", "tag"],
                name="blog_post_tag_relation_unique",
            )
        ]


class Student(models.Model):
    name = models.CharField(max_length=100)


class Course(models.Model):
    title = models.CharField(max_length=100)

# 학생이 수강하는 강좌를 나타내는 모델
class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.CharField(max_length=10)

    class Meta:
        constraints = [ # student, course, semester의 조합에 대해 유니크 제약을 추가하여, 동일한 학기에 동일한 학생이 같은 강좌를 두 번 수강할 수 없도록 합니다
            models.UniqueConstraint(
                "student",
                "course",
                Lower("semester"),  # 다수의 expression 지정
                # fields=["student", "course", "semester"],  # 단순 필드명 나열
                name="blog_enrollment_uniq",
            ),
        ]


class MemoGroup(models.Model):
    name = models.CharField(max_length=100)


class Memo(models.Model):
    class Status(models.TextChoices):
        PRIVATE = "V", "비공개"
        PUBLIC = "P", "공개"

    # author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    group = models.ForeignKey(MemoGroup, on_delete=models.CASCADE)
    message = models.CharField(max_length=140)
    status = models.CharField(
        max_length=1, default=Status.PUBLIC, choices=Status.choices
    )
    created_at = models.DateTimeField(auto_now_add=True)
