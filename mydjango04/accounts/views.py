from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView as DjangoLoginView, LogoutView
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.forms import PasswordResetForm as DjangoPasswordResetForm
from django.contrib.auth.forms import SetPasswordForm as DjangoSetPasswordForm
from django.contrib.auth.views import (
    PasswordResetConfirmView as DjangoPasswordResetConfirmView,
)
from django.contrib.auth.views import PasswordResetView as DjangoPasswordResetView
from django.contrib.auth.views import PasswordChangeView as DjangoPasswordChangeView
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from formtools.wizard.views import SessionWizardView
from vanilla import UpdateView, CreateView

from accounts.forms import (
    ProfileForm,
    UserForm,
    UserProfileForm,
    SignupForm,
    ProfileUserForm,
    PasswordResetForm,
    # PasswordChangeForm,
)
from accounts.models import Profile, User


@login_required # 사용자가 로그인해야만 이 뷰를 접근할 수 있습니다. 로그인이 되어 있지 않으면 로그인 페이지로 리디렉션
def profile_edit(request):
    try:
        instance = request.user.profile
    except Profile.DoesNotExist:
        instance = None

    if request.method == "GET":
        profile_user_form = ProfileUserForm(
            prefix="profile-user", instance=request.user
        )
        profile_form = ProfileForm(prefix="profile", instance=instance)
    else: # POST 요청이 들어오면, 폼에 사용자가 제출한 데이터를 바탕으로 폼을 다시 초기화. 제출된 데이터가 유효한지 확인한 후, 유효한 경우 저장
        profile_user_form = ProfileUserForm(
            prefix="profile-user",
            data=request.POST,
            files=request.FILES,
            instance=request.user,
        )
        profile_form = ProfileForm(
            prefix="profile", data=request.POST, files=request.FILES, instance=instance
        )
        if profile_user_form.is_valid() and profile_form.is_valid():
            profile_user_form.save()

            profile = profile_form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect("accounts:profile_edit")

    return render(
        request,
        "accounts/profile_form.html",
        {
            "profile_user_form": profile_user_form,
            "profile_form": profile_form,
        },
    )


# class ProfileUpdateView(LoginRequiredMixin, UpdateView):
#     model = Profile
#     form_class = ProfileForm
#     success_url = reverse_lazy("accounts:profile_edit")
#
#     def get_object(self):
#         try:
#             return self.request.user.profile
#         except Profile.DoesNotExist:
#             return None
#
#     def form_valid(self, form):
#         profile = form.save(commit=False)
#         profile.user = self.request.user
#         return super().form_valid(form)
#
#
# profile_edit = ProfileUpdateView.as_view()

# 이 함수는 사용자가 프로필을 업데이트할지 여부를 체크하는 기능
def check_is_profile_update(wizard_view: "UserProfileWizardView") -> bool: 
    cleaned_data = wizard_view.get_cleaned_data_for_step("user_form") # "user_form" 단계에서 제출된 데이터가 유효한지 검사한 후, 그 데이터를 가져오는 메서드
    if cleaned_data is None:
        return True
    return cleaned_data.get("is_profile_update", False)

# 사용자가 여러 단계를 거쳐 프로필을 업데이트할 수 있는 폼 위저드(Wizard) 뷰를 구현한 것
class UserProfileWizardView(LoginRequiredMixin, SessionWizardView): 
    # LoginRequiredMixin - 사용자가 로그인해야만 뷰에 접근할 수 있게 합니다. 로그인하지 않으면 자동으로 로그인 페이지로 리디렉션
    # SessionWizardView - 여러 단계를 거쳐 폼을 제출하는 폼 위저드 뷰입니다. 이 뷰는 각 단계를 세션에 저장하고, 사용자가 각 단계를 진행하도록 합니다.
    form_list = [ # 뷰에서 처리할 폼들을 정의
        ("user_form", UserForm),
        ("profile_form", UserProfileForm),
    ]
    template_name = "accounts/profile_wizard.html"
    file_storage = default_storage # 파일 업로드에 대한 저장소 설정

    condition_dict = {
        "profile_form": check_is_profile_update, # 사용자가 프로필 업데이트를 했는지를 체크하는 함수
    }
    
    # 각 폼 단계에 대해 해당하는 모델 인스턴스를 반환
    def get_form_instance(self, step): 
        if step == "profile_form": # 사용자의 프로필을 가져옵니다. 프로필이 없다면 get_or_create()로 새로 생성하여 반환
            profile, __ = Profile.objects.get_or_create(user=self.request.user)
            return profile
        elif step == "user_form": # request.user로 현재 로그인한 사용자의 정보를 반환
            return self.request.user

        return super().get_form_instance(step) # 기본 동작으로 SessionWizardView에서 제공하는 다른 단계에 대한 인스턴스를 가져옵니다.

    def done(self, form_list, form_dict, **kwargs):  # noqa
        # print("form_list :", form_list)
        # print("form_dict :", form_dict)
        # for form in form_list:
        #     form.save()

        # form_list[0].save()
        # form_list[1].save()

        user = form_dict["user_form"].save() # user_form에서 데이터를 저장하고, 사용자 정보를 반환

        if "profile_form" in form_dict:
            profile = form_dict["profile_form"].save(commit=False)
            profile.user = user
            profile.save()

        messages.success(self.request, "프로필을 저장했습니다.") # 프로필 저장이 성공적으로 완료된 후, 사용자에게 성공 메시지를 전달
        return redirect("accounts:profile_wizard") # 프로필을 저장한 후, 같은 페이지로 리디렉션


