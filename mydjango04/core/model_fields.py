import ipaddress
from typing import Union, Optional

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from core.forms import fields as core_form_fields


class BooleanYNField(models.BooleanField):
    true_value = "Y"
    false_value = "N"

    default_error_messages = {
        # null=False 일 때의 값 오류 메시지
        "invalid": (
            f"“%(value)s” 값은 True/False 값이어야 하며 "
            f"'{true_value}'/'{false_value}' 문자열도 지원합니다."
        ),
        # null=True 일 때의 값 오류 메시지
        "invalid_nullable": (
            f"“%(value)s” 값은 None이거나 True/False 값이어야 하며 "
            f"'{true_value}'/'{false_value}' 문자열도 지원합니다."
        ),
    }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 1) # 필드의 초기화 과정에서 max_length를 기본값으로 1로 설정
        super().__init__(*args, **kwargs)

    def get_internal_type(self):
        return "CharField"

    # 입력값을 Python의 True/False 값으로 변환하는 메서드
    def to_python(self, value: Union[str, bool]) -> Optional[bool]: # 인자 값을 str이나 bool을 받겠다. 반환 값이 bool 값 이거나 None값이 올 수도 있다는 뜻
        if self.null and value in self.empty_values: # null=True이거나 값이 비어 있으면 None을 반환
            return None

        if value == self.true_value: # 입력값이 'Y'인 경우 True를 반환하고, 'N'인 경우 False를 반환
            return True
        if value == self.false_value:
            return False

        return super().to_python(value) # 그 외의 값이 들어오면 부모 클래스인 BooleanField의 to_python 메서드를 호출하여 처리

    def from_db_value(
        self, value: Optional[str], expression, connection # 인자 값을 str이나 None을 받겠다
    ) -> Optional[bool]: # 반환 값을 bool이나 None을 받겠다.
        return self.to_python(value) # 

    def get_prep_value(self, value: Union[str, bool]) -> Optional[str]: # 인자 값을 str이나 bool을 받겠다. 반환 값이 bool 값 이거나 None값이 올 수도 있다는 뜻
        prep_value: Optional[bool] = super().get_prep_value(value)
        if prep_value is None: # None인 경우는 그대로 None을 반환하여 데이터베이스에 NULL 값이 저장되도록 합니다.
            return None 
        return self.true_value if prep_value else self.false_value # True이면 'Y'를, False이면 'N'을 반환하여 데이터베이스에 저장할 값을 반환

# 사용자가 IPv4 주소를 문자열로 입력하더라도 내부적으로는 해당 주소를 정수로 저장하고, 데이터를 조회할 때는 다시 문자열 형태의 IPv4 주소로 변환
class IPv4AddressIntegerField(models.CharField):
    default_error_messages = { # 발생할 수 있는 오류 메시지를 정의
        "invalid": "“%(value)s” 값은 IPv4 주소나 정수여야 합니다.",
        "invalid_nullable": "“%(value)s” 값은 None이거나 IPv4 주소나 정수여야 합니다.",
    }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 15)
        super().__init__(*args, **kwargs)

    def get_internal_type(self):
        return "PositiveIntegerField" # IPv4AddressIntegerField는 PositiveIntegerField로 저장

    def db_type(self, connection):
        if connection.vendor == "postgresql":
            return "bigint"
        if connection.vendor == "oracle":
            return "number(19)"
        return super().db_type(connection)

    def to_python(self, value: Union[str, int]) -> Optional[str]: # 인자 값을 str이나 int을 받겠다. 반환 값이 str 값 이거나 None값이 올 수도 있다는 뜻
        if self.null and value in self.empty_values: # 만약 null을 허용하는 필드이고, value가 비어 있으면 None을 반환
            return None

        if isinstance(value, str) and value.isdigit(): # 만약 value가 문자열이고 숫자만 포함된 경우(즉, 정수로 변환할 수 있는 경우) int로 변환
            value = int(value)

        try:
            return str(ipaddress.IPv4Address(value)) # ipaddress.IPv4Address(value)를 사용하여, 값을 IPv4 주소로 변환
        except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
            raise ValidationError(
                self.default_error_messages[
                    "invalid_nullable" if self.null else "invalid"
                ],
                code="invalid",
                params={"value": value},
            )

    # 데이터베이스에 저장된 값 int를 to_python 메서드를 통해 처리하여 다시 IPv4 주소 문자열로 변환
    def from_db_value(self, value: Optional[int], expression, connection) -> str:
        return self.to_python(value)

    # Python 값(IPv4 주소 문자열)을 데이터베이스에 저장할 수 있는 형식(여기서는 정수)으로 변환
    def get_prep_value(self, value: Union[str, int]) -> Optional[int]:
        prep_value: Optional[str] = super().get_prep_value(value)
        if prep_value is None:
            return None
        return int(ipaddress.IPv4Address(prep_value))


class DatePickerField(models.DateField):
    def __init__(self, *args, min_value=None, max_value=None, **kwargs):
        self.min_value = min_value
        self.max_value = max_value
        super().__init__(*args, **kwargs)

        if self.min_value is not None:
            self.validators.append(MinValueValidator(self.min_value))

        if self.max_value is not None:
            self.validators.append(MaxValueValidator(self.max_value))

    def formfield(self, **kwargs):
        return super().formfield(
            **kwargs,
            form_class=core_form_fields.DatePickerField,
            min_value=self.min_value,
            max_value=self.max_value,
        )
