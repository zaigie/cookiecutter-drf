FROM python:3.10-alpine

ENV PYTHONUNBUFFERED 1
ENV TZ={{cookiecutter.timezone}}}

RUN mkdir /app
WORKDIR /app

{% if cookiecutter.language == "zh-hans" %}RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories{% endif %}
RUN apk add --no-cache make gcc g++ jpeg-dev zlib-dev libc-dev libxml2-dev libxslt-dev libressl-dev musl-dev libffi-dev openssl-dev pcre pcre-dev tzdata
RUN apk add --no-cache {% if cookiecutter.database == "postgres" %}libpq-dev{% elif cookiecutter.database == "mysql" %}mariadb-connector-c-dev{% endif %}
RUN ln -sf /usr/share/zoneinfo/{{cookiecutter.timezone}}} /etc/localtime
RUN python -m pip install --upgrade pip

COPY requirements.txt /app
RUN pip install -r requirements.txt {% if cookiecutter.language == "zh-hans" %}-i https://pypi.douban.com/simple/{% endif %}

RUN apk del make gcc g++ libressl-dev musl-dev libffi-dev
RUN rm -rf /var/cache/apk/*
RUN rm -rf /root/.cache/
RUN find /usr/local/lib/python3.10/* -name *.pyc | xargs rm -rf -

COPY . /app

RUN chmod +x /app/start.sh
ENTRYPOINT ["sh", "start.sh"]
EXPOSE 8000