# UserProfileWizardView를 뷰로 변환합니다. 
# URL 설정에서 이 뷰를 사용할 수 있도록 as_view() 메서드를 호출하여 실제 뷰로 변환
profile_wizard = UserProfileWizardView.as_view()


# def login(request):
#     if request.method == "GET":
#         return render(request, "accounts/login_form.html")
#     else:
#         username = request.POST.get("username")
#         password = request.POST.get("password")
#
#         user = authenticate(request, username=username, password=password)
#         if user is None:
#             return HttpResponse("인증 실패", status=400)
#
#         if user.is_active is False:
#             return HttpResponse("비활성화된 계정입니다.", status=400)
#
#         request.session["_auth_user_backend"] = user.backend
#         request.session["_auth_user_id"] = user.pk
#         request.session["_auth_user_hash"] = user.get_session_auth_hash()
#
#         next_url = (
#             request.POST.get("next")
#             or request.GET.get("next")
#             or settings.LOGIN_REDIRECT_URL
#         )
#         return redirect(next_url)


class LoginView(DjangoLoginView):
    template_name = "accounts/login_form.html"
    # redirect_authenticated_user = True
    # next_page = "accounts:profile"


login = LoginView.as_view()


def profile(request):
    return HttpResponse(
        f"username : {request.user.username}, {request.user.is_authenticated}"
    )


# def signup(request):
#     if request.method == "GET":
#         form = SignupForm()
#     else:
#         form = SignupForm(data=request.POST, files=request.FILES)
#         if form.is_valid():
#             created_user = form.save()
#             auth_login(request, created_user)
#
#             next_url = request.POST.get("next") or request.GET.get("next")
#             url_is_safe = url_has_allowed_host_and_scheme(
#                 url=next_url,
#                 allowed_hosts={request.get_host()},
#                 require_https=request.is_secure(),
#             )
#             if url_is_safe is False:
#                 next_url = ""
#
#             # return redirect(settings.LOGIN_URL)  # "/accounts/login/"
#             return redirect(next_url or settings.LOGIN_REDIRECT_URL)
#
#     return render(
#         request,
#         "accounts/signup_form.html",
#         {
#             "form": form,
#         },
#     )


class SignupView(CreateView):
    form_class = SignupForm # 이 폼은 사용자의 이름, 이메일, 비밀번호 등을 입력받아 새로운 사용자를 생성하는 폼
    template_name = "accounts/signup_form.html" # 이 템플릿은 사용자가 볼 가입 폼을 렌더링
    success_url = settings.LOGIN_REDIRECT_URL # 폼이 유효하게 제출되고 새 사용자가 생성된 후 리디렉션될 URL을 설정

    def form_valid(self, form) -> HttpResponse:
        response = super().form_valid(form) # form_valid 메서드를 호출하여 폼을 저장하고 응답을 생성
        created_user = form.instance  # 폼을 통해 생성된 사용자를 가져옵니다
        auth_login(self.request, created_user) # 사용자가 가입 후 자동으로 로그인되도록 auth_login을 호출
        return response

    def get_success_url(self) -> str:
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        if next_url:
            url_is_safe = url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={self.request.get_host()},
                require_https=self.request.is_secure(),
            )
            if url_is_safe:
                return next_url
        return super().get_success_url()


signup = SignupView.as_view()


# @csrf_protect
# @never_cache
# @require_POST  # auth.LogoutView에서는 장고 5.0부터 GET 요청을 통한 로그아웃을 지원하지 않습니다.
# def logout(request):
#     auth_logout(request)
#
#     next_url = request.POST.get("next")
#     if next_url:
#         url_is_safe = url_has_allowed_host_and_scheme(
#             url=next_url,
#             allowed_hosts={request.get_host()},
#             require_https=request.is_secure(),
#         )
#         if url_is_safe:
#             return redirect(next_url)
#
#     return redirect(settings.LOGIN_URL)
#
#     # return render(request, "registration/logged_out.html")


logout = LogoutView.as_view(
    # 템플릿 파일을 변경하시거나,
    # template_name="registration/logged_out.html",
    # next_page 인자를 지정하면, 최소한 템플릿 응답은 없습니다.
    next_page=settings.LOGIN_URL,
)


