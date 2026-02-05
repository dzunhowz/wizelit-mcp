"""
Schema Validator MCP Server (Streamable-HTTP transport)
Fast synchronous code validation using AST analysis.
Demonstrates Streamable-HTTP transport compatibility.
"""
import os
import sys
from typing import Optional, List, Dict, Any

# Ensure wizelit_sdk and validator can be imported
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from wizelit_sdk.agent_wrapper import WizelitAgent

# Import validator from current directory
CURRENT_DIR = os.path.dirname(__file__)
sys.path.insert(0, CURRENT_DIR)
from validator import SchemaValidator

# Initialize FastMCP wrapper with Streamable-HTTP transport
# FastMCP exposes streamable-http at /mcp endpoint
# Port can be overridden via MCP_SERVER_PORT env var (used by Docker entrypoint for proxy setup)
_default_port = 1340
_server_port = int(os.getenv("MCP_SERVER_PORT", str(_default_port)))
mcp = WizelitAgent(
    "SchemaValidatorStreamableHTTP",
    transport="streamable-http",
    port=_server_port
)


@mcp.ingest(
    is_long_running=False,
    description="Validate Python function signature. CRITICAL: expected_params must be JSON string like '[\"x\", \"y\"]'",
    response_handling={
        "mode": "formatted",
        "extract_path": "content[0].text",
        "content_type": "json",
        "template": "### ✅ Function Signature Validation\n\n```json\n{value}\n```",
    },
)
async def validate_function_signature(
    code: str,
    function_name: str,
    expected_params: str,  # JSON string of list - MUST be format: '["param1", "param2"]'
    expected_return_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validates a function signature in Python code.
    
    PARAMETER FORMAT REQUIREMENTS:
    ================================
    - code: Python source code containing the function
    - function_name: Exact function name to validate (e.g., "calculate")
    - expected_params: MUST BE A JSON STRING ARRAY with parameter names. Examples:
        * '["x", "y", "z"]' for functions with 3 parameters
        * '["items", "tax_rate"]' for functions with 2 parameters  
        * '[]' for functions with no parameters
    - expected_return_type: Optional return type as string (e.g., "float", "str", "dict", "bool")
    
    IMPORTANT: expected_params MUST be a JSON-formatted string, not a Python list!
    
    Returns:
        Validation result with function details and parameter matching
    """
    try:
        import json
        params = json.loads(expected_params) if isinstance(expected_params, str) else expected_params
    except (json.JSONDecodeError, ValueError):
        return {
            "error": "Invalid expected_params format. Should be JSON list of strings.",
            "valid": False,
        }
    
    validator = SchemaValidator()
    result = validator.validate_function_signature(
        code,
        function_name,
        params,
        expected_return_type,
    )
    return result


@mcp.ingest(
    is_long_running=False,
    description="Validate Python class structure. CRITICAL: expected_methods must be JSON string like '[\"method1\", \"method2\"]'",
    response_handling={
        "mode": "formatted",
        "extract_path": "content[0].text",
        "content_type": "json",
        "template": "### ✅ Class Structure Validation\n\n```json\n{value}\n```",
    },
)
async def validate_class_structure(
    code: str,
    class_name: str,
    expected_methods: str,  # JSON string of list - MUST be format: '["method1", "method2"]'
) -> Dict[str, Any]:
    """
    Validates a class structure in Python code.
    
    PARAMETER FORMAT REQUIREMENTS:
    ================================
    - code: Python source code containing the class
    - class_name: Exact class name to validate (e.g., "DataProcessor")
    - expected_methods: MUST BE A JSON STRING ARRAY with method names. Examples:
        * '["__init__", "process", "validate"]' for classes with 3 methods
        * '["process", "validate"]' for classes with 2 methods (no __init__)
        * '[]' for classes with no methods
    
    IMPORTANT: expected_methods MUST be a JSON-formatted string, not a Python list!
    
    Returns:
        Validation result with class structure and method matching details
    """
    try:
        import json
        methods = json.loads(expected_methods) if isinstance(expected_methods, str) else expected_methods
    except (json.JSONDecodeError, ValueError):
        return {
            "error": "Invalid expected_methods format. Should be JSON list of strings.",
            "valid": False,
        }
    
    validator = SchemaValidator()
    result = validator.validate_class_structure(code, class_name, methods)
    return result


@mcp.ingest(
    is_long_running=False,
    description="Analyze Python code quality metrics (type hints, docstrings, etc).",
    response_handling={
        "mode": "formatted",
        "extract_path": "content[0].text",
        "content_type": "json",
        "template": "### ✅ Code Quality Analysis\n\n```json\n{value}\n```",
    },
)
async def analyze_code_quality(code: str) -> Dict[str, Any]:
    """
    Performs code quality analysis on Python code.
    
    Args:
        code: Python source code to analyze
        
    Returns:
        Dict with quality metrics
    """
    validator = SchemaValidator()
    result = validator.validate_code_quality(code)
    return result


if __name__ == "__main__":
    # Schema Validator uses Streamable-HTTP transport
    # This enables custom header support and POST-based streaming
    mcp.run(transport="streamable-http")

