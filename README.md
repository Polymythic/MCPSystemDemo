# MCPSystemDemo: MCP-Based LLM Agent Teaching Project

A comprehensive demonstration and teaching resource for building Model Context Protocol (MCP) based LLM agents. This project showcases the fundamental concepts of how LLMs can interact with external services through MCP servers, enabling them to perform real-world tasks like filesystem operations.

## 🎯 Project Overview

This demo illustrates the core principles of MCP-based LLM agents by implementing a filesystem exploration agent that can:
- Discover available MCP services automatically
- Execute filesystem operations through MCP servers
- Maintain conversation context and learn from previous interactions
- Handle both Ollama (local) and cloud LLM providers
- Demonstrate proper tool invocation and response handling
- This project was done in Cursor (Pro) using the Agent tool

## Quick Learnings from the Human In The Loop (Me)
- Generative Code using AI is not magic (well, not ALL magic).
- Having good knowledge is important because there will be debugging, and smells that you can suggest in the bugs that are raised
- Some basic errors in the initial generation: The code did not even try to use the MCP Server, the MCP server had no discovery service, it lacked the conversational feedback loop, it was only using relative paths to the filesystem
- Even in this simple example, there are MULTIPLE places to debug: System Prompt, User Prompts, AND each element of the system (had to curl the MCP server a lot to test)
- I see some examples of the model doing "When confused or in doubt, overfit a solution by using lots of regexp".  That smells like solving a specific exmample, rather than attacking a higher issue with, perhaps, a library that solves that class of problem
- There is a lot of code generated, and you WILL need to debug
- Death Spiral Scrap temptation.  When the Gen AI is fixing code, it seems to often "solve by adding".  As you iterate to find the issues, add more and more, there is a temptation to say "oh god.  Lets just scrap and start over."

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   LLM Client    │    │   MCP Discovery  │    │  MCP Server     │
│                 │    │                  │    │                 │
│ • Ollama API    │◄──►│ • Service Scan   │◄──►│ • FastAPI       │
│ • Cloud APIs    │    │ • Health Checks  │    │ • Filesystem    │
│ • Prompt Mgmt   │    │ • Type Detection │    │ • Path Validation│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Conversation Loop                            │
│                                                                 │
│ 1. LLM receives prompt + available services                    │
│ 2. LLM generates tool invocation                               │
│ 3. System parses and executes MCP action                       │
│ 4. MCP response fed back to LLM                                │
│ 5. LLM continues with updated context                          │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 System Components

### 1. **LLM Client** (`llm_client.py`)
Handles communication with LLM providers:
- **Ollama Integration**: Local LLM with streaming response support
- **Cloud Provider Support**: Extensible for OpenAI, Anthropic, etc.
- **Provider Abstraction**: Unified interface for different LLM backends
- **Response Parsing**: Handles different response formats

```python
# Example: Using Ollama
llm = LLMClient(provider="ollama", base_url="http://localhost:11434")
response = llm.prompt("List files in /home", model="gemma3:latest")
```

### 2. **MCP Server** (`mcp_server_filesystem.py`)
FastAPI-based filesystem access server:
- **Service Discovery**: `/discover` endpoint for tool documentation
- **Filesystem Operations**: List directories, read files
- **Path Validation**: Security and error handling
- **Home Directory Support**: Tilde expansion and absolute paths

```python
# Example endpoints
GET /discover    # Service capabilities and tool documentation
GET /list?path=/home/user    # List directory contents
GET /read?path=/etc/hosts    # Read file contents
```

### 3. **MCP Discovery** (`mcp_discovery.py`)
Automatically discovers available MCP services:
- **Network Scanning**: Checks multiple hosts for MCP servers
- **Health Validation**: Ensures services are responsive
- **Type Detection**: Identifies server capabilities

### 4. **Main Orchestrator** (`main.py`)
Coordinates the entire system:
- **Configuration Management**: YAML-based settings
- **Conversation Loop**: Multi-turn LLM interactions
- **Tool Parsing**: Extracts LLM tool invocations
- **Context Management**: Maintains conversation history

## 📡 Service Discovery Example

The MCP server provides comprehensive service documentation through its `/discover` endpoint:

