#!/usr/bin/env python3
"""
AWS CDK App for Wizelit MCP Servers
Deploys Code Scout, Refactoring Agent, and Schema Validator to AWS ECS Fargate.
"""
import os
import aws_cdk as cdk
from mcp_servers_stack import McpServersStack

app = cdk.App()

# Get environment from context or use defaults
env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "ap-southeast-2"),
)

McpServersStack(
    app,
    "McpServersStack",
    stack_name="wizelit-mcp-dev",
    env=env,
    description="Wizelit MCP Servers - Code Scout, Refactoring Agent, Schema Validator",
)

app.synth()
