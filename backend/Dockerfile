FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY requirements.txt requirements.txt
COPY Archipelago-0.6.7/requirements.txt ./Archipelago-0.6.7/requirements.txt
RUN --mount=type=cache,target=/root/.cache/uv uv pip install --system -r requirements.txt

COPY . .

# Create missing folders that archipelago expects
RUN mkdir -p /app/Archipelago-0.6.7/Players
RUN mkdir -p /app/Archipelago-0.6.7/data/options
RUN mkdir -p /app/Archipelago-0.6.7/data/sprites
RUN mkdir -p /app/Archipelago-0.6.7/data/lua

EXPOSE 5001

CMD ["gunicorn", "app:app"]