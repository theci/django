# zipcode_sample_download.py

import os
import csv
from typing import Dict, Iterator, Tuple
from urllib.request import urlretrieve
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()


def get_code_and_name_from_csv(zipcode_csv_path: str) -> Iterator[Tuple[str, str]]:
    """CSV 파일에서 우편번호, 시도, 시군구, 도로명을 읽어서, 우편번호와 주소를 생성합니다.

    :param zipcode_csv_path: 우편번호 CSV 파일 경로
    :return: 우편번호, 주소 튜플을 생성(yield)합니다.
    """

    with open(zipcode_csv_path, "rt", encoding="utf-8-sig") as csvfile:
        # utf-8-sig 인코딩은 BOM(Byte Order Mark)을 처리하기 위해 사용

        # CSV 파일을 읽을 때 첫 번째 줄을 필드명으로 사용하고, 각 행을 dict 형태로 읽습니다. 우편번호 CSV 파일은 구분자가 | 입니다.
        csv_reader = csv.DictReader(csvfile, delimiter="|")
        row: Dict
        for row in csv_reader:
            code = row["우편번호"]
            name = "{시도} {시군구} {도로명}".format(**row)
            yield code, name # 튜플로 반환


def main():
    # 파이썬으로 샘플 5000줄을 다운받아 csv_path 경로에 저장합니다. (원본: 531,487줄)
    sample_csv_url = "https://raw.githubusercontent.com/pyhub-kr/dump-data/main/zipcode_db/20231205/%EC%84%9C%EC%9A%B8%ED%8A%B9%EB%B3%84%EC%8B%9C-5000%ED%96%89.txt"
    csv_path = "shop/assets/zipcode_db/20231205/서울특별시.txt"  # 원본: 531,487줄

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)  # 파일을 저장할 폴더를 생성해줍니다.
    urlretrieve(sample_csv_url, csv_path)  # sample_csv_url 경로에서 파일을 다운받아, csv_path 경로에 저장합니다.

    generator = get_code_and_name_from_csv(csv_path) # CSV 파일에서 데이터를 읽어오는 제너레이터 객체를 생성

    print(next(generator))  # 처음 1줄을 가져옵니다.
    print(next(generator))  # 다음 1줄을 가져옵니다.
    print(next(generator))  # 다음 1줄을 가져옵니다.

    for row in generator:
        print(row)


# 이 부분은 이 파일이 직접 실행될 때만 main() 함수가 호출되도록 합니다. 만약 다른 파일에서 이 모듈을 임포트하면 main() 함수는 실행되지 않습니다.
if __name__ == "__main__":
    main()
