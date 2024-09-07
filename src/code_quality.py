import re
import subprocess
from typing import Tuple
from constants import AUTOPEP8_CMD, PYLINT_CMD, COMPLEXIPY_CMD, PYLINT_SCORE_PATTERN, COMPLEXIPY_SCORE_PATTERN


def run_autopep8(file_path: str, cwd: str) -> None:
    cmd = AUTOPEP8_CMD + [file_path]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=cwd)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        print(f"Command: {e.cmd}")
        print(f"Return code: {e.returncode}")
        print(f"Output: {e.output}")
        print(f"Error: {e.stderr}")


def run_pylint(file_path: str, cwd: str) -> Tuple[float, str]:
    cmd = PYLINT_CMD + [file_path]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    pylint_output = result.stdout + result.stderr
    score_match = re.search(PYLINT_SCORE_PATTERN, pylint_output)
    pylint_score = float(score_match.group(1)) if score_match else 0.0
    return pylint_score, pylint_output


def run_complexipy(file_path: str, cwd: str) -> Tuple[int, str]:
    cmd = COMPLEXIPY_CMD + [file_path]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    complexipy_output = result.stdout + result.stderr
    escaped_path = re.escape(file_path)
    score_match = re.search(COMPLEXIPY_SCORE_PATTERN.format(escaped_path=escaped_path), complexipy_output, re.DOTALL)
    complexipy_score = int(score_match.group(1)) if score_match else None
    return complexipy_score, complexipy_output


def check_code_quality(file_path: str, cwd: str) -> Tuple[float, int, str, str]:
    run_autopep8(file_path, cwd)
    pylint_score, pylint_output = run_pylint(file_path, cwd)
    complexipy_score, complexipy_output = run_complexipy(file_path, cwd)
    return pylint_score, complexipy_score, pylint_output, complexipy_output