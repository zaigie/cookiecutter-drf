from uuid import uuid4

from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
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


class CreateUserView(GenericAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = User.query.all()

    def get_serializer_class(self):
        validation_type = self.request.GET.get("validation_type")
        if validation_type == "email":
            return serializers.EmailRegisterSerializer
        elif validation_type == "phone":
            return serializers.PhoneRegisterSerializer
        if settings.ALLOW_FREE_REGISTION:
            return serializers.CreateUserSerializer
        raise CustomAPIError(_("Unsupported registration authentication mode"))

    def post(self, request, *args, **kwargs):
        password = make_password(request.data["password"])
        request.data["password"] = password

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if self.serializer_class != serializers.CreateUserSerializer:
            verification_type = self.request.GET.get("validation_type")
            verification = serializer.validated_data.get(verification_type)
            verification_code = serializer.validated_data.get("verification_code")

            r = RedisClient()
            key = f"register_{verification}"
            if r.get(key):
                if str(verification_code) == r.get(key):
                    r.delete(key)
                else:
                    raise CustomAPIError(_("Verification code error"))
            else:
                raise CustomAPIError(
                    _("The verification code does not exist or has expired")
                )
        serializer.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)


class LoginView(GenericAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = User.query.all()

    def get_serializer_class(self):
        validation_type = self.request.GET.get("validation_type")
        if validation_type == "email":
            return serializers.EmailLoginSerializer
        elif validation_type == "phone":
            return serializers.PhoneLoginSerializer
        return serializers.BasicLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verification_type = request.GET.get("validation_type")
        if not verification_type:
            verification_type = "username"
        verification = serializer.validated_data.get(verification_type)
        password = serializer.validated_data.get("password")

        user = User.query(**{verification_type: verification}).first()
        if not (user and user.check_password(password)):
            raise CustomAPIError(
                _("The user does not exist or the password is incorrect")
            )

        user.update_last_login()
        refresh = RefreshToken.for_user(user)
        data = {
            "username": user.username,
            "token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }
        return Response(data)


class UserVerificationUpdateViewSet(mixins.UpdateModelMixin, GenericViewSet):
    lookup_field = "username"
    queryset = User.query.all()
    serializer_class = serializers.UserVerificationUpdateSerializer

    def perform_update(self, serializer):
        if serializer.validated_data.get("email"):
            verification_type = "email"
        elif serializer.validated_data.get("phone"):
            verification_type = "phone"
        else:
            raise CustomAPIError(_("Unsupported verification type"))

        verification = serializer.validated_data.get(verification_type)
        verification_code = serializer.validated_data.get("verification_code")

        if User.query(**{verification_type: verification}).first():
            raise CustomAPIError(_("Verification type or already exists"))

        r = RedisClient()
        key = f"update_{verification}"
        if r.get(key):
            if str(verification_code) == r.get(key):
                r.delete(key)
            else:
                raise CustomAPIError(_("Verification code error"))
        else:
            raise CustomAPIError(
                _("The verification code does not exist or has expired")
            )

        serializer.save()


class UserPasswordUpdateViewSet(mixins.UpdateModelMixin, GenericViewSet):
    lookup_field = "username"
    queryset = User.query.all()
    serializer_class = serializers.PasswordUpdateSerializer

    def perform_update(self, serializer):
        old_password = serializer.validated_data.get("old_password")
        new_password = serializer.validated_data.get("new_password")

        if not self.request.user.check_password(old_password):
            raise CustomAPIError(_("The old password is incorrect"))

        new_password = make_password(new_password)

        serializer = serializers.UserPasswordUpdateSerializer(
            self.request.user, data={"password": new_password}, partial=True
        )

        serializer.save()


class VerificationViewSet(GenericViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        validation_type = self.request.GET.get("validation_type")
        if validation_type == "email":
            return serializers.EmailVerificationSerializer
        elif validation_type == "phone":
            return serializers.PhoneVerificationSerializer
        raise CustomAPIError(_("Unsupported registration authentication mode"))

    def send(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verification_type = request.GET.get("validation_type")
        verification = serializer.validated_data.get(verification_type)

        if User.query(**{verification_type: verification}).first():
            raise CustomAPIError(_("The user already exists."))

        verification_code = str(uuid4())[:6]

        if verification_type == "email":
            send_email(verification, verification_code, self.action)
        elif verification_type == "phone":
            send_sms(verification, verification_code, self.action)

        return Response({"message": _("Verification code sent successfully")})

    @action(methods=["POST"], detail=False)
    def register(self, request, *args, **kwargs):
        return self.send(request, *args, **kwargs)

    @action(methods=["POST"], detail=False)
    def update(self, request, *args, **kwargs):
        return self.send(request, *args, **kwargs)

    @action(methods=["POST"], detail=False)
    def reset(self, request, *args, **kwargs):
        return self.send(request, *args, **kwargs)
