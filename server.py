from fastapi import FastAPI
from pydantic import BaseModel
import os
import subprocess
import tempfile
from tools import speak
from agent import debug_file

app = FastAPI()

class CodeRequest(BaseModel):
    files: list
    developer_answers: str
    repo_name: str

@app.post("/debug")
async def debug_project(request: CodeRequest):
    print("REQUEST RECEIVED")

    return {
        "status": "completed",
        "message": "test successful"
    }
    
    results = []
    
    for file in request.files:
        filepath = file.get("path", "")
        content = file.get("content", "")
        
        # Save file temporarily
        temp_path = f"temp_{filepath.replace('/', '_')}"
        with open(temp_path, "w") as f:
            f.write(content)
        
        # Debug it
        result = debug_file(temp_path)
        results.append({
            "file": filepath,
            "status": "fixed",
            "result": result
        })
        
        # Cleanup
        os.remove(temp_path)
    
    return {
        "status": "completed",
        "results": results,
        "message": "All files debugged successfully!"
    }

@app.get("/health")
async def health():
    return {"status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
