# MCP System Automation Agent

A local agent that turns natural-language commands into file and shell operations. It uses **Model Context Protocol (MCP)** for tool exposure and **Ollama (mistral)** as the LLM. Every operation is confined to a jailed workspace directory, and shell commands go through an allowlist plus local user confirmation.

## How it works

```
┌──────────────┐   1. User query + tool schemas   ┌──────────────┐
│  host_app.py │ ───────────────────────────────► │ Ollama       │
│  (MCP client)│ ◄─────────────────────────────── │ (mistral)    │
└──────┬───────┘   2. Tool call (JSON)            └──────────────┘
       │ 3. MCP over stdio
┌──────▼───────┐
│  server.py   │  FastMCP server: registers tools
│  (MCP server)│
└──────┬───────┘
       │ 4. Validated execution
┌──────▼───────────────────────────┐
│ tools/file_ops.py  (path jail)   │
│ tools/shell_ops.py (allowlist +  │
│   confirmation) → workspace/     │
└──────────────────────────────────┘
```

1. `host_app.py` fetches tool schemas from the MCP server and passes them to Ollama.
2. Ollama returns a structured tool call.
3. The host dispatches it to `server.py` over MCP.
4. The tool runs inside `workspace/`, and the result goes back to the model.
5. The loop repeats until the model replies with plain text.

## Tools

| Tool | Description |
|---|---|
| `read_file` | Read a file in the workspace |
| `write_file` | Create or overwrite a file in the workspace |
| `list_dir` | List a workspace directory |
| `delete_file` | Delete a workspace file |
| `run_command` | Run an allowlisted shell command in the workspace |

## Security model

- **Path jail:** all paths are resolved with `Path.resolve()` and checked with `is_relative_to(WORKSPACE)`, so `../` traversal is rejected.
- **Allowlist:** `config/allowed_commands.yaml` defines permitted binaries, and a regex must fully match each one's arguments. Anything else is rejected, never sanitized.
- **No shell:** commands run via `subprocess.run([binary, *args])`, never `shell=True`, so `;`, `&&`, and `$()` are not interpreted.
- **Confirmation gate:** mutating commands (e.g. `git commit`, `git push`) print the exact command and wait for a `y/N` before running.
- **Execution limits:** commands run with `cwd=workspace/` and a 30s timeout.
- **Known gap:** file tools (`write_file`, `delete_file`) are path-jailed but not confirmation-gated.

## Setup

```bash
git clone https://github.com/Bhavyaveer44/mcp-system-agent.git
cd mcp-system-agent
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
ollama pull mistral
```

## Usage

Start Ollama if it isn't already running, then launch the agent:

```bash
ollama serve
python host_app.py
```

Example prompts:

```
You: list the files in the workspace
You: create notes.txt containing "hello agent"
You: run git status
```

Inspect and manually test the tools in the MCP inspector:

```bash
pip install "mcp[cli]"
mcp dev server.py
```

## Configuring the allowlist

Edit `config/allowed_commands.yaml`:

```yaml
commands:
  git:
    pattern: '^(status|log|diff|add|commit -m ".+"|push|pull|branch|checkout \S+)$'
    requires_confirmation: [commit, push, checkout]
```

Treat allowlist changes as security-relevant and commit them separately.

## Project structure

```
mcp-system-agent/
├── config/allowed_commands.yaml   # command allowlist
├── security/validator.py          # allowlist + regex validation
├── tools/file_ops.py              # path-jailed file operations
├── tools/shell_ops.py             # validated shell execution + confirmation
├── server.py                      # FastMCP server (stdio)
├── host_app.py                    # Ollama <-> MCP agent loop
├── workspace/                     # the only directory tools can touch
└── requirements.txt
```

## Roadmap

- [x] Path-jailed file operations
- [x] Command allowlist and validator
- [x] Confirmation gate for shell commands
- [x] MCP server (FastMCP, stdio)
- [x] Ollama host app with multi-step tool loop
- [ ] HTTP/SSE transport for remote clients
- [ ] Dockerfile and Render deployment
- [ ] API key auth on the HTTP endpoint (OAuth 2.1 as a later upgrade)
- [ ] Remote approval channel for mutating commands
- [ ] Additional tool categories (git/GitHub, APIs)

## Tech stack

Python · MCP SDK (FastMCP) · Ollama (mistral) · PyYAML