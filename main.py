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
    """Execute Python code in E2B sandbox"""
    
    e2b_api_key = os.getenv("E2B_API_KEY")
    if not e2b_api_key:
        raise HTTPException(status_code=500, detail="E2B_API_KEY not configured")
    
    template_id = os.getenv("E2B_TEMPLATE_ID", "genapi")
    
    sandbox = None
    start_time = time.time()
    
    try:
        # Create sandbox with context manager (no template - use default)
        with Sandbox() as sandbox:
            # Execute code
            result = sandbox.run_code(request.code)
            
            execution_time = time.time() - start_time
            
            # Process results
            output_lines = []
            if result.logs.stdout:
                output_lines.extend(result.logs.stdout)
            if result.logs.stderr:
                output_lines.extend([f"STDERR: {line}" for line in result.logs.stderr])
            
            output = "\n".join(output_lines) if output_lines else "Code executed successfully (no output)"
            
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
            error=str(e),
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