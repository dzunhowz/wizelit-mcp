"""
Code Formatter MCP Server (Stdio transport)
Fast lightweight code formatting using AST analysis.
Demonstrates Stdio transport compatibility (local process execution).
"""
import os
import sys
from typing import Dict, Any, Optional

# Ensure wizelit_sdk and formatter can be imported
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from wizelit_sdk.agent_wrapper import WizelitAgentWrapper

# Import formatter from current directory
CURRENT_DIR = os.path.dirname(__file__)
sys.path.insert(0, CURRENT_DIR)
from formatter import CodeFormatter

# Initialize FastMCP wrapper with Stdio transport
# Stdio is perfect for lightweight local agents that can be spawned by parent process
mcp = WizelitAgentWrapper(
    "CodeFormatterAgent",
    transport="stdio",
)


@mcp.ingest(
    is_long_running=False,
    description="Apply Black-style formatting rules to Python code.",
    response_handling={
        "mode": "formatted",
        "extract_path": "content[0].text",
        "content_type": "json",
        "template": "### ✅ Code Formatted Successfully\n\n```json\n{value}\n```"
    }
)
async def format_code(code: str) -> Dict[str, Any]:
    """
    Format Python code with Black-style rules.
    
    Performs:
    - Remove trailing whitespace
    - Normalize blank lines (max 2 consecutive)
    - Ensure single trailing newline
    
    Args:
        code: Python source code to format
        
    Returns:
        Dict with formatted code and statistics
    """
    result = CodeFormatter.format_with_black_rules(code)
    return result


@mcp.ingest(
    is_long_running=False,
    description="Organize and sort Python import statements.",
    response_handling={
        "mode": "formatted",
        "extract_path": "content[0].text",
        "content_type": "json",
        "template": "### ✅ Imports Organized\n\n```json\n{value}\n```"
    }
)
async def organize_imports(code: str) -> Dict[str, Any]:
    """
    Organize Python import statements.
    
    Organizes imports into:
    1. Standard library imports
    2. Third-party imports
    3. Local imports
    
    Args:
        code: Python source code
        
    Returns:
        Dict with organized code and import statistics
    """
    result = CodeFormatter.normalize_imports(code)
    return result


@mcp.ingest(
    is_long_running=False,
    description="Normalize indentation in Python code.",
    response_handling={
        "mode": "formatted",
        "extract_path": "content[0].text",
        "content_type": "json",
        "template": "### ✅ Indentation Normalized\n\n```json\n{value}\n```"
    }
)
async def normalize_indentation(
    code: str,
    indent_size: int = 4,
) -> Dict[str, Any]:
    """
    Normalize indentation in Python code.
    
    Args:
        code: Python source code
        indent_size: Target indentation size (default: 4 spaces)
        
    Returns:
        Dict with reformatted code
    """
    result = CodeFormatter.indent_code(code, indent_size)
    return result


@mcp.ingest(
    is_long_running=False,
    description="Apply all formatting rules to Python code (full format).",
    response_handling={
        "mode": "formatted",
        "extract_path": "content[0].text",
        "content_type": "json",
        "template": "### ✅ Code Fully Formatted\n\n```json\n{value}\n```"
    }
)
async def format_all(code: str, indent_size: int = 4) -> Dict[str, Any]:
    """
    Apply all formatting rules in sequence.
    
    Steps:
    1. Organize imports
    2. Normalize indentation
    3. Apply Black-style formatting
    
    Args:
        code: Python source code
        indent_size: Target indentation size
        
    Returns:
        Dict with fully formatted code
    """
    # Step 1: Organize imports
    result1 = CodeFormatter.normalize_imports(code)
    if not result1['success']:
        return result1
    
    code = result1['formatted_code']
    
    # Step 2: Normalize indentation
    result2 = CodeFormatter.indent_code(code, indent_size)
    if not result2['success']:
        return result2
    
    code = result2['formatted_code']
    
    # Step 3: Apply Black-style formatting
    result3 = CodeFormatter.format_with_black_rules(code)
    if not result3['success']:
        return result3
    
    return {
        "success": True,
        "formatted_code": result3['formatted_code'],
        "steps_applied": ["organize_imports", "normalize_indentation", "format_code"],
        "import_organization": result1,
        "indentation_normalization": result2,
        "code_formatting": result3,
    }


if __name__ == "__main__":
    # Run with stdio transport for local process execution
    # Note: Use _mcp.run() directly to avoid passing host/port to stdio transport
    mcp._mcp.run(transport="stdio")
