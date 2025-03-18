FROM python:3.12

WORKDIR /slack_app

COPY . /slack_app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]