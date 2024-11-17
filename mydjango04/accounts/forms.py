import datetime
from typing import Iterator

# from core.forms.fields import PhoneNumberField, DatePickerField
from core.forms.widgets import (DatePickerInput, DatePickerOptions,
                                NaverMapPointInput, PhoneNumberInput)
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpRequest
from django.shortcuts import resolve_url
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import Profile, User

token_generator = default_token_generator

# User 모델을 기반으로 하는 폼 클래스입니다. 사용자의 first_name과 last_name을 수정할 수 있는 필드를 제공
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name"] # 폼에 포함될 필드들을 나열

    is_profile_update = forms.BooleanField( # 사용자가 프로필 수정 여부를 체크할 수 있는 체크박스를 생성
        required=False,  # 필수 입력 항목이 아님. 체크하지 않아도 유효성 검사에 통과하기
        initial=True, # 기본값을 True로 설정하여 폼이 처음 로드될 때 체크박스가 선택된 상태로 나타나도록 합니다
        label="프로필 수정 여부", # 폼에서 이 필드의 레이블(문구)을 "프로필 수정 여부"로 설정합니다. 폼에서 이 레이블은 체크박스 옆에 표시
        help_text="체크 해제하시면 프로필 수정 단계를 생략합니다.", # 용자가 체크박스를 체크 해제하면 프로필 수정 단계를 생략한다는 안내 메시지가 표시
    )


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["address", "phone_number", "photo"]


class ProfileUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email"]

    def clean_email(self) -> str:
        email = self.cleaned_data.get("email")
        if email:
            qs = self._meta.model.objects.filter(email__iexact=email)
            qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("이미 등록된 이메일입니다.")
        return email

# Profile 모델의 데이터를 입력받는 폼
class ProfileForm(forms.ModelForm):
    # mydate = DatePickerField(
    #     min_value=lambda: datetime.date.today(),
    #     max_value=lambda: datetime.date.today() + datetime.timedelta(days=7),
    # )

    # phone_number = PhoneNumberField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["address"].required = True # address 필드를 필수 입력 항목으로 설정

    class Meta:
        model = Profile
        fields = [ # Profile 모델에 정의된 필드 중에서 이 폼에서 입력될 필드들을 나열한 것
            "birth_date",
            "address",
            "location_point",
            "phone_number",
            "photo",
        ]
        widgets = { # 폼 필드에 사용될 위젯(UI)을 지정하는 딕셔너리
            "birth_date": DatePickerInput( # DatePickerInput 위젯 - 날짜를 선택할 수 있는 입력창을 생
                date_picker_options=DatePickerOptions( # date_picker_options - 날짜 선택기의 옵션을 설정
                    datesDisabled=lambda: [ # 특정 날짜들을 비활성화합니다. 예시에서는 오늘로부터 2일 후의 날짜를 비활성화하고 있습니다. 즉, 사용자가 이 날짜는 선택할 수 없습니다.
                        datetime.date.today() + datetime.timedelta(days=2),
                    ],
                    todayButton=True, # 날짜 선택기에서 오늘 날짜로 이동하는 버튼을 표시
                    todayHighlight=True, # 오늘 날짜를 강조 표시
                ),
            ),
            "location_point": NaverMapPointInput, # 네이버 지도에서 좌표를 선택하는 입력창을 위한 위젯
            "phone_number": PhoneNumberInput, # 사용자가 입력하는 전화번호 형식을 검증하고
        }


class SignupForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput, strip=False)
    new_password1 = forms.CharField(widget=forms.PasswordInput, strip=False)
    new_password2 = forms.CharField(widget=forms.PasswordInput, strip=False)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self) -> str:
        old_password = self.cleaned_data.get("old_password")
        # 유저의 기존 암호와 같은 지 비교 !!!
        if self.user.check_password(old_password) is False:
            raise forms.ValidationError("기존 암호와 일치하지 않습니다.")
        return old_password

    def clean_new_password2(self) -> str:
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("새로운 두 암호가 일치하지 않습니다.")

        validate_password(password2, self.user)

        return password2

    def save(self, commit=True) -> User:
        password = self.cleaned_data.get("new_password1")
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user


class PasswordResetForm(forms.Form):
    email = forms.EmailField() # forms.EmailField는 Django의 기본 제공 필드로, 이메일 형식이 올바른지 검사

    # auth앱의 PasswordResetForm에서는 save 메서드에서 이메일 발송에 필요한
    # 다양한 인자를 전달받습니다.
    def save(self, request: HttpRequest) -> None:
        email = self.cleaned_data.get("email") # 폼이 제출되고 유효성 검사를 통과한 후의 이메일
        for uidb64, token in self.make_uidb64_and_token(email): # 이메일에 해당하는 사용자 정보를 기반으로 uidb64와 token을 생성하여 반환
            scheme = "https" if request.is_secure() else "http"
            host = request.get_host()
            # 새로운 암호를 입력받아, 암호를 변경하는 뷰
            path = resolve_url(
                "accounts:password_reset_confirm", uidb64=uidb64, token=token
            )
            reset_url = f"{scheme}://{host}{path}"
            print(
                f"{email} 이메일로 {reset_url} 주소를 발송합니다."
            )  # TODO: 이메일 발송

    # 주어진 이메일에 해당하는 사용자를 찾아 uidb64 (Base64로 인코딩된 사용자 ID)와 token을 생성하는 함수
    def make_uidb64_and_token(self, email: str) -> Iterator[tuple[str, str]]: # Iterator[tuple[str, str]] - 두 개의 문자열을 포함하는 튜플을 순차적으로 반환하는 이터러블 객체
        for user in self.get_users(email):
            print(f"{email}에 매칭되는 유저를 찾았습니다.")

            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)

            yield uidb64, token

    def get_users(self, email: str) -> Iterator[User]: # User 객체를 순차적으로 반환하는 이터러블 객체
        active_users = User.objects.filter(email__iexact=email, is_active=True)
        return (
            user
            for user in active_users
            if user.has_usable_password() and email == user.email
        )
