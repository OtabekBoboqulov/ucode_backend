from functools import wraps
from rest_framework.response import Response
from rest_framework import status


def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        print(request.user.is_authenticated)
        print(request.user.is_staff)
        if request.user.is_authenticated and request.user.is_staff:
            return view_func(request, *args, **kwargs)
        return Response({"error": "Staff access required"}, status=status.HTTP_403_FORBIDDEN)

    return wrapper
