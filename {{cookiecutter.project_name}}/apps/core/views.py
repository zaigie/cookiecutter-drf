import random
from django.utils.translation import gettext_lazy as _
from rest_framework import mixins
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from custom.exceptions import CustomAPIError
from utils.redis_func import Client as RedisClient
from utils.verify import send_email, send_sms

from core.models import User
import core.serializers as serializers


class UserViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    lookup_field = "username"
    queryset = User.query.all()
    serializer_class = serializers.UserSerializer


class LoginOrRegisterView(GenericAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = User.query.all()
    serializer_class = serializers.LoginOrRegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 校验验证码
        r = RedisClient()
        phone = serializer.validated_data["phone"]
        verification_code = serializer.validated_data["verification_code"]
        key = f"register_{phone}"
        if r.get(key):
            if str(verification_code) == r.get(key):
                r.delete(key)
            else:
                raise CustomAPIError(_("Verification code error"))
        else:
            raise CustomAPIError(
                _("The verification code does not exist or has expired")
            )

        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        )


class PhoneVerificationView(GenericAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = User.query.all()
    serializer_class = serializers.PhoneVerificationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        verification_code = str(random.randint(100000, 999999))
        send_sms(phone, verification_code, "register")
        return Response({"message": "ok"})


# class VerificationViewSet(GenericViewSet):
#     authentication_classes = []
#     permission_classes = [AllowAny]

#     def send(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         verification_type = request.GET.get("validation_type")
#         verification = serializer.validated_data.get("verification")

#         if User.query(**{verification_type: verification}).first():
#             raise CustomAPIError(_("The user already exists."))

#         verification_code = str(uuid4())[:6]

#         if verification_type == "email":
#             send_email(verification, verification_code, self.action)
#         elif verification_type == "phone":
#             send_sms(verification, verification_code, self.action)

#         return Response({"message": _("Verification code sent successfully")})

#     @action(methods=["POST"], detail=False)
#     def register(self, request, *args, **kwargs):
#         return self.send(request, *args, **kwargs)

#     @action(methods=["POST"], detail=False, url_path="update")
#     def update_verification(self, request, *args, **kwargs):
#         return self.send(request, *args, **kwargs)

#     @action(methods=["POST"], detail=False)
#     def reset(self, request, *args, **kwargs):
#         return self.send(request, *args, **kwargs)
