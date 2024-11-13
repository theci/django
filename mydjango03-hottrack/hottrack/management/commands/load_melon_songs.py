# hottrack/management/commands/load_melon_songs.py

import json
from urllib.request import urlopen

from django.core.management import BaseCommand

from hottrack.models import Song


class Command(BaseCommand): # GitHub에 호스팅된 외부 JSON 파일에서 멜론 차트 데이터를 불러와 Song 모델에 저장하는 작업
    help = "Load songs from melon chart"

    def handle(self, *args, **options):
        melon_chart_url = "https://raw.githubusercontent.com/pyhub-kr/dump-data/main/melon/melon-20230910.json"
        json_string = urlopen(melon_chart_url).read().decode("utf-8") # 지정된 URL에서 JSON 데이터를 가져옵니다

        # Song 인스턴스들은 아직 데이터베이스에 저장되지 않았습니다.
        # 가져온 JSON을 반복문을 통해 json.loads()로 파싱
        # Song.from_dict() 메서드를 호출하여 Song 객체를 만듭니다.
        song_list = [Song.from_dict(song_dict) for song_dict in json.loads(json_string)]  
        print("loaded song_list :", len(song_list))

        # Song 인스턴스들은 한 번에 INSERT 쿼리를 생성하여, INSERT 성능을 높입니다.
        Song.objects.bulk_create(song_list, batch_size=100, ignore_conflicts=True) # 배치사이즈 100개, 중복 데이터 무시

        total = Song.objects.all().count()
        print("saved song_list :", total)
