"""
AWS CDK Stack for Wizelit MCP Servers
Deploys 3 MCP servers as ECS Fargate services behind an ALB.
"""
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_logs as logs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_elasticache as elasticache,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct


class McpServersStack(Stack):
    """CDK Stack for deploying Wizelit MCP Servers to AWS."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ======================================================================
        # VPC - Simple public-only setup for cost optimization
        # ======================================================================
        vpc = ec2.Vpc(
            self,
            "McpVpc",
            max_azs=2,
            nat_gateways=0,  # Cost optimization - no NAT
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                )
            ],
        )

        # ======================================================================
        # Security Groups
        # ======================================================================
        alb_security_group = ec2.SecurityGroup(
            self,
            "AlbSecurityGroup",
            vpc=vpc,
            description="Security group for MCP ALB",
            allow_all_outbound=True,
        )
        alb_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            "Allow HTTP from anywhere",
        )

        ecs_security_group = ec2.SecurityGroup(
            self,
            "EcsSecurityGroup",
            vpc=vpc,
            description="Security group for MCP ECS services",
            allow_all_outbound=True,
        )
        ecs_security_group.add_ingress_rule(
            alb_security_group,
            ec2.Port.tcp_range(1337, 1340),
            "Allow traffic from ALB on MCP ports",
        )

        # ======================================================================
        # Redis (ElastiCache) - For log streaming
        # ======================================================================
        redis_security_group = ec2.SecurityGroup(
            self,
            "RedisSecurityGroup",
            vpc=vpc,
            description="Security group for Redis",
        )
        redis_security_group.add_ingress_rule(
            ecs_security_group,
            ec2.Port.tcp(6379),
            "Allow Redis from ECS",
        )

        redis_subnet_group = elasticache.CfnSubnetGroup(
            self,
            "RedisSubnetGroup",
            description="Subnet group for MCP Redis",
            subnet_ids=[subnet.subnet_id for subnet in vpc.public_subnets],
            cache_subnet_group_name="mcp-redis-subnet-group",
        )

        redis_cluster = elasticache.CfnCacheCluster(
            self,
            "RedisCluster",
            engine="redis",
            cache_node_type="cache.t3.micro",  # Free tier eligible
            num_cache_nodes=1,
            cache_subnet_group_name=redis_subnet_group.cache_subnet_group_name,
            vpc_security_group_ids=[redis_security_group.security_group_id],
        )
        redis_cluster.add_dependency(redis_subnet_group)

        redis_url = f"redis://{redis_cluster.attr_redis_endpoint_address}:{redis_cluster.attr_redis_endpoint_port}"

        # ======================================================================
        # Secrets Manager - For sensitive configuration
        # ======================================================================
        app_secret = secretsmanager.Secret(
            self,
            "McpAppSecrets",
            secret_name="wizelit-mcp/app-secrets",
            description="Secrets for Wizelit MCP servers",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"GITHUB_TOKEN": ""}',
                generate_string_key="placeholder",
            ),
        )

        # ======================================================================
        # ECR Repository - Single repo with different tags per server
        # ======================================================================
        ecr_repository = ecr.Repository(
            self,
            "McpRepository",
            repository_name="wizelit-mcp",
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    max_image_count=10,
                    description="Keep only 10 images",
                )
            ],
        )

        # ======================================================================
        # ECS Cluster
        # ======================================================================
        cluster = ecs.Cluster(
            self,
            "McpCluster",
            vpc=vpc,
            cluster_name="wizelit-mcp-cluster",
            container_insights=True,
        )

        # ======================================================================
        # CloudWatch Log Groups
        # ======================================================================
        log_group = logs.LogGroup(
            self,
            "McpLogGroup",
            log_group_name="/ecs/wizelit-mcp",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ======================================================================
        # IAM Role for ECS Tasks
        # ======================================================================
        task_role = iam.Role(
            self,
            "McpTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description="Role for MCP ECS tasks",
        )

        # Bedrock permissions for Refactoring Agent
        task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=["*"],
            )
        )

        # Secrets Manager access
        task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue",
                ],
                resources=[app_secret.secret_arn],
            )
        )

        execution_role = iam.Role(
            self,
            "McpExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                )
            ],
        )

        # ======================================================================
        # Application Load Balancer
        # ======================================================================
        alb = elbv2.ApplicationLoadBalancer(
            self,
            "McpAlb",
            vpc=vpc,
            internet_facing=True,
            security_group=alb_security_group,
        )

        listener = alb.add_listener(
            "HttpListener",
            port=80,
            default_action=elbv2.ListenerAction.fixed_response(
                status_code=404,
                content_type="text/plain",
                message_body="MCP Server not found. Use /code-scout, /refactoring, or /schema-validator",
            ),
        )

        # ======================================================================
        # MCP Server Definitions
        # ======================================================================
        servers = [
            {
                "name": "code-scout",
                "port": 1338,
                "path": "/code-scout/*",
                "priority": 1,
                "health_path": "/sse",  # SSE endpoint
                "env": {
                    "MCP_SERVER": "code-scout",
                    "ENABLE_LOG_STREAMING": "true",
                },
            },
            {
                "name": "refactoring-agent",
                "port": 1337,
                "path": "/refactoring/*",
                "priority": 2,
                "health_path": "/sse",  # SSE endpoint
                "env": {
                    "MCP_SERVER": "refactoring-agent",
                    "ENABLE_LOG_STREAMING": "true",
                },
            },
            {
                "name": "schema-validator",
                "port": 1340,
                "path": "/schema-validator/*",
                "priority": 3,
                "health_path": "/mcp",  # Streamable-HTTP endpoint
                "env": {
                    "MCP_SERVER": "schema-validator",
                    "ENABLE_LOG_STREAMING": "false",
                },
            },
        ]

        services = []
        for server in servers:
            # Task Definition
            task_definition = ecs.FargateTaskDefinition(
                self,
                f"{server['name'].replace('-', '')}TaskDef",
                memory_limit_mib=512,
                cpu=256,
                task_role=task_role,
                execution_role=execution_role,
            )

            container = task_definition.add_container(
                f"{server['name'].replace('-', '')}Container",
                image=ecs.ContainerImage.from_ecr_repository(
                    ecr_repository, f"{server['name']}-latest"
                ),
                logging=ecs.LogDrivers.aws_logs(
                    log_group=log_group,
                    stream_prefix=server["name"],
                ),
                environment={
                    **server["env"],
                    "REDIS_URL": redis_url,
                    "AWS_REGION": self.region,
                },
                secrets={
                    "GITHUB_TOKEN": ecs.Secret.from_secrets_manager(
                        app_secret, "GITHUB_TOKEN"
                    ),
                },
            )

            container.add_port_mappings(
                ecs.PortMapping(
                    container_port=server["port"],
                    protocol=ecs.Protocol.TCP,
                )
            )

            # ECS Service
            service = ecs.FargateService(
                self,
                f"{server['name'].replace('-', '')}Service",
                cluster=cluster,
                task_definition=task_definition,
                desired_count=0,  # Start with 0, scale up after pushing images
                assign_public_ip=True,
                security_groups=[ecs_security_group],
                vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
                circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True),
            )

            # Target Group with path-based routing
            # Note: SSE/MCP endpoints don't return 200 OK for simple GET requests
            # Using permissive health check that accepts various status codes
            # Use the health_path from server config if available, otherwise use root
            health_check_path = server.get("health_path", "/")
            target_group = listener.add_targets(
                f"{server['name'].replace('-', '')}Target",
                port=server["port"],
                protocol=elbv2.ApplicationProtocol.HTTP,
                targets=[service],
                health_check=elbv2.HealthCheck(
                    path=health_check_path,  # Use server-specific health path
                    interval=Duration.seconds(60),
                    timeout=Duration.seconds(30),
                    healthy_threshold_count=2,
                    unhealthy_threshold_count=5,
                    healthy_http_codes="200-499",  # Accept various codes since SSE doesn't return 200
                ),
                conditions=[
                    elbv2.ListenerCondition.path_patterns([server["path"]]),
                ],
                priority=server["priority"],
            )

            services.append(service)

        # ======================================================================
        # GitHub OIDC for CI/CD
        # ======================================================================
        github_oidc_provider_arn = f"arn:aws:iam::{self.account}:oidc-provider/token.actions.githubusercontent.com"

        github_oidc_provider = iam.OpenIdConnectProvider.from_open_id_connect_provider_arn(
            self,
            "GithubOidcProvider",
            open_id_connect_provider_arn=github_oidc_provider_arn,
        )

        github_actions_role = iam.Role(
            self,
            "GithubActionsRole",
            assumed_by=iam.FederatedPrincipal(
                github_oidc_provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                    },
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": "repo:*/*:ref:refs/heads/main",
                    },
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
            description="Role for GitHub Actions to deploy MCP servers",
            max_session_duration=Duration.hours(1),
        )

        # ECR permissions
        github_actions_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                    "ecr:PutImage",
                    "ecr:InitiateLayerUpload",
                    "ecr:UploadLayerPart",
                    "ecr:CompleteLayerUpload",
                ],
                resources=["*"],
            )
        )

        # ECS permissions
        github_actions_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ecs:UpdateService",
                    "ecs:DescribeServices",
                    "ecs:DescribeTaskDefinition",
                    "ecs:RegisterTaskDefinition",
                    "ecs:ListServices",
                ],
                resources=["*"],
            )
        )

        # ======================================================================
        # Outputs
        # ======================================================================
        CfnOutput(
            self,
            "AlbDnsName",
            value=alb.load_balancer_dns_name,
            description="ALB DNS name for MCP servers",
        )

        CfnOutput(
            self,
            "CodeScoutUrl",
            value=f"http://{alb.load_balancer_dns_name}/code-scout/sse",
            description="Code Scout MCP server URL",
        )

        CfnOutput(
            self,
            "RefactoringAgentUrl",
            value=f"http://{alb.load_balancer_dns_name}/refactoring/sse",
            description="Refactoring Agent MCP server URL",
        )

        CfnOutput(
            self,
            "SchemaValidatorUrl",
            value=f"http://{alb.load_balancer_dns_name}/schema-validator/mcp",
            description="Schema Validator MCP server URL",
        )

        CfnOutput(
            self,
            "EcrRepositoryUri",
            value=ecr_repository.repository_uri,
            description="ECR repository URI",
        )

        CfnOutput(
            self,
            "ClusterName",
            value=cluster.cluster_name,
            description="ECS cluster name",
        )

        CfnOutput(
            self,
            "AppSecretArn",
            value=app_secret.secret_arn,
            description="App secrets ARN (add GITHUB_TOKEN here)",
        )

        CfnOutput(
            self,
            "GithubActionsRoleArn",
            value=github_actions_role.role_arn,
            description="GitHub Actions role ARN for CI/CD",
        )
