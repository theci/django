# blog/management/commands/load_blog_posts.py


from random import choice

import requests
from accounts.models import User
from blog.models import Category, Comment, Post, Tag
from django.core.management import BaseCommand

SAMPLE_POSTS_JSON_URL = (
    "https://raw.githubusercontent.com/pyhub-kr/dump-data/main/sample-blog-post.json"
)

SAMPLE_COMMENTS_TXT_URL = (
    "https://raw.githubusercontent.com/pyhub-kr/dump-data/main/sample-blog-comments.txt"
)

# 외부의 샘플 JSON과 TXT 파일에서 데이터를 다운로드하여, 블로그 애플리케이션에 카테고리, 태그, 포스팅, 댓글 등의 데이터를 자동으로 생성하는 기능을 제공합니다. 
# 이를 통해 블로그 애플리케이션의 데이터를 자동으로 채울 수 있습니다.
class Command(BaseCommand):
    help = "샘플 데이터로부터 블로그 애플리케이션에 데이터를 추가합니다."

    # 인자로 JSON 주소를 지정하지 않으면, 디폴트 주소를 활용
    def add_arguments(self, parser): # 명령어에 전달할 수 있는 인수들을 정의
        parser.add_argument("posts_json_url", nargs="?", default=SAMPLE_POSTS_JSON_URL) # 포스트 데이터를 가져올 JSON 파일의 URL을 지정하는 인수
        parser.add_argument(
            "comments_txt_url", nargs="?", default=SAMPLE_COMMENTS_TXT_URL # 댓글 데이터를 가져올 TXT 파일의 URL을 지정하는 인수
        )
        parser.add_argument( # --clear 인수가 True로 지정되면 기존 데이터를 삭제한 후 새 데이터를 삽입합니다.
            "--clear",
            action="store_true",
            help="새 데이터를 저장하기 전에 기존 데이터를 모두 삭제합니다.",
        )

    def handle(self, *args, **options): # 명령어가 실행될 때 실제로 수행할 작업을 정의합니다.
        posts_json_url = options["posts_json_url"] # posts_json_url과 comments_txt_url에서 샘플 데이터를 다운로드
        comments_txt_url = options["comments_txt_url"]

        is_clear_data = options["clear"] # 

        if is_clear_data is True: # --clear 옵션이 True일 경우, 기존 데이터를 삭제하기 위해 clear_data() 함수를 호출
            clear_data()

        print("JSON/TXT 다운로드 중 ...")

        # 각각 포스트 JSON 데이터와 댓글 TXT 데이터를 저장합니다.
        res = requests.get(posts_json_url)
        res.raise_for_status()
        orig_post_list = res.json()

        res = requests.get(comments_txt_url)
        res.raise_for_status()
        orig_comments_txt = res.text

        # 다운로드한 데이터를 기반으로 create_categories, create_tags, create_posts, create_comments 함수를 호출하여 각각 카테고리, 태그, 포스트, 댓글을 생성합니다.
        create_categories(orig_post_list)
        create_tags(orig_post_list)
        create_posts(orig_post_list)
        create_comments(orig_comments_txt)

# 기존에 저장된 카테고리, 포스트, 태그 데이터를 모두 삭제하는 함수
def clear_data():
    print("카테고리 데이터 삭제 중 ...")
    Category.objects.all().delete()
    print("포스팅 데이터 삭제 중 ...")
    Post.objects.all().delete()
    print("태그 데이터 삭제 중 ...")
    Tag.objects.all().delete()


def create_categories(orig_post_list):
    """카테고리 생성"""

    existed_category_name_set = set(
        Category.objects.values_list("name", flat=True).distinct()
    )
    category_name_set = {orig_post["category_name"] for orig_post in orig_post_list}

    category_list = [
        Category(name=category_name)
        for category_name in category_name_set - existed_category_name_set
    ]

    if category_list:
        print(f"{len(category_list)} 개의 카테고리 생성")
        Category.objects.bulk_create(category_list, batch_size=1000)


def create_tags(orig_post_list):
    """태그 생성"""

    existed_tag_name_set = set(Tag.objects.values_list("name", flat=True).distinct())

    tag_name_set = set()
    for orig_post in orig_post_list: # 모든 카테고리와 태그, 사용자 목록을 가져와서 category_dict, tag_dict, user_list로 저장
        tag_name_set.update(orig_post["tag_list"])

    tag_list = [Tag(name=tag_name) for tag_name in tag_name_set - existed_tag_name_set]

    if tag_list:
        print(f"{len(tag_list)} 개의 태그 생성")
        Tag.objects.bulk_create(tag_list, batch_size=1000) # 존재하지 않는 태그들만 Tag 모델로 생성하고, bulk_create로 한 번에 저장합니다.


def create_posts(orig_post_list):
    """포스팅 생성"""

    category_dict = {category.name: category for category in Category.objects.all()}
    tag_dict = {tag.name: tag for tag in Tag.objects.all()}

    user_list = list(User.objects.all())

    post_list = []
    for orig_post in orig_post_list:
        post = Post(
            category=category_dict[orig_post["category_name"]],
            author=choice(user_list),
            title=orig_post["title"],
            status=choice([Post.Status.DRAFT, Post.Status.PUBLISHED]),
            content=orig_post["content"],
        )
        post._tag_list = orig_post["tag_list"]
        post.slugify()
        post_list.append(post)

    if post_list:
        print(f"{len(post_list)} 개의 포스팅 생성")
        Post.objects.bulk_create(post_list, batch_size=1000) # bulk_create로 포스트들을 한 번에 저장하고, 이후 각 포스트에 해당하는 태그들을 태그 관계로 추가합니다.

        for post in post_list:
            _tag_list = [tag_dict[tag_name] for tag_name in post._tag_list]
            post.tag_set.add(*_tag_list)


def create_comments(orig_comments_txt):
    user_list = list(User.objects.all())
    post_list = list(Post.objects.all())

    # 데이터 3배 뻥튀기
    lines = (
        orig_comments_txt + "\n" + orig_comments_txt + "\n" + orig_comments_txt
    ).splitlines()

    comment_list = []
    for message in lines:
        if message := message.strip():
            comment = Comment(
                author=choice(user_list), post=choice(post_list), message=message
            )
            comment_list.append(comment)

    if comment_list:
        print(f"{len(comment_list)} 개의 댓글 생성")
        Comment.objects.bulk_create(comment_list, batch_size=1000)
