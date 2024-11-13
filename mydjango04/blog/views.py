from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.core.files import File
from django.db.models import Q
from django.forms import formset_factory, modelformset_factory, inlineformset_factory
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_http_methods
from django_htmx.http import HttpResponseClientRefresh, trigger_client_event
from vanilla import CreateView, ListView, DetailView, UpdateView, FormView

from accounts.models import User
from blog.forms import ReviewForm, DemoForm, MemoForm, TagForm
from blog.models import Post, Review, Memo, MemoGroup, Tag
from core.decorators import login_required_hx


@login_required # 이 데코레이터는 사용자가 로그인한 상태에서만 이 뷰를 실행할 수 있도록 합니다
@permission_required("blog.view_post", raise_exception=False) # 사용자가 특정 권한(blog.view_post)을 가지고 있어야 이 뷰에 접근할 수 있게 합니다
# raise_exception=False여서 권한이 없는 경우 403 Forbidden 응답을 자동으로 처리하지 않으며, 이를 명시적으로 처리
def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug) # 주어진 slug에 해당하는 Post 객체를 데이터베이스에서 찾고, 만약 없다면 404 오류를 발생
    return HttpResponse(f"{post.pk}번 글의 {post.slug}")


@login_required
@permission_required("blog.view_premium_post", login_url="blog:premium_user_guide") # 사용자가 blog.view_premium_post 권한을 가지고 있어야만 접근
# 권한이 없는 경우, blog:premium_user_guide로 지정된 페이지로 리디렉션
def post_premium_detail(request, slug):
    return HttpResponse(f"프리미엄 컨텐츠 페이지 : {slug}") # slug를 URL에서 받아서 프리미엄 콘텐츠의 상세 정보를 화면에 출력


def premium_user_guide(request):
    return HttpResponse("프리미엄 유저 가이드 페이지")


def post_list(request):
    query = request.GET.get("query", "").strip() # GET 요청의 쿼리 매개변수에서 query 값을 가져오고, 양옆의 공백을 제거

    post_qs = Post.objects.all()

    if query:
        post_qs = post_qs.filter(
            Q(title__icontains=query) | Q(tag_set__name__in=[query])
        )

    post_qs = post_qs.select_related("author") # Post 객체와 관련된 author 정보를 한 번의 쿼리로 미리 가져옵니다
    post_qs = post_qs.prefetch_related("tag_set") # tag_set에 연결된 태그들을 미리 가져옵니다

    return render( # query와 post_qs(게시물 목록)를 전달하여 결과를 렌더링
        request,
        "blog/post_list.html",
        {
            "query": query,
            "post_list": post_qs,
        },
    )


def search(request):
    query = request.GET.get("query", "").strip()
    return render(
        request,
        "blog/search.html",
        {
            "query": query,
        },
    )


def post_new(request):
    # 요청 데이터에서 값을 추출하고,
    # 입력값에 대한 유효성 검사를 필히 수행해야만 합니다.
    message: str = request.POST.get("message", "")
    photo: File = request.FILES.get("photo", "")

    # 요청 데이터에서 값을 추출하고,
    # 입력값에 대한 유효성 검사를 필히 수행해야만 합니다.
    # 장고에서는 이러한 유효성 검사를 Form이나 Serializer에 위임해서 처리합니다.
    errors = {
        "message": [],
        "photo": [],
    }
    if not message:
        errors["message"].append("message 필드는 필수 필드입니다.")
    if len(message) < 10:
        errors["message"].append("message 필드를 10글자 이상이어야 합니다.")
    if not photo:
        errors["photo"].append("photo 필드는 필수 필드입니다.")
    if photo and not photo.name.lower().endswith((".jpg", ".jpeg")):
        errors["photo"].append("jpg 파일만 업로드할 수 있습니다.")

    return render(
        request=request,
        template_name="blog/post_new.html",
        context={
            "message": message,
            "photo": photo,
            "errors": errors,
        },
    )


review_list = ListView.as_view(
    model=Review,
)

review_new = CreateView.as_view(
    model=Review,
    form_class=ReviewForm,
    # success_url=reverse_lazy(""),
)

review_detail = DetailView.as_view(
    model=Review,
)

review_edit = UpdateView.as_view(
    model=Review,
    form_class=ReviewForm,
)


demo_form = FormView.as_view(
    form_class=DemoForm,
    template_name="blog/demo_form.html",
)


