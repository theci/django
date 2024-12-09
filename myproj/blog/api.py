from core.mixins import (ActionBasedViewSetMixin, JSONResponseWrapperMixin,
                         PermissionDebugMixin, TestFuncPermissionMixin)
from core.pagination import make_pagination_class
from core.permissions import (IsAuthorOrReadonly, PermitSafeMethods,
                              make_drf_permission_class)
from django.db.models import Model
from django.shortcuts import get_object_or_404
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view
from rest_framework.generics import (CreateAPIView, DestroyAPIView,
                                     ListAPIView, RetrieveAPIView,
                                     UpdateAPIView)
from rest_framework.pagination import (CursorPagination, LimitOffsetPagination,
                                       PageNumberPagination)
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .models import Post, Todo
from .serializers import (PostDetailSerializer, PostListSerializer,
                          PostSerializer, TodoSerializer)

# @api_view(["GET"]) # 게시글 목록을 조회
# def post_list(request: Request) -> Response:
#     post_qs = Post.objects.all().defer("content").select_related("author") # content 필드를 쿼리에서 제외하고 author를 미리 조회하여 효율성을 높입니다.
#
#     serializer = PostListSerializer(instance=post_qs, many=True)
#     list_data: ReturnList = serializer.data # 직렬화하여 응답을 반환
#
#     return Response(list_data)

# 게시글 목록 조회
# class PostListAPIView(JSONResponseWrapperMixin, PermissionDebugMixin, ListAPIView):
#     queryset = PostListSerializer.get_optimized_queryset() # 최적화된 쿼리셋을 설정
#     serializer_class = PostListSerializer
#
#
# post_list = PostListAPIView.as_view()
#
# # 특정 게시글을 조회하는 API
# # @api_view(["GET"])
# # def post_detail(request: Request, pk: int) -> Response: # pk로 전달된 게시글의 ID를 통해 게시글을 조회
# #     post = get_object_or_404(Post, pk=pk)
# #
# #     serializer = PostDetailSerializer(instance=post)
# #     detail_data: ReturnDict = serializer.data
# #
# #     return Response(detail_data)
#
# 게시글 생성 API
# class PostRetrieveAPIView(
#     JSONResponseWrapperMixin, PermissionDebugMixin, RetrieveAPIView
# ):
#     queryset = PostDetailSerializer.get_optimized_queryset() 
#     serializer_class = PostDetailSerializer 
#
#
# post_detail = PostRetrieveAPIView.as_view()
#
#
# class PostCreateAPIView(PermissionDebugMixin, CreateAPIView):
#     serializer_class = PostSerializer # 게시글 데이터를 직렬화
#     permission_classes = [IsAuthenticated] # 인증된 사용자만 게시글을 생성
#
#     def perform_create(self, serializer): # 게시글이 저장될 때 author 필드를 요청한 사용자(request.user)로 설정
#         serializer.save(author=self.request.user)
#
#
# post_new = PostCreateAPIView.as_view()
#
#
# class PostUpdateAPIView(PermissionDebugMixin, TestFuncPermissionMixin, UpdateAPIView):
#     TEST_FUNC_PERMISSION_CLASS_NAME = "PostUpdateAPIView"
#
#     queryset = PostSerializer.get_optimized_queryset()
#     serializer_class = PostSerializer
#
#     # permission_classes = [IsAuthorOrReadonly]
#     # permission_classes = [
#     #     make_drf_permission_class(
#     #         class_name="PostUpdateAPIView",
#     #         permit_safe_methods=True,
#     #         has_permission_test_func=lambda request, view: request.user.is_authenticated,
#     #         has_object_permission_test_func=(
#     #             lambda request, view, obj: obj.author == request.user
#     #         ),
#     #     ),
#     # ]
#     permission_classes = [PermitSafeMethods]
#
#     def has_permission(self, request: Request, view: APIView) -> bool:
#         return request.user.is_authenticated
#
#     def has_object_permission(self, request: Request, view: APIView, obj: Post) -> bool:
#         return obj.author == request.user
#
#     # def perform_update(self, serializer):
#     #     serializer.save()
#
#
# post_edit = PostUpdateAPIView.as_view()
#
#
# class PostDestroyAPIView(PermissionDebugMixin, DestroyAPIView):
#     queryset = Post.objects.all()
#     permission_classes = [IsAuthorOrReadonly]
#
#
# post_delete = PostDestroyAPIView.as_view()


# class PageNumberPagination10(PageNumberPagination):
#     page_size = 10


class LimitOffsetPagination10(LimitOffsetPagination):
    max_limit = 10


class PkCursorPagination(CursorPagination):
    ordering = "-pk"


class PostModelViewSet(ActionBasedViewSetMixin, ModelViewSet):
    queryset = Post.objects.all()
    queryset_map = {
        "list": PostListSerializer.get_optimized_queryset(),
        "retrieve": PostDetailSerializer.get_optimized_queryset(),
        "update": PostSerializer.get_optimized_queryset(),
        "partial_update": PostSerializer.get_optimized_queryset(),
        "destroy": Post.objects.all(),
    }
    serializer_class = PostSerializer
    serializer_class_map = {
        "list": PostListSerializer,
        "retrieve": PostDetailSerializer,
        "create": PostSerializer,
        "update": PostSerializer,
        "partial_update": PostSerializer,
    }
    permission_classes = [IsAuthorOrReadonly]

    # pagination_class = make_pagination_class(page_size=10)
    # pagination_class = LimitOffsetPagination10
    # pagination_class = make_pagination_class(
    #     cls_type="limit_offset", page_size=10, max_limit=10
    # )
    # pagination_class = PkCursorPagination
    pagination_class = make_pagination_class(
        "cursor",
        page_size=10,
        cursor_ordering="-pk",
    )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


# post_list = PostModelViewSet.as_view(
#     actions={
#         "get": "list",
#         "post": "create",
#     },
# )
#
# post_detail = PostModelViewSet.as_view(
#     actions={
#         "get": "retrieve",
#         "put": "update",
#         "patch": "partial_update",
#         "delete": "destroy",
#     },
# )


class TodoViewSet(ModelViewSet):
    queryset = Todo.objects.all()
    serializer_class = TodoSerializer
    authentication_classes = [
        SessionAuthentication
    ]  # DRF 기본 설정에서 Basic 인증은 제거하고 세션 인증만 사용하기를 권장
    permission_classes = [IsAuthenticated]  # 인증 요구
    pagination_class = None  # No Pagination
