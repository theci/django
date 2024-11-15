from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt # post를 테스트하기 위함. 사용x
def coffee_stamp(request): # url로 request 요청이 올 때 처리하는 view 함수
    if request.method == "GET": # GET으로 요청올 때 HTML 폼을 반환
        response = HttpResponse(
            """
            <form method="POST">
                <input type="text" name="phone" placeholder="적립을 위해 휴대폰 번호를 입력해주세요." />
            </form>
            """
        )
    else: # POST로 요청올 때 사용자가 폼에 입력한 휴대폰 번호를 가져와서 count를 +1한 후 적립된 스탬프(주문 횟수)를 HTML 응답으로 반환
        phone = request.POST["phone"]
        request.session["phone"] = phone

        order_count = request.session.get(phone, 0)
        order_count += 1
        request.session["order_count"] = order_count

        response = HttpResponse(
            f"""
            {phone}님. 적립횟수 : {order_count}<br/>
            10회 이상 스탬프를 찍으셨다면
            <a href="/cafe/free-coffee/">무료커피를 신청해주세요.</a>
            """
        )

    return response


def coffee_free(request):
    phone = request.session.get("phone", "")
    if not phone:
        return redirect("cafe:coffee_stamp")

    order_count = request.session.get("order_count", 0)
    if order_count < 10:
        response = HttpResponse(
            f"{phone}님. 스탬프 {order_count}번 찍으셨어요. {10-order_count}번 찍으시면 무료쿠폰을 받을 수 있습니다."
        )
    else:
        response = HttpResponse(f"{phone}님. 무료쿠폰을 사용하시겠어요?")

    return response
