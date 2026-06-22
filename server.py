from fastapi import FastAPI
from pydantic import BaseModel
import os
import base64
from concurrent.futures import ThreadPoolExecutor
import asyncio
from agent import debug_file

app = FastAPI()
executor = ThreadPoolExecutor(max_workers=2)

class CodeRequest(BaseModel):
    files: list
    developer_answers: str = ""
    repo_name: str = ""

@app.get("/")
def health():
    return {"status": "AI Debugger running"}

@app.post("/debug")
async def debug_project(request: CodeRequest):
    results = []
    loop = asyncio.get_event_loop()

    for file in request.files:
        filepath = file.get("path", "")
        content = file.get("content", "")

        print(f"Processing: {filepath}")

        # ✅ Fix 1: decode base64 content from GitHub
        try:
            decoded_content = base64.b64decode(content).decode("utf-8")
        except Exception:
            decoded_content = content  # fallback if already plain text

        temp_path = f"temp_{filepath.replace('/', '_')}"
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(decoded_content)

        try:
            final_state = await loop.run_in_executor(
                executor, debug_file, temp_path
            )

            # ✅ Fix 2: extract fixed_code from agent state
            fixed_code = final_state.get("current_code", "")

            results.append({
                "file": filepath,
                "status": final_state.get("status", "completed"),
                "fixed_code": fixed_code,          # ← n8n reads this
                "loop_count": final_state.get("loop_count", 0),
                "errors_found": final_state.get("errors", "")
            })

        except Exception as e:
            results.append({
                "file": filepath,
                "status": "failed",
                "fixed_code": "",
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
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
