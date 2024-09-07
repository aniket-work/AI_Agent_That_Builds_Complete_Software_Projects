import json
import os
import requests
from typing import Generator
from dotenv import load_dotenv

import os
from dotenv import load_dotenv
from groq import Groq

class GroqAPI:
    def __init__(self, model: str):
        load_dotenv()  # Load environment variables from .env file
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        self.model = model
        self.client = Groq(api_key=self.api_key)

    def generate(self, prompt: str) -> str:
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                stream=True
            )

            full_response = ""
            for chunk in chat_completion:
                content = chunk.choices[0].delta.content
                if content is not None:
                    full_response += content
                    print(content, end="", flush=True)
            print()  # Print a newline at the end
            return full_response
        except Exception as e:
            raise Exception(f"Groq API error: {str(e)}")