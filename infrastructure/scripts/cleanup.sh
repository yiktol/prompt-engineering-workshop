#!/bin/bash
set -e

# ============================================================================
# Prompt Engineering Workshop - Cleanup Script
# Deletes all CloudFormation stacks in reverse dependency order.
# ============================================================================

AWS_REGION="${AWS_REGION:-us-east-1}"
STACK_PREFIX="${STACK_PREFIX:-prompt-workshop}"

echo "============================================"
echo "  Prompt Engineering Workshop - Cleanup"
echo "============================================"
echo ""
echo "Region:       ${AWS_REGION}"
echo "Stack prefix: ${STACK_PREFIX}"
echo ""
echo "This will DELETE the following stacks:"
echo "  1. ${STACK_PREFIX}-cloudfront"
echo "  2. ${STACK_PREFIX}-streamlit"
echo "  3. ${STACK_PREFIX}-guardrail"
echo "  4. ${STACK_PREFIX}-vpc"
echo ""

# Confirmation
read -p "Are you sure? (yes/no): " CONFIRM
if [[ "${CONFIRM}" != "yes" ]]; then
    echo "Aborted."
    exit 0
fi

echo ""

# ----------------------------------------
# Helper function
# ----------------------------------------
delete_stack() {
    local stack_name=$1

    # Check if stack exists
    if ! aws cloudformation describe-stacks --stack-name "${stack_name}" --region "${AWS_REGION}" &>/dev/null; then
        echo "  ⏭️  ${stack_name} does not exist, skipping"
        return 0
    fi

    echo "▶ Deleting: ${stack_name}"
    aws cloudformation delete-stack \
        --stack-name "${stack_name}" \
        --region "${AWS_REGION}"

    echo "  ⏳ Waiting for deletion..."
    aws cloudformation wait stack-delete-complete \
        --stack-name "${stack_name}" \
        --region "${AWS_REGION}"

    echo "  ✅ ${stack_name} deleted"
    echo ""
}

# ----------------------------------------
# Delete in reverse dependency order
# ----------------------------------------

# Step 1: CloudFront (depends on Streamlit)
delete_stack "${STACK_PREFIX}-cloudfront"

# Step 2: Streamlit (depends on VPC)
delete_stack "${STACK_PREFIX}-streamlit"

# Step 3: Guardrail (standalone)
delete_stack "${STACK_PREFIX}-guardrail"

# Step 4: VPC (foundation)
delete_stack "${STACK_PREFIX}-vpc"

# ----------------------------------------
# Cleanup Secrets Manager (optional)
# ----------------------------------------
echo "▶ Cleaning up Secrets Manager..."
SECRET_ARN=$(aws secretsmanager describe-secret \
    --secret-id "cloudfront/alb-handshake" \
    --region "${AWS_REGION}" \
    --query "ARN" --output text 2>/dev/null || echo "")

if [[ -n "${SECRET_ARN}" && "${SECRET_ARN}" != "None" ]]; then
    aws secretsmanager delete-secret \
        --secret-id "cloudfront/alb-handshake" \
        --force-delete-without-recovery \
        --region "${AWS_REGION}" 2>/dev/null || true
    echo "  ✅ Secret deleted"
else
    echo "  ⏭️  No secret found, skipping"
fi

echo ""
echo "============================================"
echo "  ✅ Cleanup Complete!"
echo "============================================"
echo ""
echo "All workshop resources have been removed."
