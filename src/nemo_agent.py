import os
import json
import random
import logging
import re
import subprocess
from typing import Tuple
from ollama_api import OllamaAPI
from file_utils import robust_write_file, extract_file_contents, validate_file_content
from code_quality import check_code_quality
from constants import (
    CONFIG_PATH, COVERAGERC_CONTENT, PYTEST_CMD, COVERAGE_PATTERN,
    IMPROVEMENT_PROMPT, TEST_IMPROVEMENT_PROMPT, VALIDATION_PROMPT
)


class NemoAgent:
    def __init__(self, task: str):
        self.task = task
        self.config = self.load_config()
        self.setup_logging()
        self.project_name = self.generate_project_name()
        self.pwd = os.path.join(os.getcwd(), self.project_name)
        self.llm = self.setup_llm()
        self.previous_suggestions = set()

    def load_config(self):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        self.logger = logging.getLogger(__name__)

    def generate_project_name(self):
        return f"project_{random.randint(100, 999)}"

    def setup_llm(self):
        return OllamaAPI(self.config['default_model'], self.config['ollama_api_url'])

    def run_task(self):
        self.logger.info(f"Current working directory: {os.getcwd()}")
        self.ensure_uv_installed()
        self.create_project_with_uv()
        self.implement_solution()

        pylint_score, complexipy_score, pylint_output, complexipy_output = check_code_quality("main.py", self.pwd)

        code_check_attempts = 1
        while code_check_attempts < self.config['max_improvement_attempts']:
            if pylint_score < self.config['pylint_threshold'] and complexipy_score > self.config[
                'complexipy_threshold']:
                self.improve_code("main.py", pylint_score, complexipy_score, pylint_output, complexipy_output)
                pylint_score, complexipy_score, pylint_output, complexipy_output = check_code_quality("main.py",
                                                                                                      self.pwd)
            else:
                break
            code_check_attempts += 1

        test_check_attempts = 1
        while test_check_attempts < self.config['max_improvement_attempts']:
            tests_passed, coverage, test_output = self.run_tests()
            if not tests_passed or coverage < self.config['coverage_threshold']:
                self.improve_test_file(test_output)
                tests_passed, coverage, test_output = self.run_tests()
            else:
                break
            test_check_attempts += 1

        self.logger.info("Task completed. Please review the output and make any necessary manual adjustments.")

    def ensure_uv_installed(self):
        try:
            subprocess.run(["uv", "--version"], check=True, capture_output=True, text=True)
            self.logger.info("uv is already installed.")
        except FileNotFoundError:
            self.logger.info("uv is not installed. Installing uv...")
            try:
                subprocess.run("pip install uv", shell=True, check=True)
                self.logger.info("uv installed successfully.")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Error installing uv: {e}")
                raise

    def create_project_with_uv(self):
        self.logger.info(f"Creating new uv project: {self.project_name}")
        try:
            subprocess.run(["uv", "init", self.project_name, "--no-workspace"], capture_output=True, text=True,
                           check=True)
            subprocess.run(["uv", "add", "pytest", "pylint", "autopep8", "pytest-cov", "complexipy"], check=True,
                           cwd=self.pwd)

            tests_dir = os.path.join(self.pwd, "tests")
            os.makedirs(tests_dir, exist_ok=True)
            os.remove(os.path.join(self.pwd, "hello.py"))

            with open(os.path.join(tests_dir, '__init__.py'), 'w') as f:
                f.write("# This file is required to make Python treat the directory as containing packages.\n")

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error creating uv project: {e.stderr}")
            raise
        except Exception as e:
            self.logger.error(f"Error: {str(e)}")
            raise

    def implement_solution(self, max_attempts=3):
        prompt = f"""
        Create a comprehensive implementation for the task: {self.task}.
        You must follow these rules strictly:
            1. IMPORTANT: Never use pass statements in your code or tests. Always provide a meaningful implementation.
            2. CRITICAL: Use the following code block format for specifying file content:                
                For code files, use:
                <<<main.py>>>
                # File content here
                <<<end>>>

                For test files, use:
                <<<tests/test_main.py>>>
                # Test file content here
                <<<end>>>
            3. IMPORTANT: Do not add any code comments to the files.
            4. IMPORTANT: Always follow PEP8 style guide, follow best practices for Python, use snake_case naming, and provide meaningful docstrings.
            5. IMPORTANT: Do not redefine built-in functions or use reserved keywords as variable names.
            6. CRITICAL: Create any non-existent directories or files as needed that are not Python files.
            7. CRITICAL: Your response should ONLY contain the code blocks and `uv add package_names` command at the end after all the code blocks. Do not include any explanations or additional text.
            8. IMPORTANT: Do not modify the existing uv dependencies. Only add new ones if necessary.
            9. CRITICAL: Only create 1 file for the python code: main.py
            10. CRITICAL: Only create 1 file for the python tests: tests/test_main.py
            11. CRITICAL: Create a main method to run the app in main.py and if a web app run the app on port 8080.
            12. IMPORTANT: Only use pytest fixtures for Flask and FastAPI servers.
            13. IMPORTANT: Always pytest parameterize tests for different cases.
            14. CRITICAL: Always use `import main` to import the main.py file in the test file.
            15. IMPORTANT: Only mock external services or APIs in tests.
        Working directory: {self.pwd}
        """

        for attempt in range(max_attempts):
            self.logger.info(f"Attempt {attempt + 1} to implement solution")
            solution = self.llm.generate(prompt)
            self.logger.info(f"Received solution:\n{solution}")

            uv_commands = [line.strip() for line in solution.split("\n") if
                           line.strip().strip('.').startswith("uv add")]
            for command in uv_commands:
                try:
                    subprocess.run(command, shell=True, check=True, cwd=self.pwd)
                    self.logger.info(f"Executed command: {command}")
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"Failed to execute command: {command}. Error: {str(e)}")

            success = self.process_file_changes(solution)

            if success:
                self.logger.info("All files created successfully and passed pylint check")
                return True

            self.logger.warning(f"Attempt {attempt + 1} failed to create the correct files or pass pylint. Retrying...")

        self.logger.error("Failed to implement solution after maximum attempts")
        return False

    def process_file_changes(self, proposed_changes):
        file_contents = extract_file_contents(proposed_changes)
        success = True

        for file_path, content in file_contents.items():
            full_path = os.path.join(self.pwd, file_path)
            try:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                content = validate_file_content(full_path, content)

                if content is not None:
                    if robust_write_file(full_path, content, self.config['max_write_attempts'],
                                         self.config['write_retry_delay']):
                        self.logger.info(f"File written successfully: {full_path}")
                    else:
                        self.logger.error(f"Failed to write file: {full_path}")
                        success = False
                else:
                    self.logger.error(f"Invalid content for file: {full_path}")
                    success = False

            except Exception as e:
                self.logger.error(f"Error writing file {full_path}: {str(e)}")
                success = False

        return success

    def improve_code(self, file_path, current_pylint_score, current_complexipy_score, pylint_output, complexipy_output):
        prompt = IMPROVEMENT_PROMPT.format(
            file_path=file_path,
            current_pylint_score=current_pylint_score,
            current_complexipy_score=current_complexipy_score,
            pylint_output=pylint_output,
            complexipy_output=complexipy_output,
            task=self.task,
            working_dir=self.pwd
        )

        proposed_improvements = self.llm.generate(prompt)

        if proposed_improvements in self.previous_suggestions:
            self.logger.info("No new improvements suggested. Moving on.")
            return current_pylint_score, current_complexipy_score

        self.previous_suggestions.add(proposed_improvements)

        if self.validate_implementation(proposed_improvements):
            self.logger.info("Executing validated improvements:")
            self.process_file_changes(proposed_improvements)

    def improve_test_file(self, test_output):
        prompt = TEST_IMPROVEMENT_PROMPT.format(
            test_output=test_output,
            task=self.task,
            working_dir=self.pwd
        )
        proposed_improvements = self.llm.generate(prompt)

        if self.validate_implementation(proposed_improvements):
            self.logger.info("Executing validated test improvements:")
            success = self.process_file_changes(proposed_improvements)
            if success:
                self.logger.info("Test improvements have been applied. Please review the changes manually.")
            else:
                self.logger.warning("Failed to apply some or all test improvements.")
        else:
            self.logger.warning("Proposed test improvements do not align with the original task. No changes were made.")

    def validate_implementation(self, proposed_improvements):
        prompt = VALIDATION_PROMPT.format(
            proposed_improvements=proposed_improvements,
            task=self.task
        )
        response = self.llm.generate(prompt)

        if "VALID" in response.upper():
            self.logger.info("Implementation validated successfully.")
            return True
        else:
            self.logger.warning("Implementation does not match the original task.")
            return False

    def run_tests(self):
        self.logger.info("Running tests and checking code quality...")
        try:
            with open(os.path.join(self.pwd, ".coveragerc"), "w") as f:
                f.write(COVERAGERC_CONTENT.format(project_name=self.project_name))

            result = subprocess.run(
                PYTEST_CMD + [f"--cov={self.pwd}"],
                capture_output=True,
                text=True,
                cwd=self.pwd,
            )
            test_output = result.stdout + result.stderr
            self.logger.info("Pytest output:\n%s", test_output)

            if "No data to report." in test_output:
                self.logger.warning("No coverage data was collected. Ensure that the tests are running correctly.")
                return False, 0, test_output

            coverage_match = re.search(COVERAGE_PATTERN, test_output)
            coverage_percentage = int(coverage_match.group(1)) if coverage_match else 0

            tests_passed = "failed" not in test_output.lower() and result.returncode == 0

            if tests_passed and coverage_percentage >= self.config['coverage_threshold']:
                self.logger.info(f"All tests passed successfully and coverage is {coverage_percentage}%.")
            else:
                if not tests_passed:
                    self.logger.warning("Some tests failed. Please review the test output above.")
                if coverage_percentage < self.config['coverage_threshold']:
                    self.logger.warning(
                        f"Coverage is below {self.config['coverage_threshold']}%. Current coverage: {coverage_percentage}%")

            return tests_passed, coverage_percentage, test_output

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error running tests: {e}")
            return False, 0, str(e)
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")
            return False, 0, str(e)