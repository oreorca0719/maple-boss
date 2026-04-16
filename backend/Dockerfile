# ──────────────────────────────────────────────
# Stage 1: builder (의존성 설치)
# ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# 시스템 빌드 도구 (bcrypt, cryptography 컴파일 필요)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt

# ──────────────────────────────────────────────
# Stage 2: runtime
# ──────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# builder에서 설치된 패키지 복사
COPY --from=builder /install /usr/local

# 앱 소스 복사
COPY app/ ./app/

# 환경변수 기본값 (ECS에서 Task Definition의 환경변수가 오버라이드)
ENV APP_ENV=production \
    AWS_REGION=ap-northeast-2 \
    DYNAMODB_TABLE_NAME=maple-boss-scheduler \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# Gunicorn + Uvicorn worker: ECS Fargate CPU 기준 worker 수 조정
# --workers는 ECS Task CPU에 맞게 조정 (0.5 vCPU → 1, 1 vCPU → 2)
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "2", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
