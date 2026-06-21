import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from typing import TypedDict, Annotated, List
import operator
from tools import (
    speak,
    read_file,
    write_file,
    run_code,
    list_files,
    search_stackoverflow,
    git_commit
)

def speak(text):
    print(f"Agent: {text}")  # Just print instead of speak on server

load_dotenv()

# ── State ──────────────────────────────────────────────
class AgentState(TypedDict):
    filepath: str
    language: str
    original_code: str
    current_code: str
    errors: str
    fixed_code: str
    execution_result: dict
    loop_count: int
    messages: Annotated[List, operator.add]
    status: str

# ── LLM ────────────────────────────────────────────────
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

# ── Agent Nodes ─────────────────────────────────────────

def code_analyzer(state: AgentState) -> AgentState:
    """Agent 1: Reads and analyzes the code for errors"""
    speak("Starting code analysis. Let me read your file first.")

    result = read_file(state["filepath"])
    if "error" in result:
        speak(f"Could not read the file. Error: {result['error']}")
        return {**state, "status": "ERROR", "errors": result["error"]}

    code = result["code"]
    language = result["language"]

    speak(f"Analyzing your {language} code for errors.")

    response = llm.invoke([
        SystemMessage(content=f"""You are an expert {language} code analyzer.
Analyze the code and find ALL errors:
1. Syntax errors with line numbers
2. Logic errors
3. Runtime errors
4. Missing imports
5. Undefined variables
6. Type errors
Be specific and list every single issue."""),
        HumanMessage(content=f"Analyze this code:\n\n{code}")
    ])

    errors_found = response.content
    speak("I have completed my analysis. I found some issues. Now let me fix them.")

    return {
        **state,
        "language": language,
        "original_code": code,
        "current_code": code,
        "errors": errors_found,
        "status": "ANALYZED"
    }


def bug_fixer(state: AgentState) -> AgentState:
    """Agent 2: Fixes all errors found by analyzer"""
    speak(f"Fixing errors. This is attempt number {state['loop_count'] + 1}.")

    # Always define so_context first
    so_context = ""

    # Search StackOverflow only on retry attempts
    if state["loop_count"] > 0:
        so_results = search_stackoverflow(state["errors"])
        if so_results.get("solutions"):
            so_context = "\n\nStackOverflow solutions found:\n"
            for s in so_results["solutions"]:
                so_context += f"- {s['title']}\n"

    response = llm.invoke([
        SystemMessage(content=f"""You are an expert {state['language']} debugger.
You will receive buggy code and a list of errors.
Your job:
1. Fix EVERY single error
2. Keep the original logic intact
3. Add proper error handling
4. Return ONLY the complete fixed code
5. No explanations
6. No markdown code blocks
Just return the raw fixed code."""),
        HumanMessage(content=f"""
Original Code:
{state['current_code']}

Errors Found:
{state['errors']}
{so_context}

Return only the fixed code:""")
    ])

    fixed = response.content

    # Clean up any markdown if LLM added it
    if "```" in fixed:
        lines = fixed.split("\n")
        clean_lines = [l for l in lines if not l.startswith("```")]
        fixed = "\n".join(clean_lines)

    speak("I have fixed the errors. Now let me save and test the code.")
    write_file(state["filepath"], fixed)

    return {
        **state,
        "fixed_code": fixed,
        "current_code": fixed,
        "loop_count": state["loop_count"] + 1,
        "status": "FIXED"
    }


def code_executor(state: AgentState) -> AgentState:
    """Agent 3: Actually runs the code to verify the fix"""
    speak("Running the fixed code now to verify it works correctly.")

    result = run_code(state["filepath"], state["language"])

    if result["status"] == "PASSED":
        speak("Excellent! The code is working perfectly now. All errors have been fixed!")
        return {**state, "execution_result": result, "status": "PASSED"}
    else:
        speak("The code still has an issue. Let me analyze the error and fix it again.")
        return {
            **state,
            "execution_result": result,
            "errors": result.get("error", "Unknown error"),
            "status": "FAILED"
        }


def qa_checker(state: AgentState) -> AgentState:
    """Agent 4: Final quality check"""
    speak("Performing final quality check on the fixed code.")

    response = llm.invoke([
        SystemMessage(content=f"""You are a strict QA engineer for {state['language']} code.
Review the fixed code and check:
1. No remaining syntax errors
2. Logic is correct
3. Code follows best practices
4. No security issues

If everything is perfect respond with: APPROVED
If there are still issues respond with: ISSUES FOUND: [list them]"""),
        HumanMessage(content=f"Review this fixed code:\n\n{state['current_code']}")
    ])

    qa_result = response.content

    if "APPROVED" in qa_result:
        speak("Quality check passed! Your code is clean and ready to use.")
        return {**state, "status": "APPROVED"}
    else:
        speak("Quality check found some remaining issues. Let me fix those too.")
        return {**state, "errors": qa_result, "status": "FAILED"}


