# blog/management/commands/load_blog_tags.py

import requests  # pip install requests
from django.core.management import BaseCommand

from blog.models import Tag

# 외부 URL에서 텍스트 파일을 읽어와, 해당 텍스트 파일에 포함된 태그들을 데이터베이스에 존재하지 않는 태그만 추가하는 기능
class Command(BaseCommand):
    def handle(self, *args, **options): # args는 위치 인수, options는 선택적 키워드 인수
        txt_url = (
            "https://raw.githubusercontent.com/pyhub-kr/dump-data/main/tags-example.txt"
        )

        txt = requests.get(txt_url).text
        tag_set = {line.strip() for line in txt.splitlines()} #  텍스트 파일에서 각 줄을 분리하여 리스트 형태로 반환하여 각 줄의 앞뒤 공백을 제거한 뒤 집합으로 반환

        existed_tag_set = set(Tag.objects.all().values_list("name", flat=True)) # flat=True는 단일 값의 리스트로 반환
        making_tag_set = tag_set - existed_tag_set # tag_set에서 existed_tag_set을 빼는 연산을 통해, 아직 데이터베이스에 존재하지 않는 태그들을 찾습니다. 이 차집합 연산의 결과는 새로 추가할 태그들을 포함하는 making_tag_set입니다.

        tag_list = [Tag(name=tag_name) for tag_name in making_tag_set] # making_tag_set에 있는 각 태그 이름에 대해 Tag 객체를 생성하여 tag_list에 저장. 이는 Tag 모델 인스턴스를 리스트로 만드는 과정입니다.
        created_tag_list = Tag.objects.bulk_create(tag_list) # Tag 인스턴스들을 한 번에 데이터베이스에 추가
        self.stdout.write(f"{len(created_tag_list)} tags created") # 생성된 태그의 수를 출력
