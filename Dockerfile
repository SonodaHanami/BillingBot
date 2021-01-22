FROM python:3.8-slim-buster

RUN mkdir -p /bot
WORKDIR /bot

# time zone
RUN cp /usr/share/zoneinfo/Asia/Tokyo /etc/localtime && \
    echo 'Asia/Tokyo' >/etc/timezone

# python dependencies
COPY requirements.txt /bot/requirements.txt
RUN pip install -r requirements.txt
