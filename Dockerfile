# ─── Stage 1: Next.js 빌드 ──────────────────────────────────────
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
# NEXT_PUBLIC_API_URL="" 강제 지정 → .env.local 값 무시 → BASE="" → nginx 상대경로 라우팅
RUN NEXT_PUBLIC_API_URL="" npm run build

# ─── Stage 2: Python 의존성 설치 ────────────────────────────────
FROM python:3.12-slim AS python-builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libffi-dev \
    && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# ─── Stage 3: 통합 런타임 ───────────────────────────────────────
FROM python:3.12-slim AS runtime
WORKDIR /app

# Node.js 20 + nginx + supervisor
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg nginx supervisor \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Python 패키지 복사
COPY --from=python-builder /install /usr/local

# FastAPI 앱
COPY backend/app/ ./app/

# Next.js standalone 결과물
COPY --from=frontend-builder /app/.next/standalone ./frontend/
COPY --from=frontend-builder /app/.next/static     ./frontend/.next/static
COPY --from=frontend-builder /app/public           ./frontend/public

# nginx, supervisor 설정
COPY nginx.conf        /etc/nginx/nginx.conf
COPY supervisord.conf  /etc/supervisor/conf.d/app.conf

ENV APP_ENV=production \
    AWS_REGION=ap-northeast-1 \
    DYNAMODB_TABLE_NAME=maple-boss-scheduler \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NODE_ENV=production

# App Runner 헬스체크 + nginx 진입점
EXPOSE 8080

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/app.conf"]
