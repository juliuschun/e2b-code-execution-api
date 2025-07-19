"""
E2B Code Execution API
FastAPI service that executes Python code in E2B sandboxes
"""

import os
import time
import json
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from e2b_code_interpreter import Sandbox
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="E2B Code Execution API",
    description="Execute Python code safely in E2B sandboxes",
    version="1.0.0"
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
    return {"status": "healthy", "service": "e2b-code-execution-api"}

@app.post("/execute", response_model=CodeResponse)
def execute_code(request: CodeRequest):
    """Execute Python code in E2B sandbox with fallback mechanism"""
    
    e2b_api_key = os.getenv("E2B_API_KEY")
    if not e2b_api_key:
        raise HTTPException(status_code=500, detail="E2B_API_KEY not configured")
    
    template_id = os.getenv("E2B_TEMPLATE_ID", "genapi")
    
    start_time = time.time()
    
    # Try custom template first, fallback to default
    templates_to_try = [
        ("lnmzb0eecin3qojbvl9j", "custom template with uv"),
        ("genapi", "custom template by name"), 
        (None, "default template")
    ]
    
    for template, description in templates_to_try:
        try:
            if template:
                with Sandbox(template=template) as sandbox:
                    # Custom template should have uv pre-installed
                    result = sandbox.run_code(request.code)
            else:
                with Sandbox() as sandbox:
                    # Install uv in default template if needed
                    enhanced_code = f"""
# Check if uv is available, install if not
import subprocess
import sys

try:
    subprocess.run(["uv", "--version"], check=True, capture_output=True)
    print("✅ uv is available")
    uv_available = True
except (subprocess.CalledProcessError, FileNotFoundError):
    print("📦 Installing uv...")
    subprocess.run([sys.executable, "-m", "pip", "install", "uv"], check=True)
    print("✅ uv installed successfully")
    uv_available = True

# Execute user code
{request.code}
"""
                    result = sandbox.run_code(enhanced_code)
            
            execution_time = time.time() - start_time
            
            # Process results
            output_lines = []
            if result.logs.stdout:
                output_lines.extend(result.logs.stdout)
            if result.logs.stderr:
                output_lines.extend([f"STDERR: {line}" for line in result.logs.stderr])
            
            output = "\n".join(output_lines) if output_lines else "Code executed successfully (no output)"
            
            # Add template info to output
            template_info = f" (using {description})" if template else " (using default template with uv)"
            
            return CodeResponse(
                success=True,
                output=output + template_info,
                execution_time=execution_time
            )
            
        except Exception as e:
            # If this is not the last template, continue to next
            if template != templates_to_try[-1][0]:
                continue
            # If this is the last template, return error
            execution_time = time.time() - start_time
            return CodeResponse(
                success=False,
                output="",
                error=f"All templates failed. Last error: {str(e)}",
                execution_time=execution_time
            )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "E2B Code Execution API",
        "endpoints": {
            "/health": "Health check",
            "/execute": "Execute Python code (POST)",
            "/docs": "API documentation"
        },
        "template": os.getenv("E2B_TEMPLATE_ID", "genapi")
    }

# ASGI application for App Engine
from fastapi.middleware.wsgi import WSGIMiddleware

# Create WSGI wrapper for App Engine compatibility
def create_app():
    return app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)