import requests  # pip install requests
from pprint import pprint  # 가독성좋게 출력하기 위한 모듈

json_url = "https://raw.githubusercontent.com/pyhub-kr/dump-data/main/melon/melon-20230906.json"

response = requests.get(json_url)
response.raise_for_status()  # 비정상 응답을 받았다면, HTTPError를 발생시킵니다.

song_list = response.json()

print(type(song_list), len(song_list), type(song_list[0]))
pprint(song_list)
# [{'가수': 'AKMU (악뮤)',
#   '곡명': 'Love Lee',
#   '곡일련번호': '36713849',
#   '순위': '1',
#   '앨범': 'Love Lee',
#   '좋아요': 42085,
#   '커버이미지_주소': 'https://cdnimg.melon.co.kr/...'},