import datetime

from django.contrib.auth.models import AbstractUser, Permission, Group
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from core.model_fields import DatePickerField

# 그룹(Group)에 특정 권한(Permission)을 추가하는 메서드
def group_add_perm(self, perm_name: str) -> None:
    group = self
    app_label, codename = perm_name.split(".", 1) # perm_name을 app_label과 codename으로 분리
    permission = Permission.objects.get( # Permission 객체에 입력
        content_type__app_label=app_label,
        codename=codename,
    )
    # 해당 권한을 Group의 permissions에 추가
    group.permissions.add(permission)


# Group 클래스에 add_perm 메서드 추가하기, 이를 통해 그룹 객체에서 add_perm() 메서드를 호출할 수 있게 됩니다.
setattr(Group, "add_perm", group_add_perm)


class User(AbstractUser): # AbstractUser 클래스를 확장하여, 친구 관계 및 팔로잉 관계를 관리하는 기능을 추가
    # 친구 관계 (대칭 관계). 즉, A가 B를 친구로 추가하면 B도 A를 친구로 추가한 것
    friend_set = models.ManyToManyField(
        to="self",
        blank=True,
        # to="self"에서 디폴트 True
        symmetrical=True,
        # related_name="friend_set",
        related_query_name="friend_user",
    )

    # 팔로잉 관계 (비대칭 관계). 즉, A가 B를 팔로우한다고 해서 B가 A를 팔로우하는 것은 아닙니다.
    follower_set = models.ManyToManyField(
        to="self",
        blank=True,
        # to="self"에서 디폴트 True
        symmetrical=False,
        # symmetrical=False 에서는 related_name을 지원
        related_name="following_set",
        related_query_name="following",
    )
    
    # User 클래스에 특정 권한을 추가하는 메서드
    # 사용자가 add_perm()을 호출하여, 특정 앱의 특정 권한을 해당 사용자에게 부여할 수 있습니다.
    def add_perm(self, perm_name: str) -> None: 
        # perm_name 예시 : "blog.add_post"

        user = self

        # app_label = "blog"
        # codename = "add_post"
        app_label, codename = perm_name.split(".", 1)

        # app_label과 codename으로 Permission 조회
        permission = Permission.objects.get(
            content_type__app_label=app_label,
            codename=codename,
        )
        # 유저 퍼미션 목록에 추가
        user.user_permissions.add(permission)


# User 객체가 생성될 때 자동으로 해당 사용자에 대한 Profile 객체를 생성하는 기능입니다.
@receiver(post_save, sender=User) # post_save 시그널을 사용하여 User 객체가 생성될 때마다 자동으로 해당 사용자의 프로필을 생성
def post_save_on_user(instance: User, created: bool, **kwargs):
    if created:
        print(f"User({instance})의 프로필을 생성합니다.")
        Profile.objects.create(user=instance) # Profile.objects.create(user=instance)가 실행되어 Profile 인스턴스가 생성

# SuperUser 모델에 대해 is_superuser=True인 사용자만을 필터링하여 반환하는 쿼리셋을 제공하는 커스텀 매니저
class SuperUserManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(is_superuser=True) # is_superuser=True인 사용자만 반환하도록 오버라이드

# User 모델을 확장하여 SuperUser 모델을 정의하는데, 이 모델은 관리자(superuser) 사용자만을 위한 모델
class SuperUser(User):
    objects = SuperUserManager() # SuperUserManager를 통해, SuperUser 모델은 is_superuser=True인 사용자만 반환

    class Meta:
        proxy = True # SuperUser가 User 모델의 프록시 모델임을 나타냄. 즉, SuperUser는 데이터베이스 테이블을 별도로 생성하지 않고, User 모델과 동일한 테이블을 사용

    def save(self, *args, **kwargs): # save() 메서드를 오버라이드하여 객체를 저장할 때 항상 is_superuser=True로 설정
        self.is_superuser = True
        super().save(*args, **kwargs)


# User와 1:1 관계를 가지는 Profile 모델로, 사용자의 추가적인 정보(생일, 주소, 전화번호, 프로필 사진 등)를 저장하는 객체
class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        related_query_name="profile",
    )
    birth_date = DatePickerField( # 날짜 선택기(DatePickerField)를 사용하고 최소/최대 날짜 범위를 설정
        min_value=lambda: datetime.date.today(),
        max_value=lambda: datetime.date.today() + datetime.timedelta(days=7),
        blank=True,
        null=True,
    )
    address = models.CharField(max_length=100, blank=True)
    location_point = models.CharField(max_length=50, blank=True)
    phone_number = models.CharField(
        max_length=13,
        blank=True,
        validators=[
            RegexValidator(
                r"^01\d[ -]?\d{4}[ -]?\d{4}$",
                message="휴대폰 번호 포맷으로 입력해주세요.",
            ),
        ],
    )
    point = models.PositiveIntegerField(default=0) 

    photo = models.ImageField(upload_to="profile/photo", blank=True)


# Profile 객체가 삭제될 때, 해당 프로필에 연결된 사진 파일을 삭제하는 메서드
@receiver(post_delete, sender=Profile) # post_delete는 Profile 객체가 삭제된 후에 실행
def post_delete_on_profile(instance: Profile, **kwargs):
    instance.photo.delete(save=False) # save=False로 설정하여 파일만 삭제하고 객체 자체는 저장하지 않습니다.

