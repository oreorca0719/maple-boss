#!/usr/bin/env bash
# ============================================================
# MapleBoss 배포 스크립트
# - Docker 이미지 빌드 → ECR Push → App Runner 서비스 생성/갱신
#
# 사전 준비:
#   1. bash infra/setup.sh  실행 완료
#   2. .env 파일에 NEXON_API_KEY, APP_SECRET_KEY 설정
#   3. aws configure 또는 IAM 권한 확인
#
# 사용법: bash infra/deploy.sh
# ============================================================
set -euo pipefail

APP_NAME="maple-boss"
REGION="ap-northeast-1"
TABLE_NAME="maple-boss-scheduler"

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_HOST="${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${APP_NAME}-apprunner-role"
ACCESS_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${APP_NAME}-apprunner-access-role"

# .env에서 시크릿 로드
if [ -f "backend/.env" ]; then
  set -o allexport; source backend/.env; set +o allexport
else
  echo "❌ backend/.env 파일이 없습니다. .env.example을 복사하여 값을 채워주세요."
  exit 1
fi

echo "Account: $AWS_ACCOUNT_ID | Region: $REGION"

# ECR 로그인
echo ""
echo "▶ ECR 로그인..."
aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "$ECR_HOST"

# ── 백엔드 빌드 & 푸시 ────────────────────────────────────────
echo ""
echo "▶ [1/4] 백엔드 Docker 이미지 빌드..."
BACKEND_REPO="${ECR_HOST}/${APP_NAME}-backend"
docker build -t "${APP_NAME}-backend:latest" ./backend
docker tag "${APP_NAME}-backend:latest" "${BACKEND_REPO}:latest"

echo "▶ [2/4] 백엔드 ECR 푸시..."
docker push "${BACKEND_REPO}:latest"

# ── 프론트엔드 빌드 & 푸시 ───────────────────────────────────
# 백엔드 App Runner URL이 아직 없으면 임시로 placeholder 사용
# 배포 후 프론트엔드 App Runner 서비스의 환경변수로 교체 가능
echo ""
echo "▶ [3/4] 프론트엔드 Docker 이미지 빌드..."
FRONTEND_REPO="${ECR_HOST}/${APP_NAME}-frontend"
BACKEND_APP_RUNNER_URL="${BACKEND_APP_RUNNER_URL:-http://localhost:8000}"
docker build \
  --build-arg NEXT_PUBLIC_API_URL="$BACKEND_APP_RUNNER_URL" \
  -t "${APP_NAME}-frontend:latest" ./frontend
docker tag "${APP_NAME}-frontend:latest" "${FRONTEND_REPO}:latest"

echo "▶ [4/4] 프론트엔드 ECR 푸시..."
docker push "${FRONTEND_REPO}:latest"

# ── App Runner 서비스 생성/갱신 ──────────────────────────────
echo ""
echo "▶ App Runner 백엔드 서비스 배포..."
BACKEND_SVC="${APP_NAME}-backend"

BACKEND_EXISTS=$(aws apprunner list-services --region "$REGION" \
  --query "ServiceSummaryList[?ServiceName=='${BACKEND_SVC}'].ServiceArn" \
  --output text)

