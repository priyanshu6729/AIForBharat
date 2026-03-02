from __future__ import annotations

import resource
import subprocess
import time


def _set_limits():
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    memory_bytes = 256 * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))


def _complexity_hint(code: str) -> str:
    loops = code.count("for ") + code.count("while ")
    if "def " in code and "return" in code and "(" in code:
        return "Potential recursion detected; consider call depth."
    if loops >= 2:
        return "Nested loops suggest O(n^2) behavior."
    if loops == 1:
        return "Single loop suggests O(n) behavior."
    return "No obvious loops detected; likely O(1) or O(n) based on hidden operations."


def run_code(language: str, code: str) -> dict:
    start = time.time()
    if language == "python":
        cmd = ["python3", "-c", code]
    elif language == "javascript":
        cmd = ["node", "-e", code]
    else:
        raise ValueError("Unsupported language")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5,
            preexec_fn=_set_limits,
        )
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired:
        stdout = ""
        stderr = "Execution timed out"

    duration = time.time() - start
    return {
        "stdout": stdout,
        "stderr": stderr,
        "execution_time": duration,
        "complexity_hint": _complexity_hint(code),
    }
