import os

# File paths
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.json')
COVERAGERC_CONTENT = """
[run]
source = {project_name}
omit =
    */__init__.py
    tests/*
    **/test_*.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug:
    if __name__ == .__main__.:
    raise NotImplementedError
    pass
    except ImportError:
    def main
"""

# Regex patterns
FILE_CONTENT_PATTERN = r"<<<(.+?)>>>\n(.*?)<<<end>>>"
PYLINT_SCORE_PATTERN = r"Your code has been rated at (\d+\.\d+)/10"
COMPLEXIPY_SCORE_PATTERN = r"🧠 Total Cognitive Complexity in\s*{escaped_path}:\s*(\d+)"
COVERAGE_PATTERN = r"TOTAL\s+\d+\s+\d+\s+(\d+)%"

# Command lists
AUTOPEP8_CMD = ["uv", "run", "autopep8", "--in-place", "--aggressive"]
PYLINT_CMD = [
    "uv", "run", "pylint",
    "--disable=missing-function-docstring,missing-module-docstring",
    "--max-line-length=120"
]
COMPLEXIPY_CMD = ["uv", "run", "complexipy"]
PYTEST_CMD = [
    "uv", "run", "pytest",
    "--cov-config=.coveragerc",
    "--cov-report=term-missing",
    "-vv"
]

# Prompts
IMPROVEMENT_PROMPT = """
The current pylint score for {file_path} is {current_pylint_score:.2f}/10.
The current complexipy score is {current_complexipy_score}.
Please analyze the pylint output and suggest improvements to the code implementation only.
Focus on reducing cognitive complexity while maintaining or improving the pylint score.
Do not modify the test file.

Pylint output:
{pylint_output}

Complexipy output:
{complexipy_output}

Original task: {task}

Provide specific code changes to improve the score and address any issues.
Follow these rules strictly:
1. Only modify the code implementation files
2. Do not change the tests file
3. Focus on improving code quality, readability, and adherence to PEP8
4. Address any warnings or errors reported by pylint
5. Ensure the implementation correctly handles edge cases and potential errors
6. CRITICAL: Use the following code block format for specifying file content:
        <<<main.py>>>
        # File content here
        <<<end>>>
7. CRITICAL: Do not explain the task only implement the required functionality in the code blocks.
Working directory: {working_dir}
"""

TEST_IMPROVEMENT_PROMPT = """
The current test file needs minor improvements. Please analyze the test output and suggest small, specific changes to fix any issues in the test file.
Do not modify the main implementation file, only suggest minimal improvements to the tests but write out the full test file content.

Test output:
{test_output}

Original task: {task}

Provide specific, minimal code changes to improve the test file, addressing only the failing tests or obvious issues.
Follow these rules strictly:
1. CRITICAL: Only suggest changes to the test file (tests/test_main.py)
2. Do not change the code file in main.py
3. Focus on fixing failing tests or obvious errors
4. Do not rewrite entire test functions unless absolutely necessary
5. CRITICAL: Use the following code block format for specifying file content:
    For test files, use:
    <<<tests/test_main.py>>>
    # Test file content here
    <<<end>>>
6. CRITICAL: Do not explain the task only implement the required functionality in the code blocks.
7. IMPORTANT: Only use pytest fixtures for Flask and FastAPI servers.
8. IMPORTANT: Always pytest parameterize tests for different cases.
9. CRITICAL: Always use `import main` to import the main.py file in the test file.
10. IMPORTANT: Only mock external services or APIs in tests.
Working directory: {working_dir}
"""

VALIDATION_PROMPT = """
Review the proposed improvements: {proposed_improvements} and confirm if it correctly addresses the original task: {task}
If the implementation is correct or mostly correct, respond with 'VALID'.
If the implementation is completely unrelated or fundamentally flawed, respond with 'INVALID'.
Do not provide any additional information or explanations.
"""