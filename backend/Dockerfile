FROM python:3.13 AS build


RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip setuptools wheel cython cymem

COPY Archipelago-0.6.8/_speedups.pyx Archipelago-0.6.8/_speedups.pyx
COPY Archipelago-0.6.8/intset.h Archipelago-0.6.8/intset.h
RUN cythonize -b -i Archipelago-0.6.8/_speedups.pyx


FROM python:3.13-slim AS final
COPY --from=ghcr.io/astral-sh/uv:0.12.22 /uv /uvx /bin/

WORKDIR /app

COPY requirements.txt requirements.txt
COPY Archipelago-0.6.8/requirements.txt ./Archipelago-0.6.8/requirements.txt
RUN uv pip install --system --no-cache -r requirements.txt

COPY . .
COPY --from=build /app/Archipelago-0.6.8/_speedups.cpython-*.so /app/Archipelago-0.6.8/

# Create missing folders that archipelago expects
RUN mkdir -p /app/Archipelago-0.6.8/Players
RUN mkdir -p /app/Archipelago-0.6.8/data/options
RUN mkdir -p /app/Archipelago-0.6.8/data/sprites
RUN mkdir -p /app/Archipelago-0.6.8/data/lua

EXPOSE 5001

CMD ["gunicorn", "app:app"]