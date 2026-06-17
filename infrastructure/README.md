# Infrastructure — Prompt Engineering Workshop

Deploy the workshop on AWS using CloudFormation templates.

## Architecture

```
Users → CloudFront → ALB (HTTPS:8084) → EC2 Auto Scaling Group
                                              │
                                         Streamlit App
                                              │
                                      Amazon Bedrock (Converse API)
                                              │
                                      Bedrock Guardrails
```

## Prerequisites

- AWS CLI configured with appropriate credentials
- An ACM certificate for your domain (in `us-east-1` for CloudFront)
- A Route53 hosted zone for your domain
- Sufficient Bedrock model access (Nova, Claude, Llama, etc.)

## CloudFormation Templates

| Order | Template | Resources |
|-------|----------|-----------|
| 1 | `01_vpc.yaml` | VPC, 3 public/private subnets, NAT Gateway, routes |
| 2 | `02_bedrock_guardrail.yaml` | Bedrock Guardrail with all policy types |
| 3 | `03_streamlit.yaml` | EC2 ASG, ALB, IAM role, security groups |
| 4 | `04_cloudfront.yaml` | CloudFront distribution, origin secret, DNS records, WAF (optional) |

## Quick Deploy

```bash
# Set your configuration
export DOMAIN="yourdomain.com"
export SUBDOMAIN="workshop"
export CERT_ID="your-acm-certificate-id"
export WAF_WEB_ACL_ARN="arn:aws:wafv2:us-east-1:ACCOUNT:global/webacl/NAME/ID"  # optional

# Deploy all stacks
./infrastructure/scripts/deploy.sh
```

## Quick Cleanup

```bash
# Delete all stacks (prompts for confirmation)
./infrastructure/scripts/cleanup.sh
```

## Configuration

The deploy script uses environment variables for configuration. Override any default:

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_REGION` | `us-east-1` | AWS region to deploy in |
| `STACK_PREFIX` | `prompt-workshop` | Prefix for all stack names |
| `VPC_CIDR` | `10.0.0.0/16` | CIDR block for the VPC |
| `DOMAIN` | `example.com` | Root domain name |
| `SUBDOMAIN` | `workshop` | Subdomain (workshop.example.com) |
| `CERT_ID` | — | ACM certificate ID for the ALB |
| `CF_CERT_ARN` | — | Full ACM ARN for CloudFront (us-east-1) |
| `CF_PREFIX_LIST` | `pl-3b927c52` | CloudFront managed prefix list (us-east-1) |
| `APP_PORT` | `8084` | Streamlit application port |
| `WAF_WEB_ACL_ARN` | — | WAF Web ACL ARN to attach to CloudFront (optional) |
| `GIT_REPO` | GitHub URL | Repository to clone on EC2 |
| `GIT_BRANCH` | `main` | Branch to deploy |

## Manual Deployment (step by step)

If you prefer to deploy templates individually:

```bash
# 1. VPC
aws cloudformation deploy \
  --stack-name prompt-workshop-vpc \
  --template-file infrastructure/cloudformation/01_vpc.yaml \
  --parameter-overrides VpcCidrBlock=10.0.0.0/16 \
  --region us-east-1

# 2. Bedrock Guardrail
aws cloudformation deploy \
  --stack-name prompt-workshop-guardrail \
  --template-file infrastructure/cloudformation/02_bedrock_guardrail.yaml \
  --region us-east-1

# 3. Streamlit (imports VPC exports)
aws cloudformation deploy \
  --stack-name prompt-workshop-streamlit \
  --template-file infrastructure/cloudformation/03_streamlit.yaml \
  --parameter-overrides \
    Domain=yourdomain.com \
    CertId=your-cert-id \
    SourcePrefixListId=pl-3b927c52 \
    VpcStackName=prompt-workshop-vpc \
  --capabilities CAPABILITY_IAM \
  --region us-east-1

# 4. CloudFront (imports ALB DNS from Streamlit stack)
aws cloudformation deploy \
  --stack-name prompt-workshop-cloudfront \
  --template-file infrastructure/cloudformation/04_cloudfront.yaml \
  --parameter-overrides \
    Domain=yourdomain.com \
    Subdomain=workshop \
    CertificateArn=arn:aws:acm:us-east-1:ACCOUNT:certificate/CERT-ID \
    StreamlitStackName=prompt-workshop-streamlit \
    WebACLArn=arn:aws:wafv2:us-east-1:ACCOUNT:global/webacl/NAME/ID \
  --region us-east-1
```

## CloudFront Prefix Lists by Region

If deploying outside `us-east-1`, use the correct CloudFront managed prefix list:

| Region | Prefix List ID |
|--------|---------------|
| us-east-1 | `pl-3b927c52` |
| us-west-2 | `pl-82a045eb` |
| eu-west-1 | `pl-4fa04526` |
| ap-southeast-1 | `pl-31a34658` |
| ap-northeast-1 | `pl-58a04531` |

## Post-Deployment

After deployment completes:

1. **Wait 3-5 minutes** for the EC2 instance to initialize (clone repo, install Python 3.12, install dependencies, start Streamlit)
2. **Access the workshop** at `https://SUBDOMAIN.DOMAIN`
3. **Get the Guardrail ID** from the stack outputs to use in Page 05 (Prompt Injection Red Team)

```bash
# Get Guardrail ID
aws cloudformation describe-stacks \
  --stack-name prompt-workshop-guardrail \
  --query "Stacks[0].Outputs[?OutputKey=='GuardrailId'].OutputValue" \
  --output text
```

## Troubleshooting

| Issue | Check |
|-------|-------|
| App not loading | Wait 5 min for EC2 init. Check instance logs via SSM Session Manager. |
| 502 Bad Gateway | ALB target group health check failing. Verify Streamlit is running on port 8084. |
| CloudFront 403 | Origin secret header mismatch. Verify both stacks use the same `cloudfront/alb-handshake` secret. |
| Bedrock errors | Verify the EC2 IAM role has Bedrock permissions and models are enabled in the region. |
| Guardrail not working | Ensure the Guardrail ID is entered in Page 05 sidebar. Check version (DRAFT vs published). |
