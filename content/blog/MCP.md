---
date: 2026-03-03
draft: false
title: "MCP (Model Context Protocol)"
categories: ["mcp"]
tags: ["mcp", "llm", "ai"]
author: "claude-4.6-opus"
---

## 0. Introduction

When ChatGPT appeared in late 2022, people were amazed that AI could converse like a human. However, limitations soon became apparent. Large Language Models (LLMs) were essentially just **text generation models**. They couldn't know the current weather, query a database, or send an email. They were brilliant but isolated entities, trapped within their training data.

This post covers the journey LLMs have taken to connect with the outside world: from the emergence of Function Calling, the explosion of AI Agents and the Tools ecosystem, to the final arrival of the **Model Context Protocol (MCP)**. Understanding this progression reveals that MCP is not just a new technology, but an inevitable conclusion.

## 1. Limitations of LLMs

When ChatGPT (based on GPT-3.5) was released in November 2022, the world was enthusiastic. Its ability to write code in natural language, compose essays, and explain complex concepts was remarkable. But it had its limits.

```text
User: "What's the weather in Seoul today?"
ChatGPT: "I'm sorry, I don't have access to real-time information. My training data only goes up until September 2021."
```

The limitations of LLMs were clear:

- **No access to real-time data**: They don't know information beyond their training point.
- **Inability to link with external systems**: They cannot call APIs, query databases, or read files.
- **Inability to perform actions**: They cannot do actual work like sending emails, registering schedules, or executing code.

No matter how smart an LLM was, it was just a **brain disconnected from the world**. Giving this model "hands and feet" is the trend that began in 2023.

## 2. The Emergence of Function Calling

### What is Function Calling?

On June 13, 2023, OpenAI added the **Function Calling** capability to the GPT-3.5 and GPT-4 APIs. This was a paradigm shift in how LLMs connect with external tools.
The core idea was simple: instead of the LLM executing a function directly, it requests in a structured format: "Please call this function with these arguments."

```text
[Step 1] Developer defines a list of available functions using JSON Schema and passes it to the API.

{
  "name": "get_weather",
  "description": "Get the current weather for a given city",
  "parameters": {
    "type": "object",
    "properties": {
      "city": { "type": "string", "description": "City name" }
    },
    "required": ["city"]
  }
}

[Step 2] User says, "Tell me the weather in Seoul."
        The LLM analyzes the conversation context and decides on the appropriate function call.

[Step 3] LLM responds with structured JSON.
{
  "function_call": {
    "name": "get_weather",
    "arguments": "{\"city\": \"Seoul\"}"
  }
}

[Step 4] The application executes the actual function and passes the result back to the LLM.

[Step 5] The LLM converts the function result into natural language and responds to the user.
        → "The current temperature in Seoul is 15°C, and it's sunny."
```

The LLM only acts as the **decision-maker**, while the application handles the actual execution. This:

- Reduced security risks of LLMs directly accessing external systems.
- Allowed developers to have full control over the execution logic.
- Significantly reduced parsing errors with structured JSON output.

### Limitations

However, Function Calling also had clear limitations:

- **Platform dependency**: It was a format defined specifically for the OpenAI API. Anthropic Claude, Google Gemini, and others used different formats.
- **Static definition**: The list of functions had to be hard-coded in advance. Tools couldn't be discovered dynamically at runtime.
- **Redundancy of execution logic**: To use the same functionality (e.g., querying GitHub issues) in 10 different AI apps, it had to be implemented 10 separate times.

## 3. The Era of AI Agents - Tools and Skills

### Explosion of the Agent Paradigm

As Function Calling suggested a way to connect tools to LLMs, a bigger dream sprouted: **AI Agents** — autonomous systems where the LLM makes plans, uses tools, and achieves goals on its own.
In 2023, projects like `AutoGPT` and `BabyAGI` emerged, showing the potential of AI Agents. The vision was for an LLM to perform complex tasks step-by-step, such as "Search for flights, book a hotel, and register it on my calendar."

### Tools: The Agent's Toolbox

In Agent frameworks, **Tools** are a core concept. They refer to **any unit of functionality** an Agent uses to interact with the outside world.
LangChain popularized this pattern:

```python
from langchain.tools import Tool

search_tool = Tool(
    name="web_search",
    description="Searches the internet for the latest information",
    func=search_function
)

calculator_tool = Tool(
    name="calculator", 
    description="Performs mathematical calculations",
    func=calculate_function
)

# Pass the tool list to the Agent
agent = initialize_agent(
    tools=[search_tool, calculator_tool],
    llm=llm,
    agent_type="zero-shot-react-description"
)
```

The essence of a Tool is the same as Function Calling—an **abstraction of an external function that an LLM can call**. However, as frameworks like LangChain wrapped these in standardized **interfaces**, it became easy to combine various tools.

### Skills: A More Modular Approach

While Tools are at the level of individual functions, **Skills** are a higher level of abstraction. Skills bundle domain knowledge and tool usage capabilities into **reusable packages**.
For example, a "GitHub Management" skill might include:

- A set of tools for calling the GitHub API.
- Prompt guides to follow during PR reviews.
- Domain knowledge about code conventions.

