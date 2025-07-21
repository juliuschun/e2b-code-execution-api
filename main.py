"""
E2B Code Execution API - Clean Version
FastAPI service that executes Python code in E2B sandboxes using default template only
"""

import os
import time
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from e2b_code_interpreter import Sandbox
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="E2B Code Execution API - Clean",
    description="Execute Python code safely in E2B sandboxes (default template only)",
    version="2.0.0"
)

class CodeRequest(BaseModel):
    code: str
    timeout: Optional[int] = 30

class CodeResponse(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: Optional[float] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "e2b-api-clean"}

@app.post("/execute", response_model=CodeResponse)
def execute_code(request: CodeRequest):
    """Execute Python code in E2B sandbox using default template"""
    
    e2b_api_key = os.getenv("E2B_API_KEY")
    if not e2b_api_key:
        raise HTTPException(status_code=500, detail="E2B_API_KEY not configured")
    
    start_time = time.time()
    
    try:
        # Always use default template - no custom template dependency
        with Sandbox() as sandbox:
            # Step 1: Silently install UV if needed
            setup_code = """
import subprocess
import sys

try:
    subprocess.run(["uv", "--version"], check=True, capture_output=True)
except (subprocess.CalledProcessError, FileNotFoundError):
    subprocess.run([sys.executable, "-m", "pip", "install", "uv"], 
                   capture_output=True, text=True)
"""
            sandbox.run_code(setup_code)
            
            # Step 2: Check if code contains UV inline dependencies
            if "# /// script" in request.code and "# dependencies" in request.code:
                # Use uv run for scripts with inline dependencies
                script_content = request.code
                
                # Write script to temporary file
                write_script = f"""
with open('/tmp/script.py', 'w') as f:
    f.write('''{script_content}''')
"""
                sandbox.run_code(write_script)
                
                # Execute with uv run
                result = sandbox.run_code("import subprocess; result = subprocess.run(['uv', 'run', '/tmp/script.py'], capture_output=True, text=True); print(result.stdout); print(result.stderr)")
            else:
                # Execute code directly for simple scripts
                result = sandbox.run_code(request.code)
        
        execution_time = time.time() - start_time
        
        # Process results - handle both stdout string and list formats
        output_parts = []
        
        # Handle stdout
        if hasattr(result.logs, 'stdout') and result.logs.stdout:
            if isinstance(result.logs.stdout, list):
                output_parts.extend(result.logs.stdout)
            else:
                output_parts.append(result.logs.stdout)
        
        # Handle stderr  
        if hasattr(result.logs, 'stderr') and result.logs.stderr:
            stderr_lines = result.logs.stderr if isinstance(result.logs.stderr, list) else [result.logs.stderr]
            output_parts.extend([f"STDERR: {line}" for line in stderr_lines])
        
        # Also check for text output directly on result
        if hasattr(result, 'text') and result.text:
            output_parts.append(result.text)
            
        output = "\\n".join(output_parts) if output_parts else "No output generated"
        
        return CodeResponse(
            success=True,
            output=output,
            execution_time=execution_time
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        return CodeResponse(
            success=False,
            output="",
            error=f"Execution failed: {str(e)}",
            execution_time=execution_time
        )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "E2B Code Execution API - Clean Version",
        "version": "2.0.0", 
        "template": "default only",
        "changes": [
            "Auto UV installation"
        ],
        "endpoints": {
            "/health": "Health check",
            "/execute": "Execute Python code (POST)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
