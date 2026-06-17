#!/bin/bash
set -e

# ============================================================================
# Prompt Engineering Workshop - Deploy Script
# Deploys all CloudFormation stacks in dependency order.
# ============================================================================

# Configuration (override with environment variables)
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo 'UNKNOWN')}"
AWS_REGION="${AWS_REGION:-us-east-1}"
STACK_PREFIX="${STACK_PREFIX:-prompt-workshop}"
VPC_CIDR="${VPC_CIDR:-10.0.0.0/16}"
DOMAIN="${DOMAIN:-example.com}"
SUBDOMAIN="${SUBDOMAIN:-workshop}"
CERT_ID="${CERT_ID:-your-certificate-id}"
CF_CERT_ARN="${CF_CERT_ARN:-arn:aws:acm:us-east-1:${AWS_ACCOUNT_ID}:certificate/${CERT_ID}}"
CF_PREFIX_LIST="${CF_PREFIX_LIST:-pl-3b927c52}"
APP_PORT="${APP_PORT:-8084}"
GIT_REPO="${GIT_REPO:-https://github.com/yiktol/prompt-engineering-workshop.git}"
GIT_BRANCH="${GIT_BRANCH:-main}"
WAF_WEB_ACL_ARN="${WAF_WEB_ACL_ARN:-}"

TEMPLATE_DIR="$(cd "$(dirname "$0")/../cloudformation" && pwd)"

echo "============================================"
echo "  Prompt Engineering Workshop - Deployment"
echo "============================================"
echo ""
echo "Region:       ${AWS_REGION}"
echo "Stack prefix: ${STACK_PREFIX}"
echo "Domain:       ${SUBDOMAIN}.${DOMAIN}"
echo "Template dir: ${TEMPLATE_DIR}"
echo ""

# ----------------------------------------
# Helper function
# ----------------------------------------
deploy_stack() {
    local stack_name=$1
    local template=$2
    shift 2
    local params=("$@")

    echo "▶ Deploying: ${stack_name}"
    echo "  Template: ${template}"

    aws cloudformation deploy \
        --stack-name "${stack_name}" \
        --template-file "${TEMPLATE_DIR}/${template}" \
        --parameter-overrides "${params[@]}" \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
        --region "${AWS_REGION}" \
        --no-fail-on-empty-changeset

    echo "  ✅ ${stack_name} deployed successfully"
    echo ""
}

wait_for_stack() {
    local stack_name=$1
    echo "  ⏳ Waiting for ${stack_name} to complete..."
    aws cloudformation wait stack-create-complete \
        --stack-name "${stack_name}" \
        --region "${AWS_REGION}" 2>/dev/null || \
    aws cloudformation wait stack-update-complete \
        --stack-name "${stack_name}" \
        --region "${AWS_REGION}" 2>/dev/null || true
}

# ----------------------------------------
# Step 1: VPC
# ----------------------------------------
deploy_stack "${STACK_PREFIX}-vpc" "01_vpc.yaml" \
    "VpcCidrBlock=${VPC_CIDR}"

# ----------------------------------------
# Step 2: Bedrock Guardrail (parallel-safe)
# ----------------------------------------
deploy_stack "${STACK_PREFIX}-guardrail" "02_bedrock_guardrail.yaml" \
    "GuardrailName=${STACK_PREFIX}-guardrail" \
    "Environment=workshop"

# ----------------------------------------
# Step 3: Streamlit (EC2/ALB/ASG)
# ----------------------------------------
deploy_stack "${STACK_PREFIX}-streamlit" "03_streamlit.yaml" \
    "Domain=${DOMAIN}" \
    "CertId=${CERT_ID}" \
    "SourcePrefixListId=${CF_PREFIX_LIST}" \
    "VpcStackName=${STACK_PREFIX}-vpc" \
    "AppPort=${APP_PORT}" \
    "CloudFrontALBSecretName=cloudfront/${STACK_PREFIX}-cloudfront-alb-handshake" \
    "GitRepoUrl=${GIT_REPO}" \
    "GitBranch=${GIT_BRANCH}"

# ----------------------------------------
# Step 4: CloudFront
# ----------------------------------------
deploy_stack "${STACK_PREFIX}-cloudfront" "04_cloudfront.yaml" \
    "Domain=${DOMAIN}" \
    "Subdomain=${SUBDOMAIN}" \
    "CertificateArn=${CF_CERT_ARN}" \
    "AppPort=${APP_PORT}" \
    "StreamlitStackName=${STACK_PREFIX}-streamlit" \
    "WebACLArn=${WAF_WEB_ACL_ARN}"

# ----------------------------------------
# Summary
# ----------------------------------------
echo "============================================"
echo "  ✅ Deployment Complete!"
echo "============================================"
echo ""
echo "Stacks deployed:"
echo "  1. ${STACK_PREFIX}-vpc"
echo "  2. ${STACK_PREFIX}-guardrail"
echo "  3. ${STACK_PREFIX}-streamlit"
echo "  4. ${STACK_PREFIX}-cloudfront"
echo ""

# Get outputs
WORKSHOP_URL=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_PREFIX}-cloudfront" \
    --query "Stacks[0].Outputs[?OutputKey=='WorkshopURL'].OutputValue" \
    --output text \
    --region "${AWS_REGION}" 2>/dev/null || echo "pending")

GUARDRAIL_ID=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_PREFIX}-guardrail" \
    --query "Stacks[0].Outputs[?OutputKey=='GuardrailId'].OutputValue" \
    --output text \
    --region "${AWS_REGION}" 2>/dev/null || echo "pending")

echo "Workshop URL:  ${WORKSHOP_URL}"
echo "Guardrail ID:  ${GUARDRAIL_ID}"
echo ""
echo "Note: EC2 instance may take 3-5 minutes to initialize after stack creation."