# @login_required
# def password_change(request):
#     if request.method == "GET":
#         form = PasswordChangeForm(request.user)
#     else:
#         form = PasswordChangeForm(request.user, data=request.POST, files=request.FILES)
#         if form.is_valid():
#             form.save()
#             update_session_auth_hash(request, request.user)
#             messages.success(request, "암호를 변경했습니다.")
#             return redirect("accounts:profile")
#
#     return render(
#         request,
#         "accounts/password_change_form.html",
#         {
#             "form": form,
#         },
#     )


class PasswordChangeView(DjangoPasswordChangeView):
    success_url = reverse_lazy("accounts:profile")
    template_name = "accounts/password_change_form.html"


password_change = PasswordChangeView.as_view()


# @csrf_protect
# def password_reset(request):
#     if request.method == "GET":
#         form = PasswordResetForm()
#     else:
#         form = PasswordResetForm(data=request.POST)
#         if form.is_valid():
#             form.save(request)
#             messages.success(
#                 request,
#                 (
#                     "비밀번호 재설정 메일을 발송했습니다. 계정이 존재한다면 입력하신 이메일로 "
#                     "비밀번호 재설정 안내문을 확인하실 수 있습니다. "
#                     "만약 이메일을 받지 못했다면 등록하신 이메일을 다시 확인하시거나 스팸함을 확인해주세요."
#                 ),
#             )
#             return redirect("accounts:password_reset")
#
#     return render(
#         request,
#         "registration/password_reset_form.html",
#         {
#             "form": form,
#         },
#     )


class PasswordResetView(DjangoPasswordResetView):
    email_template_name = "accounts/password_reset_email.html"
    success_url = reverse_lazy("accounts:password_reset")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            (
                "비밀번호 재설정 메일을 발송했습니다. 계정이 존재한다면 입력하신 이메일로 "
                "비밀번호 재설정 안내문을 확인하실 수 있습니다. "
                "만약 이메일을 받지 못했다면 등록하신 이메일을 다시 확인하시거나 스팸함을 확인해주세요."
            ),
        )
        return response


password_reset = PasswordResetView.as_view()


# http://localhost:8000/accounts/reset/Mg/c3gazp-ed8c96e920b7e4dd458df1145b4ec7d4/


# def password_reset_confirm(request, uidb64, token):
#     uid = urlsafe_base64_decode(uidb64).decode()
#     user = get_object_or_404(User, pk=uid)
#
#     context_data = {}
#     reset_url_token = "set-password"
#
#     if token != reset_url_token:
#         if default_token_generator.check_token(user, token):
#             request.session["_password_reset_token"] = token
#             redirect_url = request.path.replace(token, reset_url_token)
#             return redirect(redirect_url)
#         else:
#             # 토큰이 유효하지 않은 경우, 암호 재설정 링크가 유효하지 않다는 메시지를 노출합니다.
#             return render(
#                 request,
#                 "registration/password_reset_confirm.html",
#                 {"validlink": False},
#             )
#     else:
#         session_token = request.session.get("_password_reset_token")
#
#         if default_token_generator.check_token(user, session_token) is False:
#             validlink = False  # token 검증에 실패하면 비밀번호 입력없이 오류 응답
#         else:
#             validlink = True  # token 검증에 실패하면 재설정할 비밀번호를 입력받습니다.
#
#             # 폼 처리 (GET/POST)
#             if request.method == "GET":
#                 form = SetPasswordForm(user=user)
#             else:
#                 form = SetPasswordForm(user=user, data=request.POST)
#                 if form.is_valid():
#                     form.save()
#
#                     del request.session["_password_reset_token"]  # 세션에서 토큰 삭제
#
#                     # 암호 재설정 후, 자동 로그인
#                     # auth_login(request, user)
#
#                     # 암호 재설정 후에 자동 로그인을 수행하고자 할 때
#                     post_reset_login = True
#                     if post_reset_login:
#                         auth_login(request, user)
#                         messages.success(
#                             request, "암호를 재설정했으며, 자동 로그인 처리되었습니다."
#                         )
#                         return redirect(settings.LOGIN_REDIRECT_URL)
#                     else:
#                         messages.success(
#                             request, "암호를 재설정했습니다. 로그인해주세요."
#                         )
#                         return redirect(settings.LOGIN_URL)
#
#             context_data["form"] = form
#
#         context_data["validlink"] = validlink
#
#         return render(request, "registration/password_reset_confirm.html", context_data)


class PasswordResetConfirmView(DjangoPasswordResetConfirmView):
    post_reset_login = True
    success_url = settings.LOGIN_REDIRECT_URL

    def form_valid(self, form) -> HttpResponse:
        response = super().form_valid(form)

        messages.success(self.request, "암호를 재설정하고, 자동 로그인했습니다.")

        return response


password_reset_confirm = PasswordResetConfirmView.as_view()
