#!/bin/bash
# =============================================================================
# Wizelit MCP Servers - Deployment Script
# Builds Docker images for all MCP servers and deploys to AWS ECS
#
# Usage:
#   ./deploy_mcp.sh              - Full deploy with cache (fast)
#   ./deploy_mcp.sh deploy-nocache - Full deploy without cache (fresh build)
#   ./deploy_mcp.sh code-scout   - Deploy only Code Scout
#   ./deploy_mcp.sh refactoring  - Deploy only Refactoring Agent
#   ./deploy_mcp.sh schema       - Deploy only Schema Validator
#   ./deploy_mcp.sh status       - Check all ECS service status
#   ./deploy_mcp.sh logs         - View recent CloudWatch logs
#   ./deploy_mcp.sh stop         - Scale down all services to 0
#   ./deploy_mcp.sh start        - Scale up all services to 1
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="${AWS_REGION:-ap-southeast-2}"
ECR_REPOSITORY="wizelit-mcp"
ECS_CLUSTER="wizelit-mcp-cluster"
DOCKER_NO_CACHE=""

# MCP Server definitions (compatible with bash 3.x)
SERVER_NAMES="code-scout refactoring-agent schema-validator"

# Map server name to ECS service pattern
get_service_pattern() {
    case "$1" in
        code-scout) echo "codescout" ;;
        refactoring-agent) echo "refactoringagent" ;;
        schema-validator) echo "schemavalidator" ;;
        *) echo "" ;;
    esac
}

# Get account ID
get_account_id() {
    aws sts get-caller-identity --query Account --output text 2>/dev/null
}

# Get service ARN by name pattern
get_service_arn() {
    local pattern=$1
    aws ecs list-services --cluster $ECS_CLUSTER --region $AWS_REGION --query 'serviceArns[]' --output text 2>/dev/null | tr '\t' '\n' | grep -i "$pattern" | head -1
}

# Handle subcommands
case "${1:-deploy}" in
    status)
        echo -e "${BLUE}Checking ECS service status...${NC}"
        for server in $SERVER_NAMES; do
            pattern=$(get_service_pattern "$server")
            service_arn=$(get_service_arn "$pattern")
            if [ -n "$service_arn" ]; then
                echo -e "\n${YELLOW}$server:${NC}"
                aws ecs describe-services --cluster $ECS_CLUSTER --services "$service_arn" --region $AWS_REGION \
                    --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}' \
                    --output table --no-cli-pager
            fi
        done
        exit 0
        ;;
    logs)
        echo -e "${BLUE}Fetching recent logs...${NC}"
        aws logs tail /ecs/wizelit-mcp --since 10m --region $AWS_REGION --format short
        exit 0
        ;;
    stop)
        echo -e "${YELLOW}Scaling down all MCP services to 0...${NC}"
        for server in $SERVER_NAMES; do
            pattern=$(get_service_pattern "$server")
            service_arn=$(get_service_arn "$pattern")
            if [ -n "$service_arn" ]; then
                echo "  Stopping $server..."
                aws ecs update-service --cluster $ECS_CLUSTER --service "$service_arn" --desired-count 0 --region $AWS_REGION --no-cli-pager > /dev/null
            fi
        done
        echo -e "${GREEN}All services scaled down${NC}"
        exit 0
        ;;
    start)
        echo -e "${YELLOW}Scaling up all MCP services to 1...${NC}"
        for server in $SERVER_NAMES; do
            pattern=$(get_service_pattern "$server")
            service_arn=$(get_service_arn "$pattern")
            if [ -n "$service_arn" ]; then
                echo "  Starting $server..."
                aws ecs update-service --cluster $ECS_CLUSTER --service "$service_arn" --desired-count 1 --region $AWS_REGION --no-cli-pager > /dev/null
            fi
        done
        echo -e "${GREEN}All services scaling up. Wait ~2-3 minutes.${NC}"
        exit 0
        ;;
    code-scout)
        DEPLOY_SERVERS="code-scout"
        ;;
    refactoring)
        DEPLOY_SERVERS="refactoring-agent"
        ;;
    schema)
        DEPLOY_SERVERS="schema-validator"
        ;;
    deploy-nocache)
        DEPLOY_SERVERS="$SERVER_NAMES"
        DOCKER_NO_CACHE="--no-cache"
        ;;
    deploy|"")
        DEPLOY_SERVERS="$SERVER_NAMES"
        ;;
    *)
        echo "Usage: ./deploy_mcp.sh [command]"
        echo ""
        echo "Commands:"
        echo "  deploy         - Full deploy all servers (with cache, fast)"
        echo "  deploy-nocache - Full deploy without cache (fresh build, slow)"
        echo "  code-scout     - Deploy only Code Scout"
        echo "  refactoring    - Deploy only Refactoring Agent"
        echo "  schema         - Deploy only Schema Validator"
        echo "  status         - Check ECS service status"
        echo "  logs           - View recent CloudWatch logs"
        echo "  stop           - Scale down all to 0 (save costs)"
        echo "  start          - Scale up all to 1"
        exit 1
        ;;
