from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler
from rest_framework.views import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return Response(
            {
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "msg": f"Internal Server Error: {exc}",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            exception=True,
        )

    for index, value in enumerate(response.data):
        if index == 0:
            key = value
            value = response.data[key]

            if isinstance(value, str):
                error_msg = value
            else:
                error_msg = f"{key}: {value[0]}"

    error_code = 999 if response.status_code == 200 else response.status_code
    return Response(
        {"code": error_code, "msg": error_msg},
        status=response.status_code,
        exception=True,
    )


class CustomAPIError(APIException):
    status_code = 200
    default_detail = "Custom API Error"
    default_code = 999
