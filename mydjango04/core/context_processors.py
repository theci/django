# core/context_processors.py

from django.contrib import messages

# Django의 메시지 시스템에서 메시지를 지연 로딩하는 함수입니다. 메시지는 실제로 사용자가 페이지를 요청할 때까지 로드되지 않으며, inner 함수에서 메시지 목록을 가져와 반환합니다. 
# 이를 통해 메시지가 실제로 소비되는 시점에 메시지를 로드하게 되어 성능을 최적화할 수 있습니다.
def lazy_messages_list(request):
    # 장고 템플릿에서는 인자없는 함수를 호출할 수 있습니다.
    # 아래 messages_list 함수에서 사전을 만들 때 메시지 목록을 가져오는 것이 아니라, 메시지를 소비하는 시점에 메시지를 가져오도록 지연시킵니다.
    def inner():
        message_list = messages.get_messages(request) # Django의 메시지 시스템을 통해 현재 요청에 대한 메시지를 가져옵니다.

        # 메시지는 level_tag와 message를 포함하는 사전 형식으로 반환됩니다.
        return [
            {
                "level_tag": message.level_tag,
                "message": message.message,
            }
            for message in message_list
        ]

    return inner

# messages_list라는 이름으로 lazy_messages_list를 반환합니다. 이 함수는 Django의 컨텍스트 프로세서로 설정되어, 템플릿에서 자동으로 메시지 목록을 사용할 수 있게 됩니다.
def messages_list(request):
    return {
        "messages_list": lazy_messages_list(request),
    }
