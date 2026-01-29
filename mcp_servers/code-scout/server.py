"""
Code Scout MCP Server (FastMCP wrapper)
Fast synchronous symbol scanner exposed via HTTP/SSE transport (like refactoring-agent).
Supports local directories and GitHub repositories.
"""

import asyncio
from dataclasses import asdict
from pathlib import Path
from typing import Optional, Dict, Any
from wizelit_sdk.agent_wrapper import WizelitAgent, Job
from ..exceptions import CodeScanError, RepositoryError, SymbolNotFoundError
from .scanner import CodeScout
from .github_helper import GitHubHelper

# Initialize FastMCP wrapper (SSE transport, port 1338 to avoid clashing with refactoring-agent)
mcp = WizelitAgent("CodeScoutAgent", transport="sse", port=1338)


def _init_scout(root_directory: str, github_token: Optional[str]) -> CodeScout:
    """Create a CodeScout instance with caching disabled to ensure fresh results."""
    return CodeScout(root_directory, github_token=github_token, use_cache=False)
def _convert_usage_paths(usages: list[Any], scout: CodeScout) -> list[Any]:
    """Convert cached file paths in usage objects back to GitHub URLs when applicable."""
    parsed = None

    if scout.original_input and "github.com" in scout.original_input.lower():
        parsed = GitHubHelper.parse_github_url(scout.original_input)

    root_path = Path(scout.root_directory).resolve()
    converted = []

    for usage in usages:
        usage_dict = asdict(usage) if hasattr(usage, "__dataclass_fields__") else usage
        if isinstance(usage_dict, dict) and "file_path" in usage_dict:
            try:
                file_path_obj = Path(usage_dict["file_path"]).resolve()
                if file_path_obj.is_relative_to(root_path):
                    rel_path = str(file_path_obj.relative_to(root_path))
                else:
                    rel_path = str(file_path_obj)

                # If GitHub repo, convert to GitHub URL
                if parsed:
                    owner = parsed.get("owner")
                    repo = parsed.get("repo")
                    ref = parsed.get("ref", "main")
                    usage_dict["file_path"] = (
                        f"https://github.com/{owner}/{repo}/blob/{ref}/{rel_path}"
                    )
                else:
                    # For local paths, keep the relative path
                    usage_dict["file_path"] = rel_path
            except Exception:
                pass
        converted.append(usage_dict)

    return converted


def _relative_to_root(
    root: Path, file_path: str, original_input: Optional[str] = None
) -> str:
    """Convert absolute paths to paths relative to the scan root when possible.

    If original_input is a GitHub URL, convert file paths to GitHub file URLs.
    """
    try:
        file_path_obj = Path(file_path).resolve()
        root_resolved = root.resolve()

        # If this is a GitHub repository, convert to GitHub URL format
        if original_input and "github.com" in original_input.lower():
            parsed = GitHubHelper.parse_github_url(original_input)
            if parsed:
                # Get relative path from root
                if file_path_obj.is_relative_to(root_resolved):
                    rel_path = str(file_path_obj.relative_to(root_resolved))
                else:
                    rel_path = str(file_path_obj)

                # Build GitHub URL
                owner = parsed.get("owner")
                repo = parsed.get("repo")
                ref = parsed.get("ref", "main")  # Default to main branch

                # Construct the GitHub blob URL
                return f"https://github.com/{owner}/{repo}/blob/{ref}/{rel_path}"

        # For local paths, return relative path if possible
        if file_path_obj.is_relative_to(root_resolved):
            return str(file_path_obj.relative_to(root_resolved))
        return str(file_path_obj)
    except Exception:
        return file_path


