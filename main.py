import yaml
from llm_client import LLMClient
from mcp_discovery import discover_mcp_servers
import requests
import re


def load_config(path="config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def execute_mcp_action(server, action, params=None):
    """Execute an action on the MCP server and return the response"""
    try:
        if action == "list":
            response = requests.get(f"http://{server}:5000/list", params=params or {})
        elif action == "read":
            response = requests.get(f"http://{server}:5000/read", params=params or {})
        else:
            return f"Unknown action: {action}"
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return f"Error executing {action}: {str(e)}"

def parse_llm_request(llm_response):
    """Parse LLM response to extract MCP action and parameters"""
    llm_response_lower = llm_response.lower()
    
    # Check for list action
    if any(keyword in llm_response_lower for keyword in ["list", "show files", "show directory", "list files", "list directory"]):
        # Prioritize tool_code blocks first - these are the most reliable
        tool_code_patterns = [
            r'```tool_code\s*\n\s*list_files\s+([^\n]+)',
            r'```\s*\n\s*list_files\s+([^\n]+)',
        ]
        
        for pattern in tool_code_patterns:
            match = re.search(pattern, llm_response_lower)
            if match:
                path = match.group(1).strip()
                # Clean up the path
                path = re.sub(r'[^\w/~\-\.]', '', path)  # Keep only valid path characters
                if path and len(path) > 1:
                    return "list", {"path": path}
        
        # Only if no tool_code block found, look for natural language patterns
        # But be very strict about what constitutes a path
        natural_patterns = [
            r'list\s+files?\s+in\s+["\']?([/~][^"\'\n]*)["\']?',  # Must start with / or ~
            r'list\s+["\']?([/~][^"\'\n]*)["\']?',  # Must start with / or ~
            r'show\s+directory\s+["\']?([/~][^"\'\n]*)["\']?',  # Must start with / or ~
        ]
        
        for pattern in natural_patterns:
            match = re.search(pattern, llm_response_lower)
            if match:
                path = match.group(1).strip()
                # Clean up the path
                path = re.sub(r'[^\w/~\-\.]', '', path)  # Keep only valid path characters
                if path and len(path) > 1:
                    return "list", {"path": path}
        
        # Default to current directory if no specific path found
        return "list", {"path": "."}
    
    # Check for read action
    elif any(keyword in llm_response_lower for keyword in ["read", "open file", "show content", "display file"]):
        # Prioritize tool_code blocks first
        tool_code_patterns = [
            r'```tool_code\s*\n\s*read_file\s+([^\n]+)',
            r'```\s*\n\s*read_file\s+([^\n]+)',
        ]
        
        for pattern in tool_code_patterns:
            match = re.search(pattern, llm_response_lower)
            if match:
                filename = match.group(1).strip()
                # Clean up the filename
                filename = re.sub(r'[^\w/~\-\.]', '', filename)  # Keep only valid path characters
                if filename and len(filename) > 1:
                    return "read", {"path": filename}
        
        # Only if no tool_code block found, look for natural language patterns
        natural_patterns = [
            r'read\s+["\']?([/~][^"\'\n]*)["\']?',  # Must start with / or ~
            r'read\s+file\s+["\']?([/~][^"\'\n]*)["\']?',  # Must start with / or ~
        ]
        
        for pattern in natural_patterns:
            match = re.search(pattern, llm_response_lower)
            if match:
                filename = match.group(1).strip()
                # Clean up the filename
                filename = re.sub(r'[^\w/~\-\.]', '', filename)  # Keep only valid path characters
                if filename and len(filename) > 1:
                    return "read", {"path": filename}
    
    return None, None

def main():
    config = load_config()
    llm_provider = config.get("llm_provider", "ollama")
    llm_model = config.get("llm_model", "llama2")
    ollama_port = config.get("ollama_port", 11434)
    cloud_api_url = config.get("cloud_api_url", "")
    system_prompt = config.get("system_prompt", "You are a helpful assistant.")
    user_prompt = config.get("user_prompt", "List the files in the home directory.")

    # Discover MCP servers
    hosts = ["localhost", "raspberrypi.local"]  # Add more as needed
    servers = discover_mcp_servers(hosts)
    print("Discovered MCP servers:", servers)
    
    # Get detailed information about discovered services for learning
    discovered_services = []
    for server in servers:
        try:
            # Get comprehensive service discovery information
            discover_response = requests.get(f"http://{server}:5000/discover")
            print(f"Raw discover response from {server}: {discover_response.text}")
            
            if discover_response.status_code != 200:
                print(f"Error: /discover endpoint returned status {discover_response.status_code}")
                continue
                
            service_info = discover_response.json()
            print(f"Parsed service info: {service_info}")
            
            # Validate the response structure
            if 'server_info' not in service_info:
                print(f"Warning: /discover response missing 'server_info' key. Available keys: {list(service_info.keys())}")
                # Create a fallback structure
                service_info = {
                    'server_info': {
                        'name': 'MCPServerFilesystem',
                        'version': '1.0.0',
                        'description': 'A filesystem access MCP server'
                    },
                    'available_tools': [],
                    'capabilities': ['File system operations']
                }
            
            # Get sample data for context
            list_response = requests.get(f"http://{server}:5000/list", params={"path": "."})
            available_files = list_response.json().get("files", [])
            
            # Add sample data to service info
            service_info["sample_data"] = {
                "host": server,
                "available_files": available_files[:5]  # Show first 5 files for brevity
            }
            
            discovered_services.append(service_info)
            print(f"Service details - Host: {server}")
            print(f"  Name: {service_info['server_info']['name']}")
            print(f"  Description: {service_info['server_info']['description']}")
            print(f"  Available tools: {[tool['name'] for tool in service_info.get('available_tools', [])]}")
            print(f"  Sample files: {available_files[:5]}")
        except Exception as e:
            print(f"Error getting details for {server}: {e}")
            import traceback
            traceback.print_exc()

    # Initialize LLM client based on provider
    if llm_provider == "ollama":
        base_url = f"http://localhost:{ollama_port}"
        llm = LLMClient(provider="ollama", base_url=base_url)
    elif llm_provider == "cloud":
        if not cloud_api_url:
            print("Error: cloud_api_url must be specified in config.yaml for cloud provider")
            return
        llm = LLMClient(provider="cloud", base_url=cloud_api_url)
    else:
        print(f"Unknown LLM provider: {llm_provider}")
        return

    # Build initial enhanced prompt including discovered services
    services_context = ""
    if discovered_services:
        services_context = f"\n\nAvailable MCP Services:\n"
        for service in discovered_services:
            server_info = service.get('server_info', {})
            tools = service.get('available_tools', [])
            sample_data = service.get('sample_data', {})
            capabilities = service.get('capabilities', [])
            
            services_context += f"\n{server_info.get('name', 'Unknown')} at {sample_data.get('host', 'unknown')}:\n"
            services_context += f"  Description: {server_info.get('description', 'No description available')}\n"
            services_context += f"  Capabilities: {', '.join(capabilities)}\n"
            services_context += f"  Available tools:\n"
            
            for tool in tools:
                services_context += f"    - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}\n"
                services_context += f"      Endpoint: {tool.get('method', 'GET')} {tool.get('endpoint', '/unknown')}\n"
                services_context += f"      Parameters: {tool.get('parameters', {})}\n"
            
            services_context += f"  Sample files: {sample_data.get('available_files', [])}\n"
        
        services_context += f"\nIMPORTANT: When using tools, ONLY include the tool invocation with the exact path. Do NOT include explanations or thinking in the tool call.\n"
        services_context += f"\nTool Usage Examples:\n"
        services_context += f"- To list files: ```tool_code\nlist_files /path/to/directory\n```\n"
        services_context += f"- To read a file: ```tool_code\nread_file /path/to/file\n```\n"
        services_context += f"\nDo NOT include explanations like 'I will now list...' or 'Let me check...' in the tool invocation.\n"
        services_context += f"- Ask for more information or provide your final answer when done"
    else:
        services_context = "\n\nNo MCP services discovered."
    
    conversation_history = []
    max_iterations = 10
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n=== Iteration {iteration} ===")
        
        # Build the current prompt with conversation history
        if iteration == 1:
            current_prompt = f"{system_prompt}\n{user_prompt}{services_context}"
        else:
            # Include conversation history for context - make it more prominent
            history_text = "\n".join([f"Round {i+1}: {msg}" for i, msg in enumerate(conversation_history)])
            current_prompt = f"{system_prompt}\n{user_prompt}{services_context}\n\n=== CONVERSATION HISTORY ===\n{history_text}\n\n=== NEXT ACTION ===\nBased on the conversation history above, what would you like to do next? Consider the results of your previous actions."
        
        print(f"Current prompt length: {len(current_prompt)} characters")
        print(f"Conversation history entries: {len(conversation_history)}")
        
        # Get LLM response
        llm_response = llm.prompt(prompt_text=current_prompt, model=llm_model)
        print(f"LLM Response: {llm_response}")
        
        # Check if LLM is done
        if any(keyword in llm_response.lower() for keyword in ["final answer", "i'm done", "that's all", "complete"]):
            print("LLM indicates it's done. Final answer provided.")
            break
        
        # Parse LLM request for MCP action
        mcp_response = None
        if servers:
            action, params = parse_llm_request(llm_response)
            if action:
                print(f"Detected action: {action} with params: {params}")
                mcp_response = execute_mcp_action(servers[0], action, params)
                print(f"MCP Response ({action.upper()}): {mcp_response}")
        
        # Add to conversation history - include both LLM request and MCP response
        conversation_entry = f"LLM Request: {llm_response}"
        if mcp_response:
            conversation_entry += f"\nMCP Response: {mcp_response}"
        else:
            conversation_entry += f"\nMCP Response: No action taken"
        
        conversation_history.append(conversation_entry)
        print(f"Added to conversation history. Total entries: {len(conversation_history)}")
        
        # If no MCP action was taken, assume LLM is providing information
        if not mcp_response:
            print("No MCP action detected. LLM may be providing information or asking for clarification.")
    
    if iteration >= max_iterations:
        print(f"Reached maximum iterations ({max_iterations}). Stopping conversation.")

if __name__ == "__main__":
    main() 