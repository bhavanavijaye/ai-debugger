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

    results = []

    for file in request.files:
        filepath = file.get("path", "")
        content = file.get("content", "")

        print(f"Processing: {filepath}")

        temp_path = f"temp_{filepath.replace('/', '_')}"

        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(content)

        try:
            result = debug_file(temp_path)

            results.append({
                "file": filepath,
                "status": "fixed",
                "result": result
            })

        except Exception as e:

            results.append({
                "file": filepath,
                "status": "failed",
                "error": str(e)
            })

        if os.path.exists(temp_path):
            os.remove(temp_path)

    return {
        "status": "completed",
        "results": results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
