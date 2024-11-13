from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class ZipCode(models.Model):
    code = models.CharField(max_length=6)
    name = models.CharField(max_length=100)


class JuniorEmployee(models.Model):
    id = models.IntegerField(primary_key=True, db_column="employee_id") # DB 실제 컬럼 이름을 employee_id으로 설정
    first_name = models.CharField(max_length=50, db_column="employee_first_name")
    last_name = models.CharField(max_length=50, db_column="employee_last_name")

    class Meta:
        managed = False # 테이블 뷰(view)에 사용됨, 이 모델은 실제 데이터베이스의 테이블에 대응하지만, Django의 마이그레이션 시스템에서는 관리하지 않습니다.
        db_table = "junior_employee_view" # junior_employee_view라는 이름의 테이블에 매핑됨을 지정


class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, # settings.AUTH_USER_MODEL을 사용하여 Django 프로젝트의 사용자 모델(User)과의 외래 키 관계를 정의
        on_delete=models.CASCADE,
        related_name="shop_post_set", # User 모델의 인스턴스에서 Post 모델의 역참조 이름을 정의  ex) user.shop_post_set.all()
        related_query_name="shop_post", # 쿼리셋에서 역참조를 사용할 때 사용하는 이름 ex) Post.objects.filter(shop_post=some_user)
    )
    message = models.TextField() # TextField는 긴 텍스트를 저장할 수 있는 필드


class Product(models.Model):
    name = models.CharField(max_length=100)
    is_available = models.BooleanField(default=True)


class Order(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        # limit_choices_to={"is_available": True},
        limit_choices_to=Q(is_available=True), # 가용한 제품에 대한 주문만 생성토록 제한합니다.
    )


class Event(models.Model):
    name = models.CharField(max_length=100)
    event_date = models.DateField()


def get_current_date():
    return {"event_date__gte": timezone.now()}


class Ticket(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        limit_choices_to=get_current_date,
    )
