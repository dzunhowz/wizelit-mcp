"""
Custom exceptions for MCP Servers with helpful error messages and suggestions.
"""


class MCPServerException(Exception):
    """Base exception class for all MCP Server errors."""

    def __init__(self, message: str, suggestion: str = ""):
        self.message = message
        self.suggestion = suggestion
        full_message = message
        if suggestion:
            full_message = f"{message}\n💡 Suggestion: {suggestion}"
        super().__init__(full_message)


class CodeScanError(MCPServerException):
    """Raised when code scanning fails."""

    def __init__(self, reason: str = "", original_error: str = ""):
        message = "Failed to scan code"
        if reason:
            message += f": {reason}"
        if original_error:
            message += f" ({original_error})"
        suggestion = (
            "1. Verify the directory or repository path is correct and accessible\n"
            "2. Ensure you have read permissions for the directory\n"
            "3. Check if the path contains valid Python files\n"
            "4. For GitHub repos, verify the URL format is correct\n"
            "5. Check that Git is installed if scanning a GitHub repository"
        )
        super().__init__(message, suggestion)


class RepositoryError(MCPServerException):
    """Raised when repository operations fail."""

    def __init__(self, repo_path: str, operation: str = "", original_error: str = ""):
        message = f"Repository operation failed for '{repo_path}'"
        if operation:
            message += f" ({operation})"
        if original_error:
            message += f": {original_error}"
        suggestion = (
            f"1. Verify the repository path '{repo_path}' exists and is accessible\n"
            f"2. Check if it's a valid Git repository\n"
            f"3. Verify you have sufficient permissions to access the repository\n"
            f"4. For remote repositories, check network connectivity\n"
            f"5. Ensure Git is properly installed and configured"
        )
        super().__init__(message, suggestion)


class GitHubAuthenticationError(MCPServerException):
    """Raised when GitHub authentication fails."""

    def __init__(self, reason: str = ""):
        message = "GitHub authentication failed"
        if reason:
            message += f": {reason}"
        suggestion = (
            "1. Verify GITHUB_TOKEN is set as an environment variable\n"
            "2. Check that the token has not expired\n"
            "3. Verify the token has required scopes (repo, read:org)\n"
            "4. Check GitHub API rate limits haven't been exceeded\n"
            "5. Try regenerating the token at github.com/settings/tokens"
        )
        super().__init__(message, suggestion)


class SymbolNotFoundError(MCPServerException):
    """Raised when a symbol cannot be found during scanning."""

    def __init__(self, symbol_name: str, context: str = ""):
        message = f"Symbol '{symbol_name}' not found"
        if context:
            message += f" in {context}"
        suggestion = (
            f"1. Verify the symbol name '{symbol_name}' is spelled correctly\n"
            f"2. Check that the symbol is defined in the scanned codebase\n"
            f"3. Verify the symbol is exported (not private)\n"
            f"4. Check if the symbol is in a different module/file\n"
            f"5. Re-run the scan to refresh the symbol index"
        )
        super().__init__(message, suggestion)


class FormattingError(MCPServerException):
    """Raised when code formatting fails."""

    def __init__(self, file_path: str = "", original_error: str = ""):
        message = "Code formatting failed"
        if file_path:
            message = f"Failed to format file: {file_path}"
        if original_error:
            message += f" ({original_error})"
        suggestion = (
            "1. Verify the file exists and is readable\n"
            "2. Check if the file contains valid Python code\n"
            "3. Verify the formatter is properly installed\n"
            "4. Check for syntax errors in the code that prevent formatting\n"
            "5. Try manually fixing syntax errors and retrying"
        )
        super().__init__(message, suggestion)


class ValidationError(MCPServerException):
    """Raised when validation fails."""

    def __init__(self, schema_name: str = "", reason: str = ""):
        message = "Validation failed"
        if schema_name:
            message = f"Schema validation failed for '{schema_name}'"
        if reason:
            message += f": {reason}"
        suggestion = (
            "1. Verify the input matches the expected schema\n"
            "2. Check all required fields are provided\n"
            "3. Verify field types are correct (string, number, boolean, etc.)\n"
            "4. Check if there are format requirements (email, URL, etc.)\n"
            "5. Review the schema documentation for valid values"
        )
        super().__init__(message, suggestion)


