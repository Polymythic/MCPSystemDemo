# MCPSystemDemo

A basic demo project showing how to orchestrate an LLM (via Ollama) and a filesystem MCP server (FastAPI) in Python.

## Project Structure

```
MCPSystemDemo/
  ├── llm_client.py         # Handles communication with Ollama LLM
  ├── mcp_server_filesystem.py # Filesystem-access server (MCP, FastAPI)
  ├── mcp_discovery.py      # Discovery mechanism for MCP servers
  ├── main.py               # Demo entry point
  └── pyproject.toml        # Project metadata and dependencies
```

## Setup

1. Install [uv](https://github.com/astral-sh/uv):
   ```bash
   # macOS/Linux (with Homebrew)
   brew install astral-sh/uv/uv
   # or with pipx
   pipx install uv
   # or see https://github.com/astral-sh/uv for other methods
   ```

2. Install dependencies with uv:
   ```bash
   uv pip install -r pyproject.toml
   ```

3. Start the MCP server (on your RPI5 or local machine):
   ```bash
   uvicorn mcp_server_filesystem:app --host 0.0.0.0 --port 5000
   ```

4. Ensure Ollama is running and accessible (default: `http://localhost:11434`).

## Running the Demo

```bash
uv python main.py
```

- Discovers available MCP servers.
- Prompts the LLM via Ollama.
- Shows invocation/response passing between the MCP server and the LLM.

## Customization
- Add more hosts to the `hosts` list in `main.py` for broader MCP server discovery.
- Adjust the LLM prompt as needed.

# Summary
This is a foundational demo to show how and LLM running locally can interact with services that are discovered via MCP Servers

# Overview of steps