@mcp.ingest(
    is_long_running=False,
    description="Scan a directory or GitHub repo for Python files and symbol usages.",
)
async def scan_directory(
    root_directory: str,
    pattern: str = "*.py",
    github_token: Optional[str] = None,
) -> dict[str, list[Any]]:
    """
    Scans a directory or GitHub repo for Python files and symbol usages.

    Args:
        root_directory: Path to the directory or GitHub repo URL to scan
        pattern: File pattern to match (default: "*.py")
        github_token: Optional GitHub token for accessing private repositories

    Returns:
        Dictionary mapping symbols to their usage locations
    """
    def _run():
        try:
            scout = _init_scout(root_directory, github_token)
        except Exception as e:
            raise RepositoryError(root_directory, "initialization", str(e))

        try:
            result = scout.scan_directory(pattern)
            converted = {}
            for symbol, usages in result.items():
                converted_usages = _convert_usage_paths(usages, scout)
                converted[symbol] = converted_usages
            return converted
        except Exception as e:
            raise CodeScanError(f"Scan failed for pattern {pattern}", str(e))
        finally:
            scout.cleanup()

    return await asyncio.to_thread(_run)


@mcp.ingest(
    is_long_running=False,
    description="[RAW JSON - DO NOT USE] Find all usages of a symbol. Returns raw JSON array. Use 'code_scout_symbol_usage' instead for formatted human-readable output.",
)
async def find_symbol(
    root_directory: str,
    symbol_name: str,
    pattern: str = "*.py",
    github_token: Optional[str] = None,
) -> list[Any]:
    """
    Finds all usages of a symbol in the scanned codebase.

    Args:
        root_directory: Path to the directory or GitHub repo URL to scan
        symbol_name: Name of the symbol to find
        pattern: File pattern to match (default: "*.py")
        github_token: Optional GitHub token for accessing private repositories

    Returns:
        List of usage locations for the specified symbol
    """
    def _run():
        scout = _init_scout(root_directory, github_token)
        try:
            if not scout.symbol_usages:
                scout.scan_directory(pattern)
            result = scout.find_symbol(symbol_name)
            converted = _convert_usage_paths(result, scout)
            return converted
        finally:
            scout.cleanup()

    return await asyncio.to_thread(_run)


@mcp.ingest(is_long_running=False, description="Analyze impact of changing a symbol.")
async def analyze_impact(
    root_directory: str,
    symbol_name: str,
    pattern: str = "*.py",
    github_token: Optional[str] = None,
) -> dict[str, Any]:
    """
    Analyzes the impact of changing a symbol in the codebase.

    Args:
        root_directory: Path to the directory or GitHub repo URL to scan
        symbol_name: Name of the symbol to analyze
        pattern: File pattern to match (default: "*.py")
        github_token: Optional GitHub token for accessing private repositories

    Returns:
        Impact analysis results for the specified symbol
    """
    def _run():
        scout = _init_scout(root_directory, github_token)
        try:
            if not scout.symbol_usages:
                scout.scan_directory(pattern)
            return scout.analyze_impact(symbol_name)
        finally:
            scout.cleanup()

    return await asyncio.to_thread(_run)


@mcp.ingest(
    is_long_running=False,
    description="Grep for a pattern across a directory or GitHub repo.",
)
async def grep_search(
    root_directory: str,
    pattern: str,
    file_pattern: str = "*.py",
    github_token: Optional[str] = None,
) -> list[dict[str, Any]]:
    def _run():
        scout = _init_scout(root_directory, github_token)
        try:
            matches = scout.grep_search(pattern=pattern, file_pattern=file_pattern)

            # Convert file paths in matches if it's a GitHub repo
            if scout.original_input and "github.com" in scout.original_input.lower():
                parsed = GitHubHelper.parse_github_url(scout.original_input)
                if parsed:
                    owner = parsed.get("owner")
                    repo = parsed.get("repo")
                    ref = parsed.get("ref", "main")
                    root_path = Path(scout.root_directory).resolve()

                    for match in matches:
                        if "file" in match:
                            try:
                                file_path_obj = Path(match["file"]).resolve()
                                if file_path_obj.is_relative_to(root_path):
                                    rel_path = str(file_path_obj.relative_to(root_path))
                                else:
                                    rel_path = str(file_path_obj)
                                match["file"] = (
                                    f"https://github.com/{owner}/{repo}/blob/{ref}/{rel_path}"
                                )
                            except Exception:
                                pass

            return matches
        finally:
            scout.cleanup()

    return await asyncio.to_thread(_run)


