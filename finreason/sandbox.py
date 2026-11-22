"""Run model-written Python code safely: static checks, a separate process, restricted builtins, a timeout."""
import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field

ALLOWED_MODULES = {"math"}
FORBIDDEN_NAMES = {
    "open", "exec", "eval", "compile", "__import__", "input", "globals", "locals", "vars",
    "getattr", "setattr", "delattr", "exit", "quit", "help", "breakpoint", "memoryview", "dir",
    "os", "sys", "subprocess", "shutil", "socket",
}

# This program runs in the child process. It reads the user code from stdin, executes it with
# a small whitelist of builtins, and prints the variable `ans` plus all numeric variables as JSON.
CHILD_PROGRAM = r'''
import json, math, sys
def safe_import(name, *args, **kwargs):
    if name != "math":
        raise ImportError("only the math module may be imported")
    return math
SAFE = {name: getattr(__builtins__, name) for name in (
    "abs", "min", "max", "round", "sum", "len", "range", "float", "int", "str", "bool", "list",
    "dict", "tuple", "set", "enumerate", "zip", "sorted", "reversed", "pow", "divmod", "any", "all",
    "map", "filter", "isinstance", "ValueError", "ZeroDivisionError", "Exception")}
SAFE["__import__"] = safe_import
SAFE["print"] = lambda *a, **k: None
env = {"__builtins__": SAFE, "math": math}
exec(sys.stdin.read(), env)
trace = {k: v for k, v in env.items()
         if not k.startswith("__") and isinstance(v, (int, float, bool)) and not isinstance(v, type)}
sys.stdout.write(json.dumps({"ans": env.get("ans"), "trace": trace}, default=str))
'''


@dataclass
class SandboxResult:
    ok: bool
    ans: object = None
    trace: dict = field(default_factory=dict)
    error: str = ""


def extract_code(text):
    """Take the first ```python ... ``` block from model output (or the whole text if none)."""
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL)
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text, flags=re.DOTALL)
    return (blocks[0] if blocks else text).strip()


def check_code(code):
    """Reject code that imports modules other than math, touches dunder attributes or calls
    dangerous builtins. Returns an error message, or None if the code looks safe."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return f"SyntaxError: {exc.msg} (line {exc.lineno})"
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            bad = [a.name for a in node.names if a.name not in ALLOWED_MODULES]
            if bad:
                return f"import of {bad} is not allowed"
        elif isinstance(node, ast.ImportFrom):
            if node.module not in ALLOWED_MODULES:
                return f"import from {node.module} is not allowed"
        elif isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            return f"access to attribute {node.attr} is not allowed"
        elif isinstance(node, ast.Name) and (node.id in FORBIDDEN_NAMES or node.id.startswith("__")):
            return f"use of name {node.id} is not allowed"
    return None


def _limit_resources(seconds):
    def apply():
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (seconds, seconds))
    return apply


def run_code(code, timeout=5):
    """Execute code in a fresh, isolated Python process and return the value of `ans`."""
    problem = check_code(code)
    if problem:
        return SandboxResult(ok=False, error=problem)
    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-c", CHILD_PROGRAM], input=code, capture_output=True,
            text=True, timeout=timeout, preexec_fn=_limit_resources(timeout),
        )
    except subprocess.TimeoutExpired:
        return SandboxResult(ok=False, error=f"timed out after {timeout}s")
    if proc.returncode != 0:
        last_line = (proc.stderr.strip().splitlines() or ["unknown error"])[-1]
        return SandboxResult(ok=False, error=last_line)
    result = json.loads(proc.stdout)
    if result["ans"] is None:
        return SandboxResult(ok=False, trace=result["trace"], error="the code did not set `ans`")
    return SandboxResult(ok=True, ans=result["ans"], trace=result["trace"])
