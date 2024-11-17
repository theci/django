from django.contrib import admin

from .models import Comment, Memo, MemoGroup, Post, Tag


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    pass


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    pass


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass

# InlineModelAdmin의 일종으로, 모델 간 관계를 관리자 페이지에서 한 번에 볼 수 있도록 표시합니다.
class MemoTabularInline(admin.TabularInline): # TabularInline은 표 형식(tabular format)으로 관련 모델의 항목을 나열하는 방식을 제공합니다. 즉, 여러 Memo 객체를 한 화면에 테이블 형식으로 나열합니다.
    model = Memo
    fields = ["message", "status"] # Memo 모델에서 **message**와 status 필드만을 인라인 폼에 표시합니다. 즉, Memo를 관리할 때 이 두 필드만 보여주게 됩니다.

# MemoGroup 모델에 대한 admin(관리자) 인터페이스를 정의하는 클래스
@admin.register(MemoGroup) 
class MemoGroupAdmin(admin.ModelAdmin):
    inlines = [MemoTabularInline] # MemoGroup 모델의 편집 페이지에서 Memo 모델의 항목들을 인라인으로 표시할 수 있게 됩니다.
