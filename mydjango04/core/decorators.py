# core/decorators.py

from functools import wraps
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, ParseResult

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required as django_login_required
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django_htmx.http import HttpResponseClientRedirect


# 1. 사용자가 로그인되어 있는지 확인합니다.
# 2. 로그인되어 있지 않으면 로그인 페이지로 리다이렉트합니다.
# 3. 만약 요청이 HTMX 요청이라면, 리다이렉트 URL에 next 쿼리 파라미터를 추가하여, 로그인 후 사용자가 원래 요청한 페이지로 리다이렉트되도록 만듭니다.
# 4. 새로운 URL로 클라이언트 측 리다이렉트를 수행합니다.

# HTMX 요청을 처리할 때의 동작을 추가하는 커스텀 데코레이터 함수
def login_required_hx(
    function=None, # 데코레이터에 적용될 실제 뷰 함수, None일 경우, 나중에 데코레이터로 감싸기 위해서 사용
    redirect_field_name=REDIRECT_FIELD_NAME, # 로그인 후 리다이렉트할 URL을 next 쿼리 파라미터로 지정하는 데 사용
    login_url=None, # 사용자가 로그인하지 않은 경우 리다이렉트할 URL을 지정하는 옵션
):
    def decorator(view_func): # 뷰 함수(view_func)를 데코레이터로 감싸는 함수
        @wraps(view_func)  # 원본 뷰 함수(view_func)를 감싸서 추가적인 wrapper 로직을 실행
        def wrapper(request, *args, **kwargs): 
            decorated_view_func = django_login_required( # django_login_required를 사용하여, 사용자가 로그인이 되어 있는지 확인
                function=view_func,
                redirect_field_name=redirect_field_name,
                login_url=login_url, # 로그인되지 않았다면, login_url로 리다이렉트
            )

            response = decorated_view_func(request, *args, **kwargs)

            if isinstance(response, HttpResponseRedirect):
                resolved_login_url = resolve_url(login_url or settings.LOGIN_URL)

                if request.htmx and resolved_login_url in response.url:
                    # /accounts/login/?next=/blog/tags/new/%3F_%3D1710826915601
                    # next_url: str = response.url
                    # request.htmx.current_url
                    # return HttpResponseClientRedirect(next_url)

                    # HTMX 요청을 한 주소가 next 인자로 포함된 URL
                    redirect_url: str = response.url
                    # HTMX 요청을 한 페이지의 주소
                    new_redirect_url: str = request.htmx.current_url

                    # next 인자가 포함된 URL에서 next 인자만 new_redirect_url 값으로 변경
                    parsed: ParseResult = urlparse(redirect_url)
                    query_dict: dict = parse_qs(parsed.query)
                    query_dict["next"] = [new_redirect_url]
                    new_query: str = urlencode(query_dict, doseq=True)
                    new_next_url = urlunparse(
                        (
                            parsed.scheme,
                            parsed.netloc,
                            parsed.path,
                            parsed.params,
                            new_query,
                            parsed.fragment,
                        )
                    )

                    return HttpResponseClientRedirect(new_next_url) # 클라이언트 측에서 리다이렉트를 수행하도록 응답을 보냅니다. 이 응답은 HTMX를 통해 요청한 클라이언트에 리다이렉트 URL을 전달

            return response

        return wrapper

    if function:
        return decorator(function)

    return decorator