```json
{
  "server_info": {
    "name": "MCPServerFilesystem",
    "version": "1.0.0",
    "description": "A filesystem access MCP server providing file and directory operations with full filesystem access"
  },
  "available_tools": [
    {
      "name": "list_files",
      "description": "List files and directories in a specified path (supports absolute and relative paths)",
      "endpoint": "/list",
      "method": "GET",
      "parameters": {
        "path": {
          "type": "string",
          "description": "Directory path to list files from (absolute or relative)",
          "default": ".",
          "required": false,
          "examples": ["/home/user", "/etc", ".", "~/Documents", "~"]
        }
      },
      "response_format": {
        "files": "List of file and directory names",
        "current_path": "Absolute path of the directory being listed",
        "error": "Error message if operation fails"
      },
      "example_request": "GET /list?path=~",
      "example_response": {
        "files": ["Documents/", "Downloads/", "Desktop/"],
        "current_path": "/home/user"
      }
    },
    {
      "name": "read_file",
      "description": "Read the contents of a specified file (supports absolute and relative paths)",
      "endpoint": "/read",
      "method": "GET",
      "parameters": {
        "path": {
          "type": "string",
          "description": "File path to read (absolute or relative)",
          "required": true,
          "examples": ["/etc/passwd", "./config.txt", "~/file.txt"]
        }
      },
      "response_format": {
        "content": "File contents as string",
        "file_path": "Absolute path of the file that was read",
        "file_size": "Size of the file in bytes"
      }
    }
  ],
  "capabilities": [
    "Full filesystem navigation",
    "Absolute and relative path support",
    "Home directory expansion (~)",
    "File content reading",
    "Directory listing",
    "Path validation and security",
    "Error handling and reporting"
  ]
}
```

## 🔄 Conversation Flow

The system implements a sophisticated conversation loop:

1. **Initial Prompt**: LLM receives task + available services
2. **Tool Invocation**: LLM generates tool_code block
3. **Action Execution**: System parses and calls MCP server
4. **Response Integration**: MCP response added to conversation history
5. **Context Update**: LLM receives updated context for next iteration
6. **Iteration**: Process continues until task completion

### Example Conversation:
```
LLM: "I need to find duplicate files in the home directory"

System: [Discovers MCP services, provides tool documentation]

LLM: ```tool_code
list_files /Users/stevestruebing
```

MCP: {"files": ["Documents/", "Downloads/", "Desktop/"], "current_path": "/Users/stevestruebing"}

LLM: "I can see the directories. Let me check Documents for duplicates."

LLM: ```tool_code
list_files /Users/stevestruebing/Documents
```

MCP: {"files": ["file1.txt", "file2.txt", "duplicate.txt"], "current_path": "/Users/stevestruebing/Documents"}
```

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- [uv](https://github.com/astral-sh/uv) package manager
- [Ollama](https://ollama.ai/) (for local LLM)

### Installation

1. **Install uv**:
   ```bash
   # macOS/Linux (with Homebrew)
   brew install astral-sh/uv/uv
   # or with pipx
   pipx install uv
   ```

2. **Install dependencies**:
   ```bash
   uv pip install -r pyproject.toml
   ```

3. **Start Ollama**:
   ```bash
   ollama serve
   ```

4. **Pull a model**:
   ```bash
   ollama pull gemma3:latest
   ```

### Running the Demo

1. **Start the MCP server**:
   ```bash
   uvicorn mcp_server_filesystem:app --host 0.0.0.0 --port 5000
   ```

2. **Run the main demo**:
   ```bash
   uv python main.py
   ```

## ⚙️ Configuration

The system is configured via `config.yaml`:

```yaml
llm_model: gemma3:latest
llm_provider: ollama  # options: ollama, cloud
ollama_port: 11434
cloud_api_url: ""  # for cloud providers
system_prompt: "You are a filesystem agent with access to MCP tools..."
user_prompt: "List the files in ~ directory and identify duplicates"
```

## 🎓 Learning Objectives

This project demonstrates key MCP concepts:

### **1. Service Discovery**
- How MCP servers advertise their capabilities
- Dynamic tool documentation and parameter specifications
- Health checking and service availability

### **2. Tool Invocation**
- Proper tool_code block formatting
- Parameter extraction and validation
- Error handling and response processing

### **3. Conversation Management**
- Maintaining context across multiple interactions
- Learning from previous actions and responses
- Iterative problem-solving with LLM agents

### **4. Security Considerations**
- Path validation and sanitization
- File size limits and access controls
- Error handling without information leakage

### **5. Extensibility**
- Adding new MCP servers
- Supporting different LLM providers
- Implementing custom tools and capabilities

## 🔍 Key Features

- **Full Filesystem Access**: Absolute and relative paths, home directory expansion
- **Multi-Provider LLM Support**: Ollama and cloud providers
- **Conversational Memory**: Context preservation across interactions
- **Tool Documentation**: Comprehensive service discovery
- **Error Handling**: Robust error management and recovery
- **Security**: Path validation and access controls
- **Extensibility**: Easy to add new MCP servers and tools

## 🤝 Contributing

This is a teaching project designed to demonstrate MCP concepts. Contributions that improve clarity, add examples, or enhance educational value are welcome!

## 📚 Further Reading

- [Model Context Protocol (MCP) Documentation](https://modelcontextprotocol.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Ollama Documentation](https://ollama.ai/docs)
- [uv Package Manager](https://github.com/astral-sh/uv)

---

**Note**: This project is designed for educational purposes and demonstrates MCP concepts. For production use, additional security, error handling, and scalability considerations should be implemented.

# Summary
This is a foundational demo to show how and LLM running locally can interact with services that are discovered via MCP Servers

# Overview of steps

