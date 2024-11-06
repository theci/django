import datetime

from django import forms
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator

from core.forms.widgets import PhoneNumberInput, DatePickerInput

# 휴대폰 번호 형식을 처리하는 커스텀 CharField
class PhoneNumberField(forms.CharField):
    default_error_messages = { # 사용자가 입력한 값이 유효한 휴대폰 번호 형식이 아니면 이 메시지가 표시
        "invalid": "휴대폰 번호 포맷으로 입력해주세요.",
    }
    widget = PhoneNumberInput # 필드에 사용될 HTML 입력 위젯을 설정. forms/widgets.py
    default_validators = [
        RegexValidator(r"^01\d[ -]?\d{4}[ -]?\d{4}$"),
    ]

    def __init__(self, *, max_length=13, min_length=11, **kwargs):
        super().__init__(max_length=max_length, min_length=min_length, **kwargs)

# 날짜 선택 필드의 최소값과 최대값을 설정하고, 선택한 날짜가 유효한 범위 내에 있는지 확인하는 기능
class DatePickerField(forms.DateField):
    default_error_messages = { # **을 통해 기본 forms.DateField의 오류 메시지를 확장하여 추가적인 오류 메시지를 설정
        "min_value": "%(limit_value)s 이상의 날짜를 선택해주세요.",
        "max_value": "%(limit_value)s 이하의 날짜를 선택해주세요.",
        **forms.DateField.default_error_messages, 
    }
    widget = DatePickerInput # 사용자가 날짜를 선택할 수 있게 돕는 UI 요소

    def __init__(self, *, min_value=None, max_value=None, **kwargs):
        self.min_value: datetime.date = min_value
        self.max_value: datetime.date = max_value
        super().__init__(**kwargs) # 부모 클래스인 forms.DateField의 __init__ 메서드를 호출하여 추가적인 인자를 전달

        if self.min_value is not None:
            self.validators.append(MinValueValidator(self.min_value))

        if self.max_value is not None:
            self.validators.append(MaxValueValidator(self.max_value))

        if isinstance(self.widget, DatePickerInput): # self.widget이 DatePickerInput 인스턴스일 경우, 날짜 선택 위젯의 옵션(date_picker_options)을 업데이트
            if (
                self.min_value is not None
                and self.widget.date_picker_options.minDate is None
            ):
                self.widget.date_picker_options.minDate = self.min_value

            if (
                self.max_value is not None
                and self.widget.date_picker_options.maxDate is None
            ):
                self.widget.date_picker_options.maxDate = self.max_value
