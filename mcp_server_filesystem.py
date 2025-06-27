from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
import os
import uvicorn
from pathlib import Path

app = FastAPI()

def validate_path(path_str: str) -> Path:
    """Validate and normalize a path for security and functionality"""
    try:
        # Expand tilde (~) to home directory path
        expanded_path = os.path.expanduser(path_str)
        
        # Convert to Path object and resolve to absolute path
        path = Path(expanded_path).resolve()
        
        # Security check: ensure the path exists and is accessible
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Path does not exist: {path_str} (resolved to: {path})")
        
        return path
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid path '{path_str}': {str(e)}")

@app.get("/discover")
def discover_services():
    """Return comprehensive information about available MCP services and tools"""
    return {
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
                        "required": False,
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
                        "required": True,
                        "examples": ["/etc/passwd", "./config.txt", "~/file.txt"]
                    }
                },
                "response_format": {
                    "content": "File contents as string",
                    "file_path": "Absolute path of the file that was read",
                    "file_size": "Size of the file in bytes",
                    "error": "Error message if operation fails"
                },
                "example_request": "GET /read?path=~/config.txt",
                "example_response": {
                    "content": "This is the content of the file...",
                    "file_path": "/home/user/config.txt",
                    "file_size": 1234
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

@app.get("/list")
def list_files(path: str = Query(".", description="Directory path to list files from")):
    try:
        # Validate and resolve the path
        dir_path = validate_path(path)
        
        # Ensure it's a directory
        if not dir_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")
        
        # List files and directories
        items = []
        for item in dir_path.iterdir():
            # Add trailing slash for directories to distinguish them
            item_name = item.name + "/" if item.is_dir() else item.name
            items.append(item_name)
        
        return {
            "files": sorted(items),
            "current_path": str(dir_path),
            "total_items": len(items)
        }
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"error": f"Error listing directory '{path}': {str(e)}"}
        )

@app.get("/read")
def read_file(path: str = Query(..., description="File path to read")):
    try:
        # Validate and resolve the path
        file_path = validate_path(path)
        
        # Ensure it's a file
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail=f"Path is not a file: {path}")
        
        # Check file size for safety (limit to 1MB)
        file_size = file_path.stat().st_size
        if file_size > 1024 * 1024:  # 1MB limit
            raise HTTPException(status_code=413, detail=f"File too large ({file_size} bytes). Maximum size is 1MB.")
        
        # Read file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {
            "content": content,
            "file_path": str(file_path),
            "file_size": file_size
        }
    except HTTPException:
        raise
    except UnicodeDecodeError:
        return JSONResponse(
            status_code=400, 
            content={"error": f"File '{path}' is not a text file or contains invalid encoding"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"error": f"Error reading file '{path}': {str(e)}"}
        )

@app.get("/type")
def server_type():
    return {"type": "MCPServerFilesystem"}

@app.get("/pwd")
def get_current_working_directory():
    """Get the current working directory of the MCP server"""
    return {"current_directory": str(Path.cwd())}

def run_server(host: str = "0.0.0.0", port: int = 5000):
    uvicorn.run("mcp_server_filesystem:app", host=host, port=port, reload=False) 