# -*- coding: utf-8 -*-
import json

from django.core.mail import send_mail
from django.conf import settings

from utils.redis_func import Client as RedisClient


# Custom SMS Provider
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
    TencentCloudSDKException,
)
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.sms.v20190711 import models, sms_client


def send_sms(phone_number, code, type):
    """Since Django does not currently have a good SMS sending plugin,
    if you need to use the SMS authentication function,
    you need to use the SMS provider's SDK to rewrite the send_sms function to achieve related functions

    Args:
        phone_number (str): phone number
        code (str): verify code (could be random string or number)
        type (str): sms template type [register, update, reset]

    Returns:
        bool: True if send success, False if send failed
    """

    cred = credential.Credential(settings.SMS_SECRET_ID, settings.SMS_SECRET_KEY)
    httpProfile = HttpProfile()
    httpProfile.reqMethod = "POST"
    httpProfile.reqTimeout = 30
    httpProfile.endpoint = settings.SMS_ENDPOINT
    clientProfile = ClientProfile()
    clientProfile.signMethod = "TC3-HMAC-SHA256"
    clientProfile.language = "en-US"
    clientProfile.httpProfile = httpProfile
    client = sms_client.SmsClient(cred, "ap-guangzhou", clientProfile)
    req = models.SendSmsRequest()
    req.SmsSdkAppid = settings.SMS_SDK_APPID
    req.Sign = settings.SMS_SIGN
    req.ExtendCode = ""
    req.SessionContext = ""
    req.SenderId = ""
    req.PhoneNumberSet = ["+86" + phone_number]
    req.TemplateID = settings.SMS_TEMPLATES[type]
    req.TemplateParamSet = [code]
    resp = client.SendSms(req)
    ret = json.loads(resp.to_json_string(indent=2))
    if ret["SendStatusSet"][0]["Code"] != "Ok":
        raise TencentCloudSDKException
    set_verification_code(type, phone_number, code)
    return True


def send_email(email, code, type):
    TYPES = {
        "register": "{{cookiecutter.project_name_cn}}注册",
        "update": "{{cookiecutter.project_name_cn}}邮箱绑定",
        "reset": "{{cookiecutter.project_name_cn}}密码重置",
    }
    title = TYPES[type]
    content = f"您的验证码为{code}。有效期为10分钟，请尽快输入！"
    ret = send_mail(title, content, settings.EMAIL_FROM, [email], fail_silently=True)
    if ret != 1:
        raise Exception
    set_verification_code(type, email, code)
    return True


def set_verification_code(type, verification, code):
    """Set verify code to redis

    Args:
        type (str): verify code type [register, update, reset]
        verification (str): verification
        code (str): verify code (could be random string or number)
    """
    r = RedisClient()
    r.set(f"{type}_{verification}", code)