BACKEND_ENV_VARS="[
  {\"Name\":\"NEXON_API_KEY\",\"Value\":\"${NEXON_API_KEY:-}\"},
  {\"Name\":\"AWS_REGION\",\"Value\":\"${REGION}\"},
  {\"Name\":\"DYNAMODB_TABLE_NAME\",\"Value\":\"${TABLE_NAME}\"},
  {\"Name\":\"APP_ENV\",\"Value\":\"production\"},
  {\"Name\":\"APP_SECRET_KEY\",\"Value\":\"${APP_SECRET_KEY:-change-me}\"},
  {\"Name\":\"APP_CORS_ORIGINS\",\"Value\":\"*\"}
]"

if [ -z "$BACKEND_EXISTS" ]; then
  echo "  신규 생성: $BACKEND_SVC"
  BACKEND_ARN=$(aws apprunner create-service \
    --region "$REGION" \
    --service-name "$BACKEND_SVC" \
    --source-configuration "{
      \"ImageRepository\":{
        \"ImageIdentifier\":\"${BACKEND_REPO}:latest\",
        \"ImageRepositoryType\":\"ECR\",
        \"ImageConfiguration\":{
          \"Port\":\"8000\",
          \"RuntimeEnvironmentVariables\":${BACKEND_ENV_VARS}
        }
      },
      \"AuthenticationConfiguration\":{
        \"AccessRoleArn\":\"${ACCESS_ROLE_ARN}\"
      },
      \"AutoDeploymentsEnabled\":false
    }" \
    --instance-configuration "{
      \"Cpu\":\"0.5 vCPU\",
      \"Memory\":\"1 GB\",
      \"InstanceRoleArn\":\"${ROLE_ARN}\"
    }" \
    --query ServiceArn --output text)
  echo "  ARN: $BACKEND_ARN"
else
  echo "  기존 서비스 업데이트: $BACKEND_SVC"
  aws apprunner start-deployment \
    --service-arn "$BACKEND_EXISTS" \
    --region "$REGION" > /dev/null
fi

# 백엔드 URL 조회
BACKEND_URL=$(aws apprunner describe-service \
  --service-arn "${BACKEND_EXISTS:-$BACKEND_ARN}" \
  --region "$REGION" \
  --query ServiceUrl --output text 2>/dev/null || echo "")

echo ""
echo "▶ App Runner 프론트엔드 서비스 배포..."
FRONTEND_SVC="${APP_NAME}-frontend"

FRONTEND_EXISTS=$(aws apprunner list-services --region "$REGION" \
  --query "ServiceSummaryList[?ServiceName=='${FRONTEND_SVC}'].ServiceArn" \
  --output text)

FRONTEND_ENV_VARS="[
  {\"Name\":\"NEXT_PUBLIC_API_URL\",\"Value\":\"https://${BACKEND_URL}\"}
]"

if [ -z "$FRONTEND_EXISTS" ]; then
  echo "  신규 생성: $FRONTEND_SVC"
  aws apprunner create-service \
    --region "$REGION" \
    --service-name "$FRONTEND_SVC" \
    --source-configuration "{
      \"ImageRepository\":{
        \"ImageIdentifier\":\"${FRONTEND_REPO}:latest\",
        \"ImageRepositoryType\":\"ECR\",
        \"ImageConfiguration\":{
          \"Port\":\"3000\",
          \"RuntimeEnvironmentVariables\":${FRONTEND_ENV_VARS}
        }
      },
      \"AuthenticationConfiguration\":{
        \"AccessRoleArn\":\"${ACCESS_ROLE_ARN}\"
      },
      \"AutoDeploymentsEnabled\":false
    }" \
    --instance-configuration "{\"Cpu\":\"0.5 vCPU\",\"Memory\":\"1 GB\"}" \
    --query ServiceUrl --output text
else
  echo "  기존 서비스 업데이트: $FRONTEND_SVC"
  aws apprunner start-deployment \
    --service-arn "$FRONTEND_EXISTS" \
    --region "$REGION" > /dev/null
fi

echo ""
echo "============================================================"
echo "배포 완료!"
echo "  백엔드 URL: https://${BACKEND_URL:-<App Runner 콘솔에서 확인>}"
echo ""
echo "⚠ 프론트엔드가 백엔드 URL을 참조하므로,"
echo "  백엔드 배포 완료 후 BACKEND_APP_RUNNER_URL=https://<url>"
echo "  변수를 설정하고 deploy.sh를 한 번 더 실행하세요."
echo ""
echo "다음 단계: 시드 스크립트 실행"
echo "  cd backend && python scripts/seed.py"
echo "============================================================"
