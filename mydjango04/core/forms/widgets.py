# core/forms/widgets.py # Django의 커스텀 폼 위젯을 정의하는 클래스들
import dataclasses
import datetime
import re
from typing import Callable, Dict, List, Tuple, Union  # 타입 힌트 모듈

from django.conf import settings
from django.forms import (CheckboxInput, ClearableFileInput, DateInput,
                          MultiWidget, RadioSelect, Select, TextInput)


class CounterTextInput(TextInput): # 입력 필드의 글자 수를 세는 기능
    template_name = "core/forms/widgets/counter_text.html"


class IosSwitchInput(CheckboxInput):
    def __init__(self, attrs=None, check_test=None):
        attrs = attrs or {}
        attrs["class"] = attrs.get("class", "") + " ios-form-switch" # "ios-form-switch" 클래스를 추가하여 iOS 스타일의 스위치로 표시
        super().__init__(attrs, check_test)

    # Meta로 지정하지마세요. # 이 클래스에서 사용하는 CSS 파일을 지정
    class Media:
        css = {
            "all": [
                "core/forms/widgets/ios_form_switch.css",
            ],
        }


class PreviewClearableFileInput(ClearableFileInput): # 사용자가 파일을 선택하면 미리보기를 제공하고 파일을 지울 수 있는 기능
    template_name = "core/forms/widgets/preview_clearable_file.html"


class HorizontalRadioSelect(RadioSelect): # 라디오 버튼을 가로로 배치하는 UI를 제공
    template_name = "core/forms/widgets/horizontal_radio.html"


class StarRatingSelect(Select): # 별점 선택 UI를 제공
    template_name = "core/forms/widgets/star_rating_select.html"

    class Media: # 별점 UI를 제공하기 위해 필요한 외부 라이브러리
        css = {
            "all": ["core/star-rating-js/4.3.0/star-rating.min.css"],
        }
        js = [
            "core/star-rating-js/4.3.0/star-rating.min.js",
        ]


class PhoneNumberInput(MultiWidget): # 세 개의 TextInput 위젯을 포함하여 전화번호를 입력할 수 있는 UI를 제공
    subwidget_default_attrs = {
        "style": "width: 6ch; margin-right: 1ch;",
        "autocomplete": "off",
    }

    def __init__(self, attrs=None):
        widgets = [
            TextInput(
                attrs={
                    **self.subwidget_default_attrs,
                    "pattern": r"01\d",
                    "maxlength": 3,
                },
            ),
            TextInput(
                attrs={
                    **self.subwidget_default_attrs,
                    "pattern": r"\d{4}",
                    "maxlength": 4,
                },
            ),
            TextInput(
                attrs={
                    **self.subwidget_default_attrs,
                    "pattern": r"\d{4}",
                    "maxlength": 4,
                },
            ),
        ]
        super().__init__(widgets, attrs)

    def build_attrs(self, base_attrs, extra_attrs=None): # maxlength 속성을 삭제. 각 서브 위젯에서 최대 길이를 따로 설정하기 위함
        attrs = super().build_attrs(base_attrs, extra_attrs)
        if "maxlength" in attrs:
            del attrs["maxlength"]
        return attrs

    def decompress(self, value: str) -> Tuple[str, str, str]: # 저장된 전화번호 값을 분해하여 각 부분(국가 코드, 지역 번호, 개인 번호)으로 나누어 반환
        if value:
            value = re.sub(r"[ -]", "", value)
            return value[:3], value[3:7], value[7:]
        return "", "", ""

    def value_from_datadict(self, data, files, name) -> str: # 사용자가 입력한 값을 하나의 문자열로 결합하여 반환
        values = super().value_from_datadict(data, files, name)
        return "".join((value or "") for value in values)

# 데이터 클래스 - (__init__, __repr__, __eq__)를 자동으로 생성해 주어, 코드의 간결함을 높입니다.
@dataclasses.dataclass # 클래스를 데이터 클래스 형태로 정의하는 데코레이터
class DatePickerOptions:
    datesDisabled: Union[ # Union[X, Y]는 X 또는 Y를 의미, 사용자가 선택할 수 없는 날짜의 리스트 또는 날짜 리스트를 반환하는 함수
        List[datetime.date],
        Callable[[], List[datetime.date]], # Callable[[인자의 타입, ...], return될 타입]
    ] = dataclasses.field(default_factory=list) # 기본값은 빈 리스트([])로 설정
    format: str = "yyyy-mm-dd"  # 날짜 포맷
    minDate: Union[ # Union[X, Y]는 X 또는 Y를 의미
        str, int, datetime.date, Callable[[], Union[str, int, datetime.date]]
    ] = None
    maxDate: Union[ # Union[X, Y]는 X 또는 Y를 의미
        str, int, datetime.date, Callable[[], Union[str, int, datetime.date]]
    ] = None
    todayButton: bool = False
    todayHighlight: bool = False

    # 데이터 클래스를 딕셔너리 형태로 변환하여 날짜 선택기에 필요한 옵션을 쉽게 사용할 수 있도록 합니다
    def to_dict(self) -> Dict[str, Union[str, int, List[int], List[datetime.date]]]: # Union[X, Y]는 X 또는 Y를 의미
        result = {}
        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            if callable(value):  # value가 함수라면
                value = value()  # 인자없이 호출하여 반환값을 value로서 활용합니다.
            result[field.name] = value
        return result


class DatePickerInput(DateInput): # 날짜 선택기를 위한 커스텀 입력 필드를 정의
    template_name = "core/forms/widgets/date_picker.html"

    def __init__(
        self,
        attrs=None,
        format=None,
        date_picker_options: DatePickerOptions = None,
    ):
        self.date_picker_options = date_picker_options or DatePickerOptions() # 날짜 선택기 옵션을 DatePickerOptions 클래스를 통해 설정
        super().__init__(attrs, format)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["date_picker_options"] = self.date_picker_options.to_dict()
        return context

    class Media: # 외부 CSS 및 JavaScript 파일을 로드하여 날짜 선택기 기능을 구현
        css = {
            "all": [
                "https://cdn.jsdelivr.net/npm/vanillajs-datepicker@1.3.4/dist/css/datepicker-bs5.min.css",
            ],
        }
        js = [
            "https://cdn.jsdelivr.net/npm/vanillajs-datepicker@1.3.4/dist/js/datepicker.min.js",
        ]


class NaverMapPointInput(TextInput):
    template_name = "core/forms/widgets/naver_map_point.html"

    def __init__(self, zoom=10, scale_control=True, zoom_control=True, attrs=None):
        self.zoom = zoom
        self.scale_control = scale_control
        self.zoom_control = zoom_control

        if attrs is None:
            attrs = {}

        attrs["readonly"] = "readonly"
        attrs["autocomplete"] = "off"

        super().__init__(attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["naver_map_options"] = {
            "zoom": self.zoom,
            "scaleControl": self.scale_control,
            "zoomControl": self.zoom_control,
        }
        return context

    class Media: # 네이버 지도를 표시하기 위해 필요한 JavaScript 파일을 로드
        js = [
            "https://oapi.map.naver.com/openapi/v3/maps.js?ncpClientId="
            + settings.NAVER_MAP_POINT_WIDGET_CLIENT_ID
        ]
