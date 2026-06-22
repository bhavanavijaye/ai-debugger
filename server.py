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

        print(f"📁 Processing: {filepath}")
        print(f"📦 Content length received: {len(content)} chars")

        try:
            decoded_content = base64.b64decode(content).decode("utf-8")
            print(f"✅ Decoded content length: {len(decoded_content)} chars")
            print(f"📄 First 100 chars: {decoded_content[:100]}")
        except Exception as e:
            decoded_content = content
            print(f"⚠️ Base64 decode failed: {e}, using raw content")

        temp_path = f"temp_{filepath.replace('/', '_')}"
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(decoded_content)

        print(f"💾 Wrote {len(decoded_content)} chars to {temp_path}")

        try:
            final_state = await loop.run_in_executor(
                executor, debug_file, temp_path
            )

            fixed_code = final_state.get("current_code", "")
            print(f"🤖 Agent status: {final_state.get('status')}")
            print(f"🔧 Fixed code length: {len(fixed_code)} chars")
            print(f"🔁 Loop count: {final_state.get('loop_count')}")

            results.append({
                "file": filepath,
                "status": final_state.get("status", "completed"),
                "fixed_code": fixed_code,
                "loop_count": final_state.get("loop_count", 0),
                "errors_found": final_state.get("errors", "")
            })

        except Exception as e:
            print(f"❌ Agent crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "file": filepath,
                "status": "failed",
                "fixed_code": "",
                "error": str(e)
            })

        if os.path.exists(temp_path):
            os.remove(temp_path)

    return {"status": "completed", "results": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