esac

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Wizelit MCP Servers Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check AWS credentials
echo -e "${YELLOW}[1/5] Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}Error: AWS credentials not configured. Run 'aws configure' first.${NC}"
    exit 1
fi

ACCOUNT_ID=$(get_account_id)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"

echo -e "${GREEN}AWS Account: $ACCOUNT_ID${NC}"
echo -e "${GREEN}Region: $AWS_REGION${NC}"
echo ""

# Login to ECR
echo -e "${YELLOW}[2/5] Logging in to Amazon ECR...${NC}"
ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"
echo -e "${GREEN}ECR login successful${NC}"
echo ""

# Build Docker image
echo -e "${YELLOW}[3/5] Building Docker image (linux/amd64)...${NC}"
if [ -n "$DOCKER_NO_CACHE" ]; then
    echo -e "${BLUE}   Building base image (--no-cache, fresh build)...${NC}"
else
    echo -e "${BLUE}   Building base image (with cache, fast build)...${NC}"
fi

docker build --platform linux/amd64 $DOCKER_NO_CACHE -t $ECR_REPOSITORY:base .
echo -e "${GREEN}Base image built${NC}"
echo ""

# Tag and push for each server
echo -e "${YELLOW}[4/5] Tagging and pushing images...${NC}"
for server in $DEPLOY_SERVERS; do
    echo -e "${BLUE}   Processing $server...${NC}"
    
    # Tag with server name
    docker tag $ECR_REPOSITORY:base $ECR_URI:$server-latest
    COMMIT_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "manual")
    docker tag $ECR_REPOSITORY:base $ECR_URI:$server-$COMMIT_HASH
    
    # Push
    docker push $ECR_URI:$server-latest
    echo -e "${GREEN}   $server pushed${NC}"
done
echo ""

# Deploy to ECS
echo -e "${YELLOW}[5/5] Deploying to ECS...${NC}"
for server in $DEPLOY_SERVERS; do
    pattern=$(get_service_pattern "$server")
    service_arn=$(get_service_arn "$pattern")
    if [ -n "$service_arn" ]; then
        echo -e "${BLUE}   Deploying $server...${NC}"
        aws ecs update-service \
            --cluster $ECS_CLUSTER \
            --service "$service_arn" \
            --force-new-deployment \
            --region $AWS_REGION \
            --no-cli-pager > /dev/null
        echo -e "${GREEN}   $server deployment triggered${NC}"
    else
        echo -e "${YELLOW}   $server service not found (run cdk deploy first)${NC}"
    fi
done
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}  Deployment initiated successfully!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "The deployment is now in progress. You can:"
echo -e "  Check status: ${YELLOW}./deploy_mcp.sh status${NC}"
echo -e "  View logs:    ${YELLOW}./deploy_mcp.sh logs${NC}"
echo -e "  Stop all:     ${YELLOW}./deploy_mcp.sh stop${NC}"
echo ""

# Get ALB URL
ALB_URL=$(aws elbv2 describe-load-balancers \
    --query "LoadBalancers[?contains(LoadBalancerName, 'Mcp')].DNSName" \
    --output text \
    --region $AWS_REGION 2>/dev/null || echo "")

if [ -n "$ALB_URL" ]; then
    echo -e "MCP Server URLs:"
    echo -e "  Code Scout:        ${GREEN}http://$ALB_URL/code-scout/sse${NC}"
    echo -e "  Refactoring Agent: ${GREEN}http://$ALB_URL/refactoring/sse${NC}"
    echo -e "  Schema Validator:  ${GREEN}http://$ALB_URL/schema-validator/mcp${NC}"
fi
