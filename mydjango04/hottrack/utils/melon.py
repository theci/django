import json
from typing import List, Dict
from urllib.parse import urlencode
from urllib.request import Request, urlopen

#HEADERS는 HTTP 요청 헤더를 정의하는 부분입니다. 
# 주로 User-Agent 헤더를 설정하여, 웹 서버에 브라우저에서 요청이 들어온 것처럼 보이게 만듭니다. 이는 멜론 서버가 봇으로 인식하는 것을 방지하려는 용도입니다.
HEADERS = { 
    "User-Agent": ( # User-Agent 문자열은 브라우저에서 요청을 보내는 것처럼 보이게 하며, 크롬 브라우저의 60버전의 Windows 10 64비트 환경을 나타냅니다.
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36"
    ),
}


# Song 모델의 melon_uid 필드는 문자열 타입이었고, 이를 id 정수 타입으로 변경

# 이 함수는 멜론에서 곡의 좋아요 수를 가져오는 함수입니다
def get_likes_dict(melon_uid_list: List[int]) -> Dict[int, int]: # melon_uid_list: List[int] 타입으로 멜론 곡의 고유 ID(정수 값)들을 전달받습니다.
    url = "https://www.melon.com/commonlike/getSongLike.json"
    params = urlencode( 
        {
            # 정수는 문자열로 변환해야만 join이 가능합니다.
            "contsIds": ",".join(map(str, melon_uid_list)), # 멜론의 API에 요청을 보내기 위한 URL과 파라미터를 합칩니다. 
        } # 예를 들어, [1, 2, 3]이 [ "1", "2", "3" ] 형태로 변환되어 contsIds=1,2,3와 같은 형식으로 URL에 포함됩니다.
    )

    url_with_params = url + "?" + params # 앞서 생성한 URL에 인코딩된 파라미터를 결합하여 최종 요청 URL을 만듭니다. 
    # 예를 들어, https://www.melon.com/commonlike/getSongLike.json?contsIds=1,2,3와 같은 형태로 요청이 완성됩니다.

    request = Request(url_with_params, headers=HEADERS) # Request 객체는 URL과 헤더를 포함한 HTTP 요청을 생성합니다.
    result = json.loads(urlopen(request).read()) # urlopen은 요청을 보내고 그에 대한 응답을 받는 함수입니다.
    # 응답은 JSON 형식으로 오기 때문에, json.loads를 사용하여 JSON 데이터를 파이썬 객체로 변환합니다. 이때 result는 JSON 객체(파이썬 딕셔너리)로 변환됩니다.

    # result에서 필요한 데이터를 추출하여, 곡 ID(CONTSID)와 좋아요 수(SUMMCNT)를 키-값 쌍으로 가지는 딕셔너리를 생성합니다.
    likes_dict = {int(song["CONTSID"]): song["SUMMCNT"] for song in result["contsLike"]} 

    return likes_dict # Dict[int, int]: 키 - 각 곡의 멜론 ID(CONTSID), 값 - 그 곡의 좋아요 수(SUMMCNT)를 가지는 딕셔너리를 반환합니다.
