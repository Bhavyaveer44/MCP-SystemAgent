import asyncio
import json

import ollama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PARAMS = StdioServerParameters(
    command="python",
    args=["server.py"],
)

MODEL = "llama3.2:latest"

SYSTEM_PROMPT = (
    "You are a system automation agent. Call exactly one matching tool. "
    "create/write -> write_file. read ONE file -> read_file. read TWO OR "
    "MORE files -> read_files. list/show files -> list_dir with '.'. "
    "delete -> delete_file. Paths are bare filenames like 'notes.txt': no "
    "'workspace/', no leading '/', no '..'. Never invent paths or files "
    "the user did not name. After a tool returns, reply with one short "
    "sentence."
)


def mcp_tools_to_ollama_format(mcp_tools) -> list[dict]:
    """
    MCP tools and Ollama tools describe the same three things (name,
    description, parameter schema) but wrap them differently. This
    converts one shape into the other.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            },
        }
        for tool in mcp_tools
    ]


async def run_agent_loop(session: ClientSession):
    tools_response = await session.list_tools()
    ollama_tools = [
        t for t in mcp_tools_to_ollama_format(tools_response.tools)
        if t["function"]["name"] != "approved_run_command"
    ]

    print(f"Connected. {len(ollama_tools)} tools available: "
          f"{[t['function']['name'] for t in ollama_tools]}\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break

        if user_input.startswith("!"):
            cmd = user_input[1:].strip()
            result = await session.call_tool("run_command", {"raw_command": cmd})
            text = "".join(b.text for b in result.content if hasattr(b, "text"))
            if text.startswith("CONFIRMATION_REQUIRED:"):
                print(f"\n--- CONFIRMATION REQUIRED ---\nCommand: {cmd}")
                if input("Allow? [y/N]: ").strip().lower() == "y":
                    result = await session.call_tool(
                        "approved_run_command", {"raw_command": cmd}
                    )
                    text = "".join(b.text for b in result.content if hasattr(b, "text"))
                else:
                    text = "DENIED: user declined this command."
            print(f"{text}\n")
            continue

        low = user_input.lower()
        if low in ("ls", "list", "list files", "list all files in directory"):
            result = await session.call_tool("list_dir", {"relative_path": "."})
            print("".join(b.text for b in result.content if hasattr(b, "text")) + "\n")
            continue

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]

        # This inner loop handles the case where the model wants to call
        # MULTIPLE tools in sequence before giving a final text answer.

        last_tool_result = ""

        while True:
            response = ollama.chat(model=MODEL, messages=messages, tools=ollama_tools)
            msg = response["message"]
            messages.append(msg)

            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                text = (msg.get("content") or "").strip()
                print(f"Agent: {text or last_tool_result or '(no response)'}\n")
                break

            for call in tool_calls:
                name = call["function"]["name"]
                args = call["function"]["arguments"]
                if isinstance(args, str):
                    args = json.loads(args)

                print(f"  [calling tool] {name}({args})")
                result = await session.call_tool(name, args)
                result_text = "".join(
                    block.text for block in result.content if hasattr(block, "text")
                )

                if result_text.startswith("CONFIRMATION_REQUIRED:"):
                    cmd = args["raw_command"]
                    print(f"\n--- CONFIRMATION REQUIRED ---\nCommand: {cmd}")
                    if input("Allow? [y/N]: ").strip().lower() == "y":
                        result = await session.call_tool(
                            "approved_run_command", {"raw_command": cmd}
                        )
                        result_text = "".join(
                            b.text for b in result.content if hasattr(b, "text")
                        )
                    else:
                        result_text = "DENIED: user declined this command."

                print(f"  [tool result] {result_text[:200]}")
                last_tool_result = result_text


async def main():
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await run_agent_loop(session)


if __name__ == "__main__":
    asyncio.run(main())