FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

COPY requirements.txt /tmp/

RUN pip install --requirement /tmp/requirements.txt

COPY . /tmp/

COPY ./app /app/app