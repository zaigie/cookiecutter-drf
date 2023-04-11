from django.urls import path, include
from core.views import UserViewSet, LoginOrRegisterView, PhoneVerificationView
from rest_framework_nested import routers

router = routers.DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
# router.register(r"verification", VerificationViewSet, basename="verification")
user_router = routers.NestedDefaultRouter(router, r"users", lookup="user")
urlpatterns = [
    path(r"login/", LoginOrRegisterView.as_view()),
    path(r"verification/phone", PhoneVerificationView.as_view()),
    path(r"", include(router.urls)),
    path(r"", include(user_router.urls)),
]
