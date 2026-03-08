from __future__ import annotations

import logging
from typing import Generator
from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are Codexa, an AI pair programmer that teaches by Socratic questioning. "
    "You must NOT give direct answers or solutions. "
    "Ask guiding questions or offer hints that lead the learner to discover the answer."
)


class SocraticEngine:
    def __init__(self):
        self._model = None
        try:
            from llama_cpp import Llama

            self._model = Llama(
                model_path=settings.llm_model_path,
                n_ctx=2048,
                n_threads=settings.llm_model_threads,
            )
        except Exception as exc:
            logger.warning("LLM not available, using stub: %s", exc)

    def generate(
        self,
        question: str,
        code_context: str,
        ast_context: dict,
        goal: str | None = None,
        guidance_level: int = 0,
    ) -> str:
        if not self._model:
            return self._heuristic_response(question, ast_context, goal, guidance_level)

        goal_line = f"Learning goal: {goal}\n" if goal else ""
        rules = (
            "Guidance levels:\n"
            "0 = ask a clarifying question (inputs/outputs/constraints)\n"
            "1 = high-level hint, no code\n"
            "2 = outline steps, no code\n"
            "3 = pseudocode, no code\n"
            "4 = tiny snippet (<=10 lines)\n"
            "5 = full solution only if explicitly requested\n"
        )
        prompt = (
            f"{SYSTEM_PROMPT}\n"
            f"{rules}\n"
            f"{goal_line}"
            f"Guidance level: {guidance_level}\n"
            f"User question: {question}\n"
            f"Code context: {code_context}\n"
            f"AST context: {ast_context}\n"
            "Respond with the guidance level behavior."
        )

        output = self._model(prompt, max_tokens=200, stop=["\n\n"])
        return output["choices"][0]["text"].strip()

    def _heuristic_response(
        self,
        question: str,
        ast_context: dict,
        goal: str | None = None,
        guidance_level: int = 0,
    ) -> str:
        question_lower = question.lower()
        functions = ast_context.get("functions", []) if isinstance(ast_context, dict) else []
        loops = ast_context.get("loops", []) if isinstance(ast_context, dict) else []
        conditions = ast_context.get("conditions", []) if isinstance(ast_context, dict) else []
        calls = ast_context.get("calls", []) if isinstance(ast_context, dict) else []
        dependencies = ast_context.get("dependencies", []) if isinstance(ast_context, dict) else []

        function_names = [fn.get("name") for fn in functions if fn.get("name")]
        focus_name = None
        for name in function_names:
            if name and name.lower() in question_lower:
                focus_name = name
                break
        if not focus_name and function_names:
            focus_name = function_names[0]

        def topic_hint() -> str:
            if "fibonacci" in question_lower:
                return "Think about how each Fibonacci term depends on the previous two values."
            if "factorial" in question_lower:
                return "Can you express the factorial of n in terms of factorial of n-1?"
            if "palindrome" in question_lower:
                return "Compare characters from both ends moving toward the center."
            if "sort" in question_lower:
                return "Which sorting strategy fits the constraints (time vs space)?"
            if "search" in question_lower:
                return "Is the data sorted? That changes whether binary search applies."
            return "Start by defining inputs, outputs, and the simplest example."

        if guidance_level <= 0:
            if goal:
                return f"What input and output would show you've achieved the goal: {goal}?"
            return "What input should your function accept, and what output should it produce?"
        if guidance_level == 1:
            return topic_hint()
        if guidance_level == 2:
            outline = [
                "1. Clarify inputs, outputs, and constraints.",
                "2. Choose a data structure or recurrence that fits.",
                "3. Step through a small example by hand.",
                "4. Implement and verify with edge cases.",
            ]
            return "Outline:\n" + "\n".join(outline)
        if guidance_level == 3:
            steps = [
                "Define variables/state for the current step.",
                "Loop/iterate while the stopping condition holds.",
                "Update state deterministically each step.",
                "Return or print the accumulated result.",
            ]
            return "Pseudocode steps:\n" + "\n".join(f"- {step}" for step in steps)
        if guidance_level == 4:
            if "fibonacci" in question_lower:
                return "Snippet:\nprev, curr = 0, 1\nfor _ in range(n):\n    prev, curr = curr, prev + curr\nprint(prev)"
            if focus_name:
                return f"Snippet:\n# inside {focus_name}\nfor item in items:\n    # update state\n    pass"
            return "Snippet:\nresult = []\nfor item in data:\n    # process item\n    pass\nprint(result)"
        # Level 5: full solution (generic)
        if "fibonacci" in question_lower:
            return (
                "Full solution:\n"
                "def fib(n):\n"
                "    a, b = 0, 1\n"
                "    for _ in range(n):\n"
                "        a, b = b, a + b\n"
                "    return a\n"
                "print(fib(n))"
            )
        if focus_name:
            return (
                "Full solution (template):\n"
                f"def {focus_name}(...):\n"
                "    # initialize state\n"
                "    # iterate over inputs\n"
                "    # return result\n"
                "    return result"
            )
        return "Full solution: define the function, iterate inputs, update state, return result."

    def generate_chat_fallback(self, question: str, code_context: str | None) -> str:
        """
        Local fallback for non-Socratic chat when Bedrock is unavailable.
        Keeps tone direct and helpful.
        """
        question_clean = (question or "").strip()
        if not question_clean:
            question_clean = "Help me understand this code."

        snippets: list[str] = [
            "Here is a direct step-by-step explanation.",
            f"Question: {question_clean}",
        ]

        if code_context and code_context.strip():
            code_preview = code_context.strip().splitlines()
            preview = "\n".join(code_preview[:12])
            snippets.append("Code context observed:")
            snippets.append(f"```\n{preview}\n```")
            snippets.append(
                "Quick approach:\n"
                "1. Identify inputs, outputs, and side effects.\n"
                "2. Walk line-by-line and track state changes.\n"
                "3. Validate edge cases and error paths."
            )
        else:
            snippets.append(
                "Quick approach:\n"
                "1. Define the exact goal and constraints.\n"
                "2. Break the problem into small functions.\n"
                "3. Validate with one simple and one edge-case input."
            )

        snippets.append(
            "If you share the exact function or error, I can give a tighter step-by-step breakdown."
        )
        return "\n\n".join(snippets)

    def stream_chat_fallback(
        self, question: str, code_context: str | None
    ) -> Generator[str, None, None]:
        """Streaming local fallback for chat endpoint."""
        response = self.generate_chat_fallback(question, code_context)
        for paragraph in response.split("\n\n"):
            text = paragraph.strip()
            if text:
                yield f"{text}\n\n"


engine = SocraticEngine()