class RefactoringError(MCPServerException):
    """Raised when code refactoring fails."""

    def __init__(self, refactoring_type: str = "", original_error: str = ""):
        message = "Code refactoring failed"
        if refactoring_type:
            message += f" ({refactoring_type})"
        if original_error:
            message += f": {original_error}"
        suggestion = (
            "1. Verify the code is syntactically valid\n"
            "2. Check that the refactoring type is supported\n"
            "3. Review the code for patterns that may not be refactorable\n"
            "4. Check if there are conflicting imports or definitions\n"
            "5. Try refactoring smaller portions of code at a time"
        )
        super().__init__(message, suggestion)


class ToolExecutionError(MCPServerException):
    """Raised when a tool execution fails."""

    def __init__(self, tool_name: str, reason: str = "", original_error: str = ""):
        message = f"Tool execution failed: {tool_name}"
        if reason:
            message += f" ({reason})"
        if original_error:
            message += f": {original_error}"
        suggestion = (
            f"1. Verify all required parameters for '{tool_name}' are provided\n"
            f"2. Check that parameter values are in the correct format\n"
            f"3. Review the tool documentation for usage details\n"
            f"4. Check if external dependencies are available\n"
            f"5. Review the tool's logs for detailed error information"
        )
        super().__init__(message, suggestion)


class FileOperationError(MCPServerException):
    """Raised when file I/O operations fail."""

    def __init__(self, operation: str, file_path: str, original_error: str = ""):
        message = f"File operation '{operation}' failed for '{file_path}'"
        if original_error:
            message += f": {original_error}"
        suggestion = (
            f"1. Verify the file/directory path exists: {file_path}\n"
            f"2. Check file permissions (read/write/execute as needed)\n"
            f"3. Verify disk space is available\n"
            f"4. Check if another process is using the file\n"
            f"5. Ensure the file path doesn't contain invalid characters"
        )
        super().__init__(message, suggestion)


class ConfigurationError(MCPServerException):
    """Raised when configuration is invalid or missing."""

    def __init__(self, config_key: str, expected_value: str = ""):
        message = f"Configuration error: {config_key} is missing or invalid"
        if expected_value:
            message += f" (expected: {expected_value})"
        suggestion = (
            f"1. Verify {config_key} is set in environment variables\n"
            f"2. Check the value format is correct\n"
            f"3. Review the configuration documentation\n"
            f"4. Check the .env file or deployment configuration\n"
            f"5. Restart the server after changing configuration"
        )
        super().__init__(message, suggestion)


class TimeoutError(MCPServerException):
    """Raised when an operation exceeds the timeout limit."""

    def __init__(self, operation: str, timeout_seconds: float):
        message = f"Operation '{operation}' exceeded timeout of {timeout_seconds} seconds"
        suggestion = (
            f"1. The {operation} took too long to complete\n"
            f"2. Check system resources (CPU, memory, disk)\n"
            f"3. Verify network connectivity for remote operations\n"
            f"4. Try with simpler inputs or smaller datasets\n"
            f"5. Check logs for performance bottlenecks"
        )
        super().__init__(message, suggestion)


class APIError(MCPServerException):
    """Raised when external API calls fail."""

    def __init__(self, api_name: str, status_code: int = 0, reason: str = ""):
        message = f"API error from {api_name}"
        if status_code:
            message += f" (HTTP {status_code})"
        if reason:
            message += f": {reason}"
        suggestion = (
            f"1. Check if {api_name} service is operational\n"
            f"2. Verify API credentials and authentication\n"
            f"3. Check if API rate limits have been exceeded\n"
            f"4. Verify network connectivity to the API\n"
            f"5. Check API status page for known issues"
        )
        super().__init__(message, suggestion)
