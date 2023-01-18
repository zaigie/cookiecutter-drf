from rest_framework.renderers import JSONRenderer


class CustomRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if renderer_context:
            if isinstance(data, list):
                res = {"code": 1000, "msg": "success", "data": data}
            else:
                res = {}
                if not data:
                    data = {}
                res["code"] = data.pop("code", 1000)
                res["msg"] = data.pop("msg", "success")
                res["data"] = data
            return super().render(res, accepted_media_type, renderer_context)
        return super().render(data, accepted_media_type, renderer_context)
