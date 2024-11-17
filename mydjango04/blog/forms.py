from core.crispy_bootstrap5_ext.layout import BorderedTabHolder
from core.forms.widgets import HorizontalRadioSelect, StarRatingSelect
from crispy_bootstrap5.bootstrap5 import FloatingField
from crispy_forms.bootstrap import PrependedText, Tab, TabHolder
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout, Row, Submit
from django import forms
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.db import models

from .models import Memo, Review, Tag


# 사용자가 "message"와 "rating"을 입력할 수 있도록 하며, StarRatingSelect 위젯을 사용하여 별점 선택을 구현
class ReviewForm(forms.ModelForm):
    class Meta: # ModelForm을 더 명확하게 구성하고, 폼의 설정들을 하나의 클래스 안에 모아서 관리하는 클래스
        model = Review # 이 폼은 Review 모델 클래스와 연결
        fields = ["message", "rating"] # 이 폼에서 사용할 모델의 필드
        widgets = { # 폼 필드의 위젯을 커스터마이즈
            "rating": StarRatingSelect(
                choices=[(i, i) for i in range(1, 6)],
            ),
        }


class DemoForm(forms.Form):
    author = forms.CharField(label="작성자")
    instagram_username = forms.CharField(label="인스타그램 아이디")
    title = forms.CharField(label="제목")
    summary = forms.CharField( # 요약을 입력받는 CharField로, 최소 20자에서 최대 200자까지 입력을 허용하는 유효성 검사를 추가
        label="요약",
        help_text="본문에 대한 요약을 최소 20자, 최대 200자 내로 입력해주세요.",
        validators=[MinLengthValidator(20), MaxLengthValidator(200)],
    )
    content = forms.CharField(widget=forms.Textarea, label="내용")
    content_en = forms.CharField(widget=forms.Textarea, label="내용(영문)") # forms.Textarea 위젯을 사용하여 멀티라인 입력을 받습니다.

    field_order = [ # 폼 필드의 순서를 지정하는 옵션
        "title",
        "summary",
        "author",
        "instagram_username",
    ] 

    # 폼의 레이아웃이 좀 더 직관적이고 사용하기 편리한 스타일로 구성
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper() # FormHelper는 주로 폼의 스타일링과 구성을 처리하며, 다양한 레이아웃 옵션을 사용하여 폼을 효율적으로 제어할 수 있습니다.
        # self.helper.form_action = "" # 이 속성에 URL을 지정하면, 폼이 제출될 때 해당 URL로 요청을 보냅니다. 기본적으로 폼의 action 속성은 빈 문자열이므로, 이 속성을 지정하지 않으면 폼이 현재 URL로 제출됩니다.
        # self.helper.form_tag = True # True로 설정하면 form 태그가 자동으로 포함됩니다.
        # self.helper.disable_csrf = False
        # self.helper.form_class = "form-horizontal"
        # self.helper.label_class = "col-sm-4"
        # self.helper.field_class = "col-sm-8"
        self.helper.attrs = {"novalidate": True} # novalidate 속성(attrs)을 추가하여 클라이언트 측의 기본 유효성 검사를 비활성화. HTML5에서 제공하는 기본 유효성 검사 기능이 작동하지 않게 됩니다.
        self.helper.layout = Layout(     # Layout 객체를 사용하여 폼 필드가 어떻게 표시될지를 정의할 수 있습니다.
            FloatingField("title"), # title 필드를 플로팅 스타일로 렌더링합니다. 일반적으로 라벨이 입력란 위에 위치하도록 설정
            "summary",
            BorderedTabHolder( # content와 content_en 필드를 탭 형식으로 묶어서 렌더링
                Tab("내용", "content"),
                Tab("내용 (영문)", "content_en"),
            ),
            Row( # Row는 필드들을 그리드 형식으로 배치할 때 사용됩니다. 예를 들어, 두 개의 필드를 한 줄에 나란히 배치하고 싶을 때 유용합니다.
                Field("author", autocomplete="off", wrapper_class="col-sm-6"), # author와 instagram_username 필드를 그리드 시스템에 맞게 배치. autocomplete="off"는 자동 완성을 비활성화
                PrependedText("instagram_username", "@", wrapper_class="col-sm-6"), # instagram_username 필드에 @ 문자를 미리 추가
            ),
        )
        self.helper.add_input(Submit("submit", "제출")) # "제출" 버튼을 폼에 추가

    # clean 메서드는 폼 전체의 유효성 검사를 담당합니다. 이 메서드는 각 필드의 유효성 검사 후, 폼이 제출되기 전에 추가적인 검증 로직을 구현할 때 사용
    def clean(self):
        content = self.cleaned_data.get("content")
        summary = self.cleaned_data.get("summary")

        if content and not summary: # content가 존재하지만 summary가 비어있다면, ValidationError를 발생
            raise forms.ValidationError("본문에 대한 요약을 입력해주세요.")


class MemoForm(forms.ModelForm):
    class Meta:
        model = Memo
        fields = ["message", "status"]


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name"]
