FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.22 /uv /uvx /bin/

WORKDIR /app

COPY requirements.txt requirements.txt
COPY Archipelago-0.6.8/requirements.txt ./Archipelago-0.6.8/requirements.txt
RUN uv pip install --system --no-cache -r requirements.txt

COPY . .

# Create missing folders that archipelago expects
RUN mkdir -p /app/Archipelago-0.6.8/Players
RUN mkdir -p /app/Archipelago-0.6.8/data/options
RUN mkdir -p /app/Archipelago-0.6.8/data/sprites
RUN mkdir -p /app/Archipelago-0.6.8/data/lua

EXPOSE 5001

CMD ["gunicorn", "app:app"]