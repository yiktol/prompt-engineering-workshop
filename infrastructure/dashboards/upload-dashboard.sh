#!/bin/bash

# Upload CloudWatch Dashboard via CLI
# This bypasses the console's log group discovery that requires StartQuery permissions

DASHBOARD_NAME="coffeeshop-metrics"
REGION="ap-southeast-1"

echo "Uploading CloudWatch Dashboard: ${DASHBOARD_NAME}"
echo "Region: ${REGION}"
echo ""

aws cloudwatch put-dashboard \
  --dashboard-name "${DASHBOARD_NAME}" \
  --dashboard-body file://cloudwatch-dashboard.json \
  --region "${REGION}"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Dashboard uploaded successfully!"
    echo ""
    echo "View your dashboard at:"
    echo "https://${REGION}.console.aws.amazon.com/cloudwatch/home?region=${REGION}#dashboards:name=${DASHBOARD_NAME}"
else
    echo ""
    echo "❌ Failed to upload dashboard"
    exit 1
fi
