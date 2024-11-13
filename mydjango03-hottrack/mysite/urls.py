from django.conf import settings # Django 설정을 가져옵니다. 이 설정에서 DEBUG 값이 참인지 확인하여 디버그 도구를 활성화할지 결정
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls), # admin/ URL로 들어오는 요청을 Django 관리 사이트로 라우팅
    path(route="hottrack/", view=include("hottrack.urls")), # include를 사용하여 다른 앱의 URL을 포함
    path(route="", view=lambda request: redirect("/hottrack/")), # 기본 URL (/)로 들어오는 요청을 /hottrack/로 리디렉션합니다.
]

if settings.DEBUG: # DEBUG 모드가 활성화된 경우, 디버그 툴바를 사용하기 위해 추가적인 URL 패턴을 추가
    urlpatterns += [ # 디버그 툴바가 활성화된 상태에서 __debug__/ 경로에 대한 요청을 debug_toolbar.urls로 라우팅
        path(route="__debug__/", view=include("debug_toolbar.urls")),
    ]
