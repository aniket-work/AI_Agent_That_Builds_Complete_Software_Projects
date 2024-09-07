import os
import re
import ast
import time
import logging
from contextlib import contextmanager
import win32file
import win32con
from constants import FILE_CONTENT_PATTERN

logger = logging.getLogger(__name__)

@contextmanager
def file_lock(file_path: str):
    lock_path = f"{file_path}.lock"
    file_handle = None
    try:
        file_handle = win32file.CreateFile(
            lock_path,
            win32con.GENERIC_READ | win32con.GENERIC_WRITE,
            0,  # Exclusive access
            None,
            win32con.OPEN_ALWAYS,
            win32con.FILE_ATTRIBUTE_NORMAL,
            None
        )
        win32file.LockFileEx(file_handle, win32con.LOCKFILE_EXCLUSIVE_LOCK | win32con.LOCKFILE_FAIL_IMMEDIATELY, 0, -0x10000, 0)
        yield
    except OSError as e:
        if e.winerror == 33:  # ERROR_LOCK_VIOLATION
            raise IOError("File is locked by another process")
        raise
    finally:
        if file_handle:
            win32file.UnlockFileEx(file_handle, 0, -0x10000, 0)
            win32file.CloseHandle(file_handle)
        try:
            os.remove(lock_path)
        except OSError:
            pass

def robust_write_file(file_path: str, content: str, max_attempts: int, retry_delay: int) -> bool:
    logger.info(f"Attempting to write to file: {file_path}")
    for attempt in range(max_attempts):
        try:
            with file_lock(file_path):
                with open(file_path, "w") as f:
                    f.write(content)
                logger.info(f"Successfully wrote to file: {file_path}")
                return True
        except IOError as e:
            logger.error(f"IOError writing to {file_path}: {e}")
            if attempt < max_attempts - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to write to {file_path} after {max_attempts} attempts")
        except Exception as e:
            logger.error(f"Unexpected error writing to {file_path}: {e}")
            break
    return False

def extract_file_contents(solution: str) -> dict:
    file_contents = {}
    matches = re.findall(FILE_CONTENT_PATTERN, solution, re.DOTALL)
    for filename, content in matches:
        file_contents[filename.strip()] = content.strip()
    return file_contents

def validate_file_content(file_path: str, content: str) -> str:
    if file_path.endswith(".py"):
        content = clean_markdown_artifacts(content)
        try:
            ast.parse(content)
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            return None
    return content

def clean_markdown_artifacts(content: str) -> str:
    content = re.sub(r"```python\n|```\n|```", "", content)
    content = content.strip()
    content = re.sub(r"^#+\s+.*$", "", content, flags=re.MULTILINE)
    content = re.sub(r"`([^`]+)`", r"\1", content)
    return content