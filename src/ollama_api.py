import json
import requests
from typing import Generator


class OllamaAPI:
    def __init__(self, model: str, base_url: str):
        self.model = model
        self.base_url = base_url

    def generate(self, prompt: str) -> str:
        url = f"{self.base_url}/generate"
        data = {"model": self.model, "prompt": prompt, "stream": True}

        try:
            with requests.post(url, json=data, stream=True) as response:
                response.raise_for_status()
                return self._process_stream(response)
        except requests.RequestException as e:
            raise Exception(f"Ollama API error: {str(e)}")

    def _process_stream(self, response: requests.Response) -> str:
        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    json_line = json.loads(line.decode("utf-8"))
                    chunk = json_line.get("response", "")
                    full_response += chunk
                    print(chunk, end="", flush=True)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON: {line.decode('utf-8')}")
        print()  # Print a newline at the end
        return full_response