@mcp.ingest(is_long_running=False, description="Git blame for a specific line.")
async def git_blame(
    root_directory: str,
    file_path: str,
    line_number: int,
    github_token: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    def _run():
        scout = _init_scout(root_directory, github_token)
        try:
            return scout.git_blame(file_path, line_number)
        finally:
            scout.cleanup()

    return await asyncio.to_thread(_run)


@mcp.ingest(
    is_long_running=False, description="Build a dependency graph from symbol usages."
)
async def build_dependency_graph(
    root_directory: str,
    pattern: str = "*.py",
    github_token: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    def _run():
        scout = _init_scout(root_directory, github_token)
        try:
            if not scout.symbol_usages:
                scout.scan_directory(pattern)
            graph = scout.build_dependency_graph()

            # Convert file paths in nodes if it's a GitHub repo
            result = {}
            for symbol, node in graph.items():
                node_dict = asdict(node)
                if (
                    scout.original_input
                    and "github.com" in scout.original_input.lower()
                ):
                    parsed = GitHubHelper.parse_github_url(scout.original_input)
                    if parsed and "file_path" in node_dict:
                        owner = parsed.get("owner")
                        repo = parsed.get("repo")
                        ref = parsed.get("ref", "main")
                        root_path = Path(scout.root_directory).resolve()
                        try:
                            file_path_obj = Path(node_dict["file_path"]).resolve()
                            if file_path_obj.is_relative_to(root_path):
                                rel_path = str(file_path_obj.relative_to(root_path))
                            else:
                                rel_path = str(file_path_obj)
                            node_dict["file_path"] = (
                                f"https://github.com/{owner}/{repo}/blob/{ref}/{rel_path}"
                            )
                        except Exception:
                            pass
                result[symbol] = node_dict

            return result
        finally:
            scout.cleanup()

    return await asyncio.to_thread(_run)


@mcp.ingest(
    is_long_running=False,
    description="Generate a Mermaid graph visualization from dependency graph. Returns Mermaid markdown that can be rendered visually.",
    response_handling={
        "mode": "direct",
    },
)
async def visualize_dependency_graph(
    target: str,
    pattern: str = "*.py",
    github_token: Optional[str] = None,
    max_nodes: int = 50,
    show_files: bool = False,
) -> str:
    """
    Generate a Mermaid graph diagram from the dependency graph.

    Args:
        target: Path to the directory or GitHub repo URL to analyze
        pattern: File pattern to match (default: "*.py")
        github_token: Optional GitHub token for accessing private repositories
        max_nodes: Maximum number of nodes to include (default: 50)
        show_files: If True, include file paths in node labels

    Returns:
        Mermaid markdown string for graph visualization
    """
    def _run() -> str:
        scout = _init_scout(target, github_token)
        try:
            if not scout.symbol_usages:
                scout.scan_directory(pattern)

            graph = scout.build_dependency_graph()

            if not graph:
                return "No dependency graph data found. Try scanning the directory first."

            # Convert DependencyNode objects to dicts
            graph_dicts: Dict[str, Dict[str, Any]] = {}
            for symbol, node in graph.items():
                # Always convert to dict for consistent handling
                if hasattr(node, "__dataclass_fields__"):
                    node_dict: Dict[str, Any] = asdict(node)
                elif isinstance(node, dict):
                    node_dict = node
                else:
                    # Fallback: convert to dict and cast
                    node_dict = dict(node)  # type: ignore[arg-type]

                # Convert file paths for GitHub repos
                if scout.original_input and "github.com" in scout.original_input.lower():
                    parsed = GitHubHelper.parse_github_url(scout.original_input)
                    if parsed and isinstance(node_dict, dict) and "file_path" in node_dict:
                        owner = parsed.get("owner")
                        repo = parsed.get("repo")
                        ref = parsed.get("ref", "main")
                        root_path = Path(scout.root_directory).resolve()
                        try:
                            file_path_obj = Path(node_dict["file_path"]).resolve()
                            if file_path_obj.is_relative_to(root_path):
                                rel_path = str(file_path_obj.relative_to(root_path))
                            else:
                                rel_path = str(file_path_obj)
                            node_dict["file_path"] = (
                                f"https://github.com/{owner}/{repo}/blob/{ref}/{rel_path}"
                            )
                        except Exception:
                            pass

                graph_dicts[symbol] = node_dict

            # Filter to most interesting nodes (those with dependencies or dependents)
            interesting_nodes = {
                symbol: node for symbol, node in graph_dicts.items()
                if node.get("dependencies") or node.get("dependents")
            }

            # Limit number of nodes if too many
            if len(interesting_nodes) > max_nodes:
                # Prioritize nodes with most connections
                sorted_nodes = sorted(
                    interesting_nodes.items(),
                    key=lambda x: len(x[1].get("dependencies", [])) + len(x[1].get("dependents", [])),
                    reverse=True
                )
                interesting_nodes = dict(sorted_nodes[:max_nodes])

            # Build Mermaid graph
            lines = ["```mermaid", "graph TD"]

            # Add nodes with descriptions
            node_ids = {}
            for idx, (symbol, node) in enumerate(interesting_nodes.items()):
                node_id = f"N{idx}"
                node_ids[symbol] = node_id

                # Create label
                if show_files:
                    file_path = node.get("file_path", "")
                    if "/" in file_path:
                        file_name = file_path.split("/")[-1]
                    else:
                        file_name = file_path
                    label = f"{symbol}<br/><small>{file_name}</small>"
                else:
                    label = symbol

                # Determine node shape based on connections
                dep_count = len(node.get("dependencies", []))
                dependent_count = len(node.get("dependents", []))

                if dep_count == 0 and dependent_count > 0:
                    # Source node (no deps, has dependents)
                    lines.append(f'    {node_id}["{label}"]')
                    lines.append(f'    style {node_id} fill:#90EE90')
                elif dep_count > 0 and dependent_count == 0:
                    # Leaf node (has deps, no dependents)
                    lines.append(f'    {node_id}("{label}")')
                    lines.append(f'    style {node_id} fill:#FFB6C1')
                elif dep_count > 2 or dependent_count > 2:
                    # Hub node (many connections)
                    lines.append(f'    {node_id}{{"{label}"}}')
                    lines.append(f'    style {node_id} fill:#FFD700')
                else:
                    # Regular node
                    lines.append(f'    {node_id}["{label}"]')

            # Add edges (dependencies)
            for symbol, node in interesting_nodes.items():
                if symbol not in node_ids:
                    continue

                source_id = node_ids[symbol]
                for dep in node.get("dependencies", []):
                    if dep in node_ids:
                        target_id = node_ids[dep]
                        lines.append(f"    {source_id} --> {target_id}")

            lines.append("```")
            lines.append("")
            lines.append("**Legend:**")
            lines.append("- 🟢 Green rectangles: Source nodes (no dependencies, others depend on them)")
            lines.append("- 🔴 Pink rounded: Leaf nodes (have dependencies, nothing depends on them)")
            lines.append("- 🟡 Yellow diamonds: Hub nodes (highly connected, 3+ connections)")
            lines.append("- ⬜ White rectangles: Regular nodes")
            lines.append("")

            # Add statistics
            total_symbols = len(interesting_nodes)
            total_edges = sum(len(node.get("dependencies", [])) for node in interesting_nodes.values())

            lines.append(f"**Statistics:**")
            lines.append(f"- Total symbols shown: {total_symbols}")
            lines.append(f"- Total dependencies: {total_edges}")

            if len(graph) > len(interesting_nodes):
                lines.append(f"- Note: {len(graph) - len(interesting_nodes)} isolated symbols hidden")

            return "\n".join(lines)
        finally:
            scout.cleanup()

    return await asyncio.to_thread(_run)


# Text-oriented tools matching the previous refactoring-agent behavior


@mcp.ingest(
    is_long_running=False,
    description="Find symbol usages and analyze impact in an EXISTING codebase or repository. Requires a target (directory path or GitHub URL) to search in. Use this tool ONLY when the user provides or points to an existing codebase/repository to analyze. Do NOT use for generating new code or examples.",
    response_handling={
        "mode": "direct",
    },
)
async def code_scout_symbol_usage(
    target: str,
    symbol: str,
    file_pattern: str = "*.py",
    github_token: Optional[str] = None,
    max_results: int = 50,
    include_graph: bool = True,
) -> str:
    def _run() -> str:
        scout = _init_scout(target, github_token)
        try:
            scout.scan_directory(pattern=file_pattern)
            usages = scout.find_symbol(symbol)

            if not usages:
                return f"No usages for '{symbol}' found in {target}."

            impact = scout.analyze_impact(symbol)
            root_path = Path(scout.root_directory).resolve()

            lines = [
                f"Code Scout report for '{symbol}'",
                f"Target: {target}",
                f"Total usages: {impact.get('total_usages', len(usages))}",
            ]

            breakdown = impact.get("usage_breakdown", {})
            if breakdown:
                lines.append(
                    "Breakdown: "
                    + ", ".join(f"{key}={value}" for key, value in breakdown.items())
                )

            if include_graph:
                deps = impact.get("dependencies", [])
                dependents = impact.get("dependents", [])
                if deps:
                    lines.append("Depends on: " + ", ".join(sorted(deps)))
                if dependents:
                    lines.append("Used by: " + ", ".join(sorted(dependents)))

            lines.append("Top matches:")
            for usage in usages[:max_results]:
                rel_path = _relative_to_root(
                    root_path, usage.file_path, scout.original_input
                )
                lines.append(
                    f"- {rel_path}:{usage.line_number} [{usage.usage_type}] {usage.context}"
                )

            if len(usages) > max_results:
                lines.append(f"(trimmed to first {max_results} results)")

            return "\n".join(lines)
        finally:
            scout.cleanup()

    return await asyncio.to_thread(_run)


@mcp.ingest(
    is_long_running=False,
    description="Search for text patterns in an EXISTING codebase or repository. Requires a target (directory path or GitHub URL) to search in. Use this tool ONLY when the user provides or points to an existing codebase/repository to search. Do NOT use for generating new code or examples.",
    response_handling={
        "mode": "direct",
    },
)
async def code_scout_grep(
    job: Job,
    target: str,
    pattern: str,
    file_pattern: str = "*.py",
    github_token: Optional[str] = None,
    max_results: int = 50,
) -> str:
    def _run() -> str:
        scout = _init_scout(target, github_token)
        try:
            matches = scout.grep_search(pattern=pattern, file_pattern=file_pattern)
            if not matches:
                return f"No matches for '{pattern}' found in {target}."

            root_path = Path(scout.root_directory).resolve()
            lines = [f"Grep results for '{pattern}'", f"Target: {target}", "Matches:"]

            for match in matches[:max_results]:
                rel_path = _relative_to_root(
                    root_path,
                    match.get("file", match.get("path", "?")),
                    scout.original_input,
                )
                lines.append(
                    f"- {rel_path}:{match.get('line_number')} {match.get('content')}"
                )

            if len(matches) > max_results:
                lines.append(f"(trimmed to first {max_results} results)")

            return "\n".join(lines)
        finally:
            scout.cleanup()

    return await asyncio.to_thread(_run)


if __name__ == "__main__":
    # Run with HTTP/SSE transport so it behaves like refactoring-agent
    mcp.run()
