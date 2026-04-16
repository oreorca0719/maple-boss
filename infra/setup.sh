#!/usr/bin/env bash
# ============================================================
# MapleBoss AWS 인프라 셋업 스크립트
# 실행 전 AWS CLI 로그인 확인: aws sts get-caller-identity
#
# 사용법: bash infra/setup.sh
# ============================================================
set -euo pipefail

# ── 설정 변수 ────────────────────────────────────────────────
APP_NAME="maple-boss"
REGION="ap-northeast-1"
TABLE_NAME="maple-boss-scheduler"

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account: $AWS_ACCOUNT_ID  Region: $REGION"

# ── 1. DynamoDB 테이블 생성 ───────────────────────────────────
echo ""
echo "▶ [1/4] DynamoDB 테이블 생성 중..."
if aws dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" &>/dev/null; then
  echo "  이미 존재: $TABLE_NAME"
else
  aws dynamodb create-table \
    --table-name "$TABLE_NAME" \
    --key-schema \
      AttributeName=pk,KeyType=HASH \
      AttributeName=sk,KeyType=RANGE \
    --attribute-definitions \
      AttributeName=pk,AttributeType=S \
      AttributeName=sk,AttributeType=S \
      AttributeName=gsi1pk,AttributeType=S \
      AttributeName=gsi1sk,AttributeType=S \
    --global-secondary-indexes \
      '[{"IndexName":"GSI1","KeySchema":[{"AttributeName":"gsi1pk","KeyType":"HASH"},{"AttributeName":"gsi1sk","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"}}]' \
    --billing-mode PAY_PER_REQUEST \
    --region "$REGION"
  echo "  생성 완료: $TABLE_NAME"
fi

# ── 2. ECR 리포지토리 생성 ────────────────────────────────────
echo ""
echo "▶ [2/4] ECR 리포지토리 생성 중..."
for REPO in "${APP_NAME}-backend" "${APP_NAME}-frontend"; do
  if aws ecr describe-repositories --repository-names "$REPO" --region "$REGION" &>/dev/null; then
    echo "  이미 존재: $REPO"
  else
    aws ecr create-repository \
      --repository-name "$REPO" \
      --region "$REGION" \
      --image-scanning-configuration scanOnPush=true \
      --output table
    echo "  생성 완료: $REPO"
  fi
done

# ── 3. IAM 역할 생성 (App Runner → DynamoDB) ─────────────────
echo ""
echo "▶ [3/4] IAM Task Role 생성 중..."
ROLE_NAME="${APP_NAME}-apprunner-role"

if aws iam get-role --role-name "$ROLE_NAME" &>/dev/null; then
  echo "  이미 존재: $ROLE_NAME"
else
  aws iam create-role \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document '{
      "Version":"2012-10-17",
      "Statement":[{
        "Effect":"Allow",
        "Principal":{"Service":"tasks.apprunner.amazonaws.com"},
        "Action":"sts:AssumeRole"
      }]
    }'

  # DynamoDB 풀 엑세스 (해당 테이블만 한정 가능 — 여기서는 편의상 전체)
  aws iam put-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-name "DynamoDBAccess" \
    --policy-document "{
      \"Version\":\"2012-10-17\",
      \"Statement\":[{
        \"Effect\":\"Allow\",
        \"Action\":[
          \"dynamodb:GetItem\",\"dynamodb:PutItem\",\"dynamodb:UpdateItem\",
          \"dynamodb:DeleteItem\",\"dynamodb:Query\",\"dynamodb:Scan\"
        ],
        \"Resource\":[
          \"arn:aws:dynamodb:${REGION}:${AWS_ACCOUNT_ID}:table/${TABLE_NAME}\",
          \"arn:aws:dynamodb:${REGION}:${AWS_ACCOUNT_ID}:table/${TABLE_NAME}/index/*\"
        ]
      }]
    }"
  echo "  생성 완료: $ROLE_NAME"
fi

ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query Role.Arn --output text)

# ── 4. App Runner 접근 역할 생성 (ECR 접근용) ─────────────────
echo ""
echo "▶ [4/4] App Runner ECR 접근 역할 설정..."
ACCESS_ROLE_NAME="${APP_NAME}-apprunner-access-role"

if aws iam get-role --role-name "$ACCESS_ROLE_NAME" &>/dev/null; then
  echo "  이미 존재: $ACCESS_ROLE_NAME"
else
  aws iam create-role \
    --role-name "$ACCESS_ROLE_NAME" \
    --assume-role-policy-document '{
      "Version":"2012-10-17",
      "Statement":[{
        "Effect":"Allow",
        "Principal":{"Service":"build.apprunner.amazonaws.com"},
        "Action":"sts:AssumeRole"
      }]
    }'
  aws iam attach-role-policy \
    --role-name "$ACCESS_ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
  echo "  생성 완료: $ACCESS_ROLE_NAME"
fi

ACCESS_ROLE_ARN=$(aws iam get-role --role-name "$ACCESS_ROLE_NAME" --query Role.Arn --output text)

echo ""
echo "============================================================"
echo "셋업 완료! 다음 값을 deploy.sh에서 사용합니다:"
echo "  ROLE_ARN        = $ROLE_ARN"
echo "  ACCESS_ROLE_ARN = $ACCESS_ROLE_ARN"
echo "  ACCOUNT_ID      = $AWS_ACCOUNT_ID"
echo "============================================================"
echo "다음 단계: bash infra/deploy.sh"
