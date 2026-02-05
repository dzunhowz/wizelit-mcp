#!/usr/bin/env python3
"""
Simple reverse proxy that strips ALB path prefixes and rewrites SSE responses.

The ALB routes:
  /code-scout/* → Code Scout container (expects /sse)
  /refactoring/* → Refactoring Agent container (expects /sse)
  /schema-validator/* → Schema Validator container (expects /mcp)

This proxy:
1. Strips the first path segment for incoming requests (/code-scout/sse -> /sse)
2. Rewrites SSE endpoint responses to include the path prefix (/messages/ -> /code-scout/messages/)
"""
import asyncio
import os
import re
from aiohttp import web, ClientSession, ClientTimeout

# Configuration from environment
# BACKEND_PORT: where the MCP server is running (internal)
# PROXY_PORT: where this proxy listens (external, for ALB)
BACKEND_PORT = int(os.environ.get("BACKEND_PORT", 9000))
PROXY_PORT = int(os.environ.get("PROXY_PORT", 1338))


def get_path_prefix(original_path: str) -> str:
    """Extract the path prefix from the original request path."""
    # /code-scout/sse -> /code-scout
    parts = original_path.strip("/").split("/", 1)
    if parts:
        return "/" + parts[0]
    return ""


def rewrite_sse_line(line: bytes, path_prefix: str) -> bytes:
    """Rewrite SSE endpoint URLs to include the path prefix."""
    try:
        text = line.decode("utf-8")
        
        # Rewrite /messages/ and /sse paths in SSE data
        # The MCP protocol sends endpoint info like: data: /messages/?session_id=xxx
        if path_prefix and ("/messages" in text or "endpoint" in text.lower()):
            # Rewrite /messages/ to /prefix/messages/
            text = re.sub(
                r'(["\s])/messages',
                rf'\1{path_prefix}/messages',
                text
            )
            # Also handle bare /messages at start of data line
            text = re.sub(
                r'^(data:\s*)/messages',
                rf'\1{path_prefix}/messages',
                text
            )
            print(f"[Proxy] Rewriting SSE: {line.decode('utf-8').strip()} → {text.strip()}", flush=True)
        
        return text.encode("utf-8")
    except Exception:
        return line


async def proxy_handler(request: web.Request) -> web.StreamResponse:
    """Proxy requests to the backend, stripping the path prefix."""
    original_path = request.path
    
    # Extract path prefix for SSE rewriting
    path_prefix = get_path_prefix(original_path)
    
    # Remove the first path segment (e.g., /code-scout/sse -> /sse)
    # Use lstrip to preserve trailing slash (important for /messages/ endpoint)
    path_parts = original_path.lstrip("/").split("/", 1)
    if len(path_parts) > 1:
        new_path = "/" + path_parts[1]
    else:
        new_path = "/"
    
    # Build backend URL
    query_string = request.query_string
    if query_string:
        backend_url = f"http://127.0.0.1:{BACKEND_PORT}{new_path}?{query_string}"
    else:
        backend_url = f"http://127.0.0.1:{BACKEND_PORT}{new_path}"
    
    print(f"[Proxy] {request.method} {original_path} → {new_path}", flush=True)
    
    # Handle SSE (Server-Sent Events)
    # SSE uses GET requests to /sse endpoint, while streamable-http uses POST to /mcp
    # Check both the Accept header AND the method/path to distinguish them
    is_sse = (
        request.method.upper() == "GET"
        and ("/sse" in new_path or new_path.endswith("/sse"))
        and "text/event-stream" in request.headers.get("Accept", "")
    )
    
    if is_sse:
        return await proxy_sse(request, backend_url, path_prefix)
    
    # Regular HTTP proxy (handles POST for streamable-http, GET for other requests)
    timeout = ClientTimeout(total=300)
    async with ClientSession(timeout=timeout) as session:
        # Forward headers (excluding hop-by-hop headers)
        headers = {
            k: v for k, v in request.headers.items()
            if k.lower() not in ("host", "content-length", "transfer-encoding")
        }
        
        # Read request body if present
        body = await request.read() if request.body_exists else None
        
        async with session.request(
            method=request.method,
            url=backend_url,
            headers=headers,
            data=body,
            allow_redirects=False,
        ) as resp:
            # Create response
            response = web.StreamResponse(
                status=resp.status,
                headers={
                    k: v for k, v in resp.headers.items()
                    if k.lower() not in ("content-length", "transfer-encoding", "content-encoding")
                },
            )
            
            # Stream response body
            await response.prepare(request)
            async for chunk in resp.content.iter_any():
                await response.write(chunk)
            
            await response.write_eof()
            return response


async def proxy_sse(request: web.Request, backend_url: str, path_prefix: str) -> web.StreamResponse:
    """Handle SSE (Server-Sent Events) proxying with endpoint URL rewriting."""
    timeout = ClientTimeout(total=None)  # No timeout for SSE
    
    async with ClientSession(timeout=timeout) as session:
        headers = {
            k: v for k, v in request.headers.items()
            if k.lower() not in ("host", "content-length", "transfer-encoding")
        }
        
        async with session.get(backend_url, headers=headers) as resp:
            response = web.StreamResponse(
                status=resp.status,
                headers={
                    "Content-Type": "text/event-stream",
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
            
            await response.prepare(request)
            
            # Stream SSE with endpoint URL rewriting
            async for line in resp.content:
                rewritten_line = rewrite_sse_line(line, path_prefix)
                await response.write(rewritten_line)
            
            await response.write_eof()
            return response


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint for ALB."""
    return web.Response(text="OK", status=200)


def create_app() -> web.Application:
    """Create the proxy application."""
    app = web.Application()
    
    # Health check at root (for ALB)
    app.router.add_get("/", health_check)
    
    # Catch-all proxy
    app.router.add_route("*", "/{path:.*}", proxy_handler)
    
    return app


if __name__ == "__main__":
    print(f"[Proxy] Starting reverse proxy on port {PROXY_PORT}", flush=True)
    print(f"[Proxy] Forwarding to backend on port {BACKEND_PORT}", flush=True)
    
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=PROXY_PORT, print=None)