@login_required
def memo_form(request, group_pk):
    # MemoGroup 모델과 관련된 Memo 모델에 대한 폼셋을 생성, 
    # 이 폼셋은 MemoGroup과 연관된 Memo 객체를 관리하며, extra=3으로 초기 3개의 비어있는 폼을 제공
    MemoFormSet = inlineformset_factory( 
        parent_model=MemoGroup,
        model=Memo,
        form=MemoForm,
        extra=3,
        can_delete=True, # 각 메모에 대한 삭제 체크박스를 활성화
    )

    memo_group = get_object_or_404(MemoGroup, pk=group_pk)
    queryset = None  # Memo의 모든 레코드에 대한 수정폼
    # queryset = Memo.objects.none()  # 수정폼 끄기

    if request.method == "GET": # GET 요청에서는 MemoFormSet을 초기화하여 렌더링
        formset = MemoFormSet(instance=memo_group, queryset=queryset)
    else: # POST 요청에서는 제출된 데이터를 기반으로 MemoFormSet을 처리
        formset = MemoFormSet(
            data=request.POST,
            files=request.FILES,
            instance=memo_group,
            queryset=queryset,
        )
        if formset.is_valid(): # 폼셋이 유효하면, 데이터를 저장하고 성공 메시지를 표시
            objs = formset.save()

            if objs:
                messages.success(request, f"메모 {len(objs)}개를 저장했습니다.")

            if formset.deleted_objects: # 삭제된 메모 객체들을 추적하여 삭제된 메모 개수를 메시지로 표시
                messages.success(
                    request, f"메모 {len(formset.deleted_objects)}개를 삭제했습니다."
                )

            return redirect("blog:memo_form", group_pk) # 저장 후 다시 memo_form 뷰로 리디렉션하여 폼을 갱신

    return render(
        request,
        "blog/memo_form.html",
        {
            "memo_group": memo_group,
            "formset": formset,
        },
    )


# def tag_list(request):
#     tag_qs = Tag.objects.all()
#
#     query = request.GET.get("query", "")
#     if query:
#         tag_qs = tag_qs.filter(name__icontains=query)
#
#     # is_htmx = bool(request.htmx)  # request.META.get("HTTP_HX_REQUEST") == "true"
#     # if is_htmx:
#     if request.htmx:
#         template_name = "blog/_tag_list.html"
#     else:
#         template_name = "blog/tag_list.html"
#
#     return render(
#         request,
#         template_name,
#         {
#             "tag_list": tag_qs,
#         },
#     )


class TagListView(ListView):
    model = Tag
    queryset = Tag.objects.all()
    paginate_by = 10 # 페이지당 10개의 Tag를 표시

    # query 파라미터를 통해 검색어를 받아 Tag 이름에 포함된 태그만 필터링하여 표시
    def get_queryset(self): 
        qs = super().get_queryset()
        query = self.request.GET.get("query", "")
        if query:
            qs = qs.filter(name__icontains=query)
        return qs
    
    # HTMX 요청이 있을 경우, 부분 템플릿(_tag_list.html)을 반환하고, 일반 요청일 경우 전체 페이지 템플릿(tag_list.html)을 반환
    def get_template_names(self) -> list[str]:
        if self.request.htmx:
            template_name = "blog/_tag_list.html"
        else:
            template_name = "blog/tag_list.html"
        return [template_name]


# TagListView라는 클래스 기반 뷰를 실제 HTTP 요청을 처리할 수 있는 뷰 함수로 변환하여 tag_list에 할당 
# 이 뷰 함수는 urls.py에 등록되어, 웹 서버가 해당 URL로 들어오는 요청을 처리하는 데 사용됩니다.
tag_list = TagListView.as_view()


# 이 뷰는 새로운 Tag를 생성하거나 기존 Tag를 수정하는 폼을 처리
@login_required_hx
def tag_new(request, pk=None):
    if pk:  # instance는 pk가 주어지면 해당 Tag 객체로 초기화되고, 없으면 None으로 새 태그를 생성
        instance = get_object_or_404(Tag, pk=pk)
    else:
        instance = None

    if request.method == "GET": # 새로운 태그를 생성하거나 기존 태그를 수정하는 폼을 표시
        form = TagForm(instance=instance)
    else: # 제출된 데이터를 기반으로 TagForm을 처리하고, 유효한 경우 Tag를 저장ㄴ
        form = TagForm(data=request.POST, instance=instance)
        if form.is_valid():
            form.save() # 태그 저장 후, HTMX를 사용하여 클라이언트 이벤트(refresh-tag-list)를 트리거하여 태그 목록을 갱신
            messages.success(request, "태그를 저장했습니다.")
            response = render(request, "core/_messages_as_event.html")
            response = trigger_client_event(response, "refresh-tag-list")
            return response

    return render(
        request,
        "blog/_tag_form.html",
        {
            "form": form,
        },
    )

# 주어진 pk로 기존 태그를 수정. 사실상 tag_new 뷰의 별칭
def tag_edit(request, pk):
    return tag_new(request, pk)

# 특정 Tag에 대한 정보를 부분 템플릿(_tag_list_item.html)에 렌더링하여 반환
def tag_list_item(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    return render(request, "blog/_tag_list_item.html", {"tag": tag})

# 주어진 pk에 해당하는 Tag를 삭제합니다. DELETE 요청만 허용
@require_http_methods(["DELETE"]) 
def tag_delete(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    tag.delete()
    return HttpResponse("") # 태그가 삭제되면 빈 응답(HttpResponse(""))을 반환


def test(request):
    return render(request, "blog/test.html")
