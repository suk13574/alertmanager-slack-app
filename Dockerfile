FROM python:3.12

WORKDIR /slack_app

COPY . /slack_app

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

CMD ["gunicorn", "--bind", "0.0.0.0:3000", "main:create_app()"]