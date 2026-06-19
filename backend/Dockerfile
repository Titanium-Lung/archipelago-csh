FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt requirements.txt
COPY Archipelago-0.6.7/requirements.txt ./Archipelago-0.6.7/requirements.txt
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5001

CMD ["python3", "app.py"]