The advantage of the Skills pattern was **Progressive Disclosure**. Instead of loading all tools at once, an Agent could activate appropriate skills when needed, using the context window efficiently.

### The N×M Integration Problem

By 2024, the ecosystem grew **explosively** yet was **severely fragmented**.
**LLM Providers**:

- OpenAI (GPT-4, GPT-4 Turbo)
- Anthropic (Claude 2, Claude 3)
- Google (Gemini)
- Meta (LLaMA)
- Dozens of open-source models

**AI Applications**:

- Cursor, GitHub Copilot (Coding tools)
- ChatGPT, Claude.ai (Conversational AI)
- Hundreds of AI agent frameworks

**External Services**:

- GitHub, Slack, Jira, Google Drive, Notion, DBs, Cloud services...

The problem was that there was **no standard** to connect them.

```
              AI App A        AI App B        AI App C
           (Uses OpenAI)   (Uses Claude)   (Uses Gemini)
                ↕               ↕               ↕  
GitHub ─ [Custom Code A] ─ [Custom Code B] ─ [Custom Code C]
Slack  ─ [Custom Code D] ─ [Custom Code E] ─ [Custom Code F]
Jira   ─ [Custom Code G] ─ [Custom Code H] ─ [Custom Code I]
```

To connect N AI apps with M external services, **N×M custom integrations** were required. Every time a new AI app emerged or a new service was added, the integration code grew exponentially.
This was unsustainable. It was like the era **before USB, where every device used a different connector**.

## 4. The Birth of MCP

### What is MCP?

On November 25, 2024, Anthropic open-sourced the **Model Context Protocol (MCP)**. MCP is an **open standard protocol** for two-way connection between LLM applications and external data sources and tools.

### Why was MCP needed?

Looking back at the N×M problem, let's compare before and after MCP:

**Before MCP (N×M Integrations):**

```
AI App A ──[Custom]──→ GitHub
AI App A ──[Custom]──→ Slack  
AI App A ──[Custom]──→ DB

AI App B ──[Custom]──→ GitHub
AI App B ──[Custom]──→ Slack
AI App B ──[Custom]──→ DB

→ 6 custom integrations needed (2 apps × 3 services)
```

**After MCP (N+M Integrations):**

```
AI App A ──[MCP]──┐
                  ├──→ GitHub MCP Server
AI App B ──[MCP]──┤    Slack MCP Server
                  └──→ DB MCP Server

→ Only 5 implementations needed (2 MCP clients + 3 MCP servers)
```

An AI app only needs to implement an MCP client to connect to **all MCP servers**. An external service only needs to implement an MCP server once to be usable by **all AI apps**. N×M reduces to N+M.

### Inspired by the Language Server Protocol

The design of MCP was directly inspired by Microsoft's **LSP (Language Server Protocol)**.
Before LSP, each IDE (VS Code, IntelliJ, Vim...) had to implement separate autocomplete/linting/formatting logic for each programming language (Python, Go, TypeScript...). With the advent of LSP, implementing one Language Server per language made it usable in all IDEs.
MCP applies this same approach to AI tool integration.

## 5. How MCP Works

### Architecture: Host → Client → Server

MCP consists of three core components.

**Host**

- The LLM application itself. This could be Cursor IDE, Claude Desktop, or a user-created AI app.
- Creates and manages multiple MCP Clients.
- Applies security policies and manages user approvals.

**Client**

- Runs inside the Host and connects **1:1 with one Server**.
- Performs capability negotiation.
- Relays messages bidirectionally between the Host and the Server.

**Server**

- A lightweight process that exposes the functionality of an external service via the MCP protocol.
- Each server operates independently and is unaware of other servers.
- Ensures security through server isolation.

### Three Things Servers Provide — Tools, Resources, and Prompts

An MCP server can expose three types of functionality:

#### 1. Tools

**Executable functions** that an LLM can call. An evolution of Function Calling.

```json
{
  "name": "create_github_issue",
  "description": "Creates a new issue in a GitHub repository",
  "inputSchema": {
    "type": "object",
    "properties": {
      "repo": { "type": "string", "description": "Format: owner/repo" },
      "title": { "type": "string" },
      "body": { "type": "string" }
    },
    "required": ["repo", "title"]
  }
}
```

Difference from traditional Function Calling: The **definition and execution logic of the Tool exist together on the server**. The client simply requests the server: "Execute this tool with these arguments."

#### 2. Resources

**Data provided as context** to the LLM. Read-only.

```json
{
  "uri": "github://repos/myorg/myrepo/issues/42",
  "name": "Issue #42",
  "mimeType": "application/json"
}
```

Provides information the LLM can refer to, such as file contents, database records, or API responses. If a Tool is an "Action," a Resource is "Knowledge."

#### 3. Prompts

Predefined **prompt templates and workflows**.

```json
{
  "name": "code_review",
  "description": "Prompt template for performing code reviews",
  "arguments": [
    { "name": "diff", "description": "Code diff to review", "required": true }
  ]
}
```

Servers provide prompts optimized for specific tasks, guiding the LLM to perform work in a consistent manner.

