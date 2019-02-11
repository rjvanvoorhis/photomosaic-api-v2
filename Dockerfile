FROM python:3.6-alpine
COPY ./requirements.txt /code/requirements.txt
WORKDIR /code
RUN apk add --no-cache jpeg-dev zlib-dev
RUN apk add gcc g++ \
    && apk add linux-headers\
    && apk add bash gifsicle
RUN pip3 install -r requirements.txt
COPY . /code
CMD ["gunicorn", "--log-level", "debug", "--workers", "2", "--name", "app", "-b", "0.0.0.0:5000", "--timeout", "160", "wsgi:app"]