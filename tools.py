import subprocess
import os
import sys
try:
    import pyttsx3
    engine = pyttsx3.init()
    HAS_VOICE = True
except:
    HAS_VOICE = False
    engine = None
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)

def speak(text):
    print(f"\n🔊 Agent: {text}")
    if HAS_VOICE and engine:
        engine.say(text)
        engine.runAndWait()

def read_file(filepath: str) -> dict:
    """Read code from a file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        ext = os.path.splitext(filepath)[1]
        language = {
            '.py': 'python',
            '.js': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.ts': 'typescript',
            '.go': 'go',
            '.rb': 'ruby',
        }.get(ext, 'unknown')
        speak(f"I have read the {language} file. Let me analyze it now.")
        return {"code": content, "language": language, "filepath": filepath}
    except Exception as e:
        return {"error": str(e)}

def write_file(filepath: str, content: str) -> dict:
    """Write fixed code back to file"""
    try:
        # Save original as backup
        backup_path = filepath + ".backup"
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                original = f.read()
            with open(backup_path, 'w') as f:
                f.write(original)

        with open(filepath, 'w') as f:
            f.write(content)
        speak("I have written the fixed code to the file.")
        return {"success": True, "backup": backup_path}
    except Exception as e:
        return {"error": str(e)}

def run_code(filepath: str, language: str) -> dict:
    """Actually execute the code and return result"""
    speak(f"Now I am running the {language} code to check if it works.")
    
    commands = {
        'python': [sys.executable, filepath],
        'javascript': ['node', filepath],
        'java': ['java', filepath],
        'cpp': ['g++', filepath, '-o', 'temp_output', '&&', './temp_output'],
        'c': ['gcc', filepath, '-o', 'temp_output', '&&', './temp_output'],
        'ruby': ['ruby', filepath],
        'go': ['go', 'run', filepath],
    }

    cmd = commands.get(language)
    if not cmd:
        return {"error": f"Language {language} not supported for execution"}

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            speak("The code ran successfully! No errors found.")
            return {
                "status": "PASSED",
                "output": result.stdout,
                "error": None
            }
        else:
            speak(f"The code failed. I found an error. Let me fix it.")
            return {
                "status": "FAILED",
                "output": result.stdout,
                "error": result.stderr
            }
    except subprocess.TimeoutExpired:
        return {"status": "FAILED", "error": "Code execution timed out after 30 seconds"}
    except FileNotFoundError:
        return {"status": "FAILED", "error": f"{language} runtime not found. Please install it."}
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}

def list_files(folder: str) -> dict:
    """List all code files in a folder"""
    supported = ['.py', '.js', '.java', '.cpp', '.c', '.ts', '.go', '.rb']
    try:
        files = []
        for f in os.listdir(folder):
            if any(f.endswith(ext) for ext in supported):
                files.append(os.path.join(folder, f))
        speak(f"I found {len(files)} code files in the folder.")
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}
def install_package(package_name: str) -> dict:
    """Automatically installs missing packages"""
    speak(f"Installing missing package: {package_name}")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            speak(f"Successfully installed {package_name}")
            return {"success": True, "package": package_name}
        else:
            speak(f"Could not install {package_name}")
            return {"success": False, "error": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}
def search_stackoverflow(error: str) -> dict:
    """Search StackOverflow for error solutions"""
    speak("Searching StackOverflow for a solution to this error.")
    try:
        import requests
        url = "https://api.stackexchange.com/2.3/search/advanced"
        params = {
            "order": "desc",
            "sort": "relevance",
            "q": error[:150],
            "site": "stackoverflow",
            "filter": "withbody",
            "pagesize": 3
        }
        res = requests.get(url, params=params)
        data = res.json()
        
        solutions = []
        for item in data.get("items", [])[:3]:
            solutions.append({
                "title": item["title"],
                "link": item["link"],
                "score": item["score"]
            })
        
        if solutions:
            speak(f"Found {len(solutions)} possible solutions on StackOverflow.")
        else:
            speak("No solutions found on StackOverflow.")
            
        return {"solutions": solutions}
    except Exception as e:
        return {"error": str(e), "solutions": []}
def git_commit(filepath: str, error_summary: str) -> dict:
    """Auto commit fixed code to git"""
    speak("Committing the fixed code to git repository.")
    try:
        # Initialize git if not already
        subprocess.run(
            ["git", "init"],
            capture_output=True,
            cwd=os.path.dirname(filepath)
        )

        # Add the fixed file
        subprocess.run(
            ["git", "add", filepath],
            capture_output=True
        )

        # Commit with descriptive message
        commit_message = f"AI Auto-Fix: Fixed {os.path.basename(filepath)} - {error_summary[:50]}"
        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            speak("Successfully committed fixed code to git!")
            return {"success": True, "message": commit_message}
        else:
            speak("Could not commit to git. Make sure git is installed.")
            return {"success": False, "error": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}
