FROM python:3.10-alpine

ENV PYTHONUNBUFFERED 1
ENV TZ={{cookiecutter.timezone}}}

RUN mkdir /app
WORKDIR /app

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories
RUN apk add --no-cache make gcc g++ jpeg-dev zlib-dev libc-dev libxml2-dev libxslt-dev libressl-dev musl-dev libffi-dev openssl-dev mariadb-connector-c-dev libpq-dev pcre pcre-dev tzdata
RUN ln -sf /usr/share/zoneinfo/{{cookiecutter.timezone}}} /etc/localtime
RUN python -m pip install --upgrade pip

COPY requirements.txt /app
RUN pip install -r requirements.txt -i https://pypi.douban.com/simple/
RUN apk del make gcc g++ libressl-dev musl-dev libffi-dev

RUN rm -rf /var/cache/apk/*
RUN rm -rf /root/.cache/
RUN find /usr/local/lib/python3.10/* -name *.pyc | xargs rm -rf -

COPY . /app

RUN chmod +x /app/start.sh
ENTRYPOINT ["sh", "start.sh"]
EXPOSE 8000