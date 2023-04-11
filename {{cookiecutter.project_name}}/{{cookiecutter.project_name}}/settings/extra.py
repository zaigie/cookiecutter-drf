from utils.cfg import cfg

# Storage
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
AWS_ACCESS_KEY_ID = cfg("storage", "key_id")
AWS_SECRET_ACCESS_KEY = cfg("storage", "key")
AWS_STORAGE_BUCKET_NAME = cfg("storage", "bucket")
AWS_S3_ENDPOINT_URL = cfg("storage", "endpoint")
AWS_S3_REGION_NAME = cfg("storage", "region")
AWS_S3_USE_SSL = cfg("storage", "use_ssl", is_bool=True)

# SMS
SMS_SECRET_ID = cfg("sms", "secret_id")
SMS_SECRET_KEY = cfg("sms", "secret_key")
SMS_ENDPOINT = cfg("sms", "endpoint")
SMS_SDK_APPID = cfg("sms", "sdk_appid")
SMS_SIGN = cfg("sms", "signature")
SMS_TEMPLATES = {
    "register": cfg("sms", "register_template"),
    "update": cfg("sms", "update_template"),
    "reset": cfg("sms", "reset_template"),
}

# EMAIL
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = cfg("email", "host")
EMAIL_PORT = cfg("email", "port")
EMAIL_USE_SSL = cfg("email", "use_ssl", is_bool=True)
EMAIL_HOST_USER = cfg("email", "user")
EMAIL_HOST_PASSWORD = cfg("email", "pswd")
EMAIL_FROM = f"{cfg('email', 'from')} <{EMAIL_HOST_USER}>"

# verification code
VERIFICATION_CODE_EXPIRES = 600
VERIFICATION_CODE_INTERVAL = 120

# Admin
ADMIN_SITE_TITLE = cfg("admin", "site_title")
ADMIN_SITE_HEADER = cfg("admin", "site_header")
ADMIN_INDEX_TITLE = cfg("admin", "index_title")

# SIMPLEUI
SIMPLEUI_LOGO = cfg("simpleui", "logo")
SIMPLEUI_STATIC_OFFLINE = cfg("simpleui", "static_offline", is_bool=True)
SIMPLEUI_DEFAULT_THEME = cfg("simpleui", "default_theme")
SIMPLEUI_HOME_INFO = False

# https://simpleui.72wo.com/docs/simpleui/QUICK.html#%E8%8F%9C%E5%8D%95
# SIMPLEUI_CONFIG = {
#     "system_keep": False,
#     "menu_display": ["Core"],
#     "dynamic": False,
#     "menus": [
#         {
#             "app": "core",
#             "name": "Core",
#             "icon": "fas fa-user-shield",
#             "models": [
#                 {"name": "User", "icon": "fa fa-user", "url": "core/user/"},
#             ],
#         },
#     ],
# }
