from django.contrib import messages
from django.shortcuts import render


def index(request):
    messages.debug(request, "디버그 메시지") # 디버그 메시지 (디버깅 중에 유용한 정보).
    messages.info(request, "정보 메시지") # 정보 메시지 (사용자에게 전달할 일반적인 정보).
    messages.success(request, "성공 메시지") # 성공 메시지 (작업이 성공적으로 완료되었음을 알리는 메시지).
    messages.warning(request, "경고 메시지") # 경고 메시지 (사용자에게 주의가 필요함을 알리는 메시지).
    messages.error(request, "에러 메시지") # 에러 메시지 (에러나 문제 발생 시 보여주는 메시지).

    return render(request, "core/index.html")
