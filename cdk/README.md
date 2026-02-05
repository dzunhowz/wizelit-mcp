# Wizelit MCP Servers - AWS CDK Deployment

This CDK stack deploys the Wizelit MCP servers to AWS ECS Fargate.

## Deployed Servers

| Server | Port | Transport | Path |
|--------|------|-----------|------|
| Code Scout | 1338 | SSE | `/code-scout/*` |
| Refactoring Agent | 1337 | SSE | `/refactoring/*` |
| Schema Validator | 1340 | Streamable-HTTP | `/schema-validator/*` |

> **Note:** Code Formatter uses Stdio transport and cannot be deployed to AWS.

## AWS Resources Created

- **VPC** - Public subnets only (no NAT for cost savings)
- **ECS Cluster** - `wizelit-mcp-cluster`
- **ECS Services** - 3 Fargate services (one per MCP server)
- **Application Load Balancer** - Path-based routing to each server
- **ECR Repository** - `wizelit-mcp` (shared repo with server-specific tags)
- **ElastiCache Redis** - For log streaming (t3.micro, free tier)
- **Secrets Manager** - For GITHUB_TOKEN and other secrets
- **CloudWatch Logs** - `/ecs/wizelit-mcp`
- **IAM Roles** - Task role with Bedrock permissions, GitHub Actions role

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **AWS CDK CLI** installed: `npm install -g aws-cdk`
3. **Python 3.12+** with pip
4. **Docker** for building images

## Quick Start

### 1. Install CDK Dependencies

```bash
cd cdk
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Bootstrap CDK (first time only)

```bash
# Get your AWS account ID
aws sts get-caller-identity --query Account --output text

# Bootstrap CDK
cdk bootstrap aws://YOUR_ACCOUNT_ID/ap-southeast-2
```

### 3. Deploy Infrastructure

```bash
# Set region (optional, defaults to ap-southeast-2)
export AWS_DEFAULT_REGION=ap-southeast-2
export CDK_DEFAULT_REGION=ap-southeast-2

# Deploy
cdk deploy --require-approval never
```

### 4. Configure Secrets

After deployment, add your GitHub token to Secrets Manager:

```bash
aws secretsmanager put-secret-value \
    --secret-id wizelit-mcp/app-secrets \
    --secret-string '{"GITHUB_TOKEN": "ghp_your_token_here"}' \
    --region ap-southeast-2
```

### 5. Build and Deploy MCP Servers

```bash
cd ..  # Back to wizelit-mcp root
chmod +x deploy_mcp.sh
./deploy_mcp.sh deploy
```

## Deploy Commands

```bash
# Full deploy (all servers)
./deploy_mcp.sh deploy

# Deploy single server
./deploy_mcp.sh code-scout
./deploy_mcp.sh refactoring
./deploy_mcp.sh schema

# Check status
./deploy_mcp.sh status

# View logs
./deploy_mcp.sh logs

# Stop all (save costs)
./deploy_mcp.sh stop

# Start all
./deploy_mcp.sh start
```

## CDK Commands

```bash
# Synthesize CloudFormation template
cdk synth

# View changes before deploy
cdk diff

# Deploy changes
cdk deploy

# Destroy all resources
cdk destroy
```

## Server URLs

After deployment, the MCP servers will be available at:

```
http://<ALB_DNS>/code-scout/sse          # Code Scout
http://<ALB_DNS>/refactoring/sse         # Refactoring Agent
http://<ALB_DNS>/schema-validator/mcp    # Schema Validator
```

Get the ALB DNS from:
- CDK output after deployment
- AWS Console → EC2 → Load Balancers

## Connecting from Wizelit Hub

Add these URLs to your Wizelit Hub configuration to connect to the deployed MCP servers:

```python
# In Wizelit Hub, add servers via UI or config:
MCP_SERVERS = {
    "code-scout": {
        "url": "http://<ALB_DNS>/code-scout/sse",
        "transport": "sse"
    },
    "refactoring-agent": {
        "url": "http://<ALB_DNS>/refactoring/sse",
        "transport": "sse"
    },
    "schema-validator": {
        "url": "http://<ALB_DNS>/schema-validator/mcp",
        "transport": "streamable-http"
    }
}
```

## GitHub Actions CI/CD

To enable automatic deployment on push to main:

1. Get the GitHub Actions Role ARN from CDK output
2. Add to GitHub repository secrets:
   - `AWS_ROLE_ARN`: The role ARN from CDK output

## Cost Optimization

- **ECS Fargate**: ~$0.04/hour per server (256 CPU, 512 MB)
- **Redis**: Free tier (t3.micro)
- **ALB**: ~$0.02/hour + data transfer
- **NAT Gateway**: Not used (public subnets only)

**To minimize costs:**
```bash
# Stop all services when not in use
./deploy_mcp.sh stop

# Start when needed
./deploy_mcp.sh start
```

## Architecture

```
                    ┌─────────────────────────────────────────────────┐
                    │                      VPC                         │
                    │  ┌───────────────────────────────────────────┐  │
Internet ──────────►│  │              Application Load Balancer     │  │
                    │  │  /code-scout/*  /refactoring/*  /schema/*  │  │
                    │  └───────────────────────────────────────────┘  │
                    │           │              │              │        │
                    │  ┌────────▼──────┐ ┌─────▼─────┐ ┌─────▼─────┐  │
                    │  │  Code Scout   │ │Refactoring│ │  Schema   │  │
                    │  │  ECS Fargate  │ │  Agent    │ │ Validator │  │
                    │  │  Port 1338    │ │ Port 1337 │ │ Port 1340 │  │
                    │  └───────────────┘ └───────────┘ └───────────┘  │
                    │                         │                        │
                    │                  ┌──────▼──────┐                 │
                    │                  │   Redis     │                 │
                    │                  │ (Streaming) │                 │
                    │                  └─────────────┘                 │
                    └─────────────────────────────────────────────────┘
```

## Troubleshooting

### No targets in ALB
Services start with `desired_count=0`. Run:
```bash
./deploy_mcp.sh start
```

### Health checks failing
Check CloudWatch logs:
```bash
./deploy_mcp.sh logs
```

### Permission errors
Ensure the task role has Bedrock permissions (included in CDK stack).

### GitHub Actions fails
1. Verify `AWS_ROLE_ARN` secret is set correctly
2. Check the OIDC provider is configured in AWS
