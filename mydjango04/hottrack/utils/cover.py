# melon/utils/cover.py

from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont, __version__ as pil_version


# PIL 버전 10부터 변경되는 동작이 있어서, 버전을 체크해줍니다.
PIL_VERSION = tuple(map(int, pil_version.split(".")))


def make_cover_image(cover_url: str, text: str, canvas_size: int = 256) -> Image:
    canvas = Image.new("RGB", (canvas_size, canvas_size), "white")
    draw = ImageDraw.Draw(canvas)

    res = requests.get(cover_url) # requests.get(cover_url)을 사용하여 URL에서 이미지를 다운로드
    if res.ok: # res.ok가 True이면 이미지 다운로드가 성공한 경우입니다. 
        cover_image = Image.open(BytesIO(res.content)) # 이미지 파일을 BytesIO로 열어 cover_image 객체로 변환
        cover_image.thumbnail((canvas_size, canvas_size)) # thumbnail() 메서드를 사용하여 캔버스 크기에 맞게 이미지를 축소한 후, 캔버스에 붙여넣습니다.
        canvas.paste(cover_image, (0, 0))
    else:
        # 이미지 다운로드에 실패했을 경우, X 표시를 그립니다.
        draw.line((0, 0, canvas_size, canvas_size), fill="red")
        draw.line((0, canvas_size, canvas_size, 0), fill="blue")

    # 사선 스트라이프 패턴 그리기 (회색, 선 굵기 3)
    for i in range(-canvas_size, canvas_size, 10): # range(-canvas_size, canvas_size, 10)로 일정 간격(10픽셀)마다 선을 그려 사선 패턴을 생성합니다.
        draw.line([(i, 0), (i + canvas_size, canvas_size)], fill="#F0F0F0", width=2) # 캔버스에 회색("#F0F0F0") 사선 스트라이프 패턴을 그립니다

    # 맑은고딕 (윈도우), 애플고딕(맥) 폰트 사용하기
    trying_font_names = ["malgunsl.ttf", "AppleGothic.ttf"] # 텍스트를 그릴 폰트를 설정합니다. 먼저 malgunsl.ttf와 AppleGothic.ttf 폰트를 시도합니다.
    for font_name in trying_font_names:
        try:
            font = ImageFont.truetype(font=font_name, size=32) # ImageFont.truetype()은 주어진 폰트 파일에서 truetype 폰트를 로드하는 함수로, 폰트 크기를 32로 설정합니다.
            break
        except IOError:
            continue
    else:
        font = ImageFont.load_default() # 만약 두 폰트가 모두 존재하지 않으면 기본 폰트(ImageFont.load_default())를 사용합니다.

    # 텍스트를 그릴 시작 좌표 x, y 좌표 계산하기
    if PIL_VERSION >= (10,):
        x0 = int(canvas.width / 2)
        y0 = int(canvas.height / 2)
        bb_l, bb_t, bb_r, bb_b = draw.textbbox(xy=(0, 0), text=text, font=font)
        x = x0 - (bb_r - bb_l) / 2
        y = y0 - (bb_b - bb_t) / 2
    else:
        text_width, text_height = draw.textsize(text=text, font=font)
        x = (canvas.width - text_width) / 2
        y = (canvas.height - text_height) / 2

    # 지정 좌표, 폰트, 색상으로 텍스트 그리기
    draw.text(xy=(x, y), text=text, fill="black", font=font) # 계산된 좌표 (x, y)에 주어진 텍스트를 검은색("black")으로 그립니다. 텍스트는 중앙에 배치됩니다.

    return canvas # 최종적으로 생성된 이미지를 반환합니다.
