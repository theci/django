#!/usr/bin/env python # 스크립트가 Python으로 실행되도록 합니다. 이를 통해 해당 파일을 실행할 때 명시적으로 python 명령어를 사용하지 않아도 됩니다.
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings") # Django의 설정 모듈을 지정
    try:
        from django.core.management import execute_from_command_line # Django 관리 명령어를 실행할 수 있는 함수를 가져옵니다.
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # 커맨드라인 인수(sys.argv)를 기반으로 Django 명령어를 실행합니다. ex) python manage.py runserver와 같은 명령어를 처리합니다.
    execute_from_command_line(sys.argv) 


if __name__ == "__main__":
    main()