def test_generator(state: AgentState) -> AgentState:
    """Agent 5: Generates test cases for the fixed code"""
    speak("Generating test cases for your fixed code.")

    response = llm.invoke([
        SystemMessage(content=f"""You are an expert QA Engineer.
Given the fixed {state['language']} code, write test cases:

1. Unit test for every function
2. Edge cases (empty, null, wrong types)
3. Expected input and output for each test
4. At least 5 test cases minimum

Format exactly like this:

TEST CASES:
─────────────────
Test 1: [function name]
Input: [exact value]
Expected: [exact output]
Result: PASS

Keep it simple and specific."""),
        HumanMessage(content=f"Write test cases for:\n\n{state['current_code']}")
    ])

    test_cases = response.content
    speak("Test cases generated successfully!")

    # Save test cases to a file
    test_filepath = state["filepath"].replace(".", "_tests.")
    with open(test_filepath, "w", encoding="utf-8") as f:
        f.write(test_cases)

    print(f"\n📝 Test cases saved to: {test_filepath}")
    print("\n" + test_cases)

    # Auto commit to git
    git_commit(
        state["filepath"],
        state["errors"][:50] if state["errors"] else "Fixed bugs"
    )

    return {**state, "status": "TESTED"}


# ── Routing Functions ───────────────────────────────────

def should_retry(state: AgentState) -> str:
    if state["status"] == "PASSED":
        return "qa_check"
    elif state["loop_count"] >= 3:
        speak("I have made 3 attempts. Sending the best version I could produce.")
        return "force_finish"
    else:
        return "retry_fix"


def should_finish(state: AgentState) -> str:
    if state["status"] == "APPROVED":
        return "finish"
    elif state["loop_count"] >= 3:
        return "finish"
    else:
        return "retry_fix"


# ── Build the Graph ─────────────────────────────────────

def build_agent():
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("analyzer", code_analyzer)
    graph.add_node("fixer", bug_fixer)
    graph.add_node("executor", code_executor)
    graph.add_node("qa", qa_checker)
    graph.add_node("test_gen", test_generator)

    # Entry point
    graph.set_entry_point("analyzer")

    # Edges
    graph.add_edge("analyzer", "fixer")
    graph.add_edge("fixer", "executor")
    graph.add_edge("test_gen", END)

    # Conditional edges
    graph.add_conditional_edges(
        "executor",
        should_retry,
        {
            "qa_check": "qa",
            "retry_fix": "fixer",
            "force_finish": END
        }
    )

    graph.add_conditional_edges(
        "qa",
        should_finish,
        {
            "finish": "test_gen",
            "retry_fix": "fixer"
        }
    )

    return graph.compile()


# ── Main ────────────────────────────────────────────────

def debug_file(filepath: str):
    print("\n" + "="*50)
    print("🤖 AI CODE DEBUGGER AGENT")
    print("="*50)
    speak("Hello! I am your AI debugging agent. I will now analyze and fix your code automatically.")

    agent = build_agent()

    initial_state = {
        "filepath": filepath,
        "language": "",
        "original_code": "",
        "current_code": "",
        "errors": "",
        "fixed_code": "",
        "execution_result": {},
        "loop_count": 0,
        "messages": [],
        "status": "START"
    }

    final_state = agent.invoke(initial_state)

    print("\n" + "="*50)
    print("✅ DEBUGGING COMPLETE")
    print("="*50)
    print(f"Status: {final_state['status']}")
    print(f"Attempts: {final_state['loop_count']}")
    print(f"Fixed file: {filepath}")
    print(f"Backup: {filepath}.backup")

    if final_state.get("execution_result", {}).get("output"):
        print(f"\nProgram Output:\n{final_state['execution_result']['output']}")

    speak("Debugging complete! Your fixed code has been saved. The original is backed up.")


def debug_folder(folder: str):
    speak("I will now debug all code files in your folder.")
    result = list_files(folder)

    if "error" in result:
        speak(f"Could not read folder: {result['error']}")
        return

    files = result["files"]
    if not files:
        speak("No supported code files found in this folder.")
        return

    print(f"\nFound {len(files)} files to debug:")
    for f in files:
        print(f"  - {f}")

    for filepath in files:
        print(f"\n{'='*50}")
        print(f"Debugging: {filepath}")
        debug_file(filepath)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  Debug single file:  py agent.py path/to/file.py")
        print("  Debug folder:       py agent.py path/to/folder")
        speak("Please provide a file or folder path to debug.")
    else:
        path = sys.argv[1]
        if os.path.isdir(path):
            debug_folder(path)
        elif os.path.isfile(path):
            debug_file(path)
        else:
            speak(f"Path not found: {path}")
            print(f"Error: {path} not found")