### What MCP Standardizes and What It Doesn't — Two Communication Segments

There is a common misunderstanding when it comes to MCP. In an MCP system, there are **two different communication segments**, and MCP only standardizes one of them.

```text
   Area Unrelated to MCP               Area Standardized by MCP
◄─────────────────────►    ◄──────────────────────────────►

┌───────┐  Vendor-specific   ┌──────┐     JSON-RPC 2.0     ┌──────────┐
│  LLM  │ ═══════════════ │ Host │ ═══════════════════ │MCP Server│
│       │  (REST API)     │      │  (MCP Protocol)       │          │
└───────┘                 └──────┘                     └──────────┘
                              ▲
                              │
                        Host Translates
```

**Segment ① Host ↔ LLM (Vendor-specific, unrelated to MCP)**
This is the segment where the Host sends the "list of available tools" and "user messages" to the LLM. This follows **each LLM vendor's REST API format**, not JSON-RPC.

When the LLM determines a tool call is needed, it also responds in a vendor-specific format. Even for the same content, the format varies by vendor.
How does the LLM generate this JSON? The LLM has been trained/fine-tuned to "generate" this format. **MCP is not involved in this segment at all.**

**Segment ② MCP Client ↔ MCP Server (JSON-RPC 2.0, MCP Standard)**
When the LLM responds with "Please call this tool," the Host parses that vendor-specific format, **translates it into the MCP standard format (JSON-RPC 2.0)**, and delivers it to the Server via the MCP Client.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "create_github_issue",
    "arguments": {
      "repo": "myorg/myrepo",
      "title": "Bug fix needed",
      "body": "Error occurring on the login page"
    }
  }
}
```

When the server returns the execution result, it is also in JSON-RPC format:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "Issue #143 has been successfully created."
    }]
  }
}
```

In summary, **the Host acts as a translator in the middle**. It converts the LLM's vendor-specific format to the MCP format and passes the MCP result back to the LLM in the vendor format.
MCP standardizes the "AI App ↔ External Tool" segment, not the "AI App ↔ LLM" segment. To use an analogy, MCP **unified the connector on the tool side to USB-C**, while the connector on the LLM side still uses each vendor's own method. That's why once you create a GitHub MCP server, it works exactly the same in Cursor or Claude Desktop, regardless of which LLM you use. Each Host just needs to implement the part that translates its LLM's tool calling format to the MCP format.

### LLM Tool Calling Can Fail

A natural question follows. If the LLM learned what format to use for tool calling through training, **couldn't it respond in the wrong format?**
Correct. An LLM is ultimately a model that predicts the next token. A tool calling response is also the result of the LLM generating tokens like `{`, `"`, `n`, `a`, `m`, `e`, ... one by one. Thus, various errors can occur:

- **JSON Syntax Error**: Missing matching brackets in complex nested structures.
- **Non-existent Tool Name**: Hallucinating a similar but different name like `make_github_issue` instead of `create_github_issue`.
- **Wrong Parameters**: Using a field like `repository` when it was defined as `repo` in the schema, or omitting required fields.
- **Type Mismatch**: Generating a string when the value should be an array.

Modern LLMs are trained to generate valid JSON through fine-tuning, and some cases apply **Constrained Decoding**, like OpenAI's Structured Outputs. Constrained Decoding limits the probability distribution during token generation so that only tokens matching the JSON syntax are selected. Thanks to these techniques, JSON syntax errors themselves rarely occur in models like GPT-4 or Claude. However, **"syntactically correct but semantically wrong"** cases (wrong tool names, wrong parameters) still happen.

To mitigate this, the Host verifies if the tool name actually exists, validates if parameters match the schema, and checks for missing required fields.
Therefore, LLM tool calling cannot be 100% trusted. This is why MCP design principles specify that the Host **must obtain explicit user consent for every tool call**. In practice, annotations like `readOnlyHint` or `destructiveHint` are used to apply automatic approval policies based on risk level, but the basic principle remains user approval for all tools. This is the same reason Cursor asks for approval before executing a terminal command.

### Transport Layer

MCP defines two standard transport methods:

**1. stdio (Standard I/O)**

```
Host Process ──stdin/stdout──→ Server Process (Child Process)
```

- The Host runs the MCP server as a **child process**.
- JSON-RPC messages are exchanged via stdin/stdout.
- Suitable for local tools (file systems, local DBs, etc.).

**2. Streamable HTTP**

```
Client ──HTTP POST/GET──→ Remote Server 
  ←── SSE (Server-Sent Events) ──
```

- The server is operated as an independent HTTP service.
- Requests are sent via POST, and streaming responses can be received via SSE.
- Suitable for remote services (Cloud APIs, SaaS, etc.).

## 6. Conclusion

MCP is not a revolutionary new technology. It took the proven concept of Function Calling, applied the proven architecture pattern of LSP, and built it on top of the proven protocol of JSON-RPC. **Presenting the right abstraction at the right time** — that is why MCP has quickly become an industry standard.

LLMs are no longer isolated geniuses. Through the standard link called MCP, AI is finally becoming an **intelligence connected to the world**.

---

_This post was written based on information as of March 2026._
