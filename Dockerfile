FROM python:3

RUN pip install scrapy

WORKDIR /scrapy

COPY scrapy.cfg .
COPY fass fass

