import requests
import json
import os

class LLMClient:
    def __init__(self, provider="ollama", base_url="http://localhost:11434", api_key=None):
        self.provider = provider
        self.base_url = base_url
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def prompt(self, prompt_text, model="llama2"):
        print(f"LLMClient: Using {model} model via {self.provider} at {self.base_url}")
        print(f"LLMClient: Sending prompt: {prompt_text[:100]}{'...' if len(prompt_text) > 100 else ''}")
        
        if self.provider == "ollama":
            return self._ollama_prompt(prompt_text, model)
        elif self.provider == "cloud":
            return self._cloud_prompt(prompt_text, model)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _ollama_prompt(self, prompt_text, model):
        """Handle Ollama's streaming response format"""
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": model, "prompt": prompt_text},
            stream=True
        )
        response.raise_for_status()
        
        # Ollama returns streaming JSON responses, one per line
        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    json_response = json.loads(line.decode('utf-8'))
                    if 'response' in json_response:
                        full_response += json_response['response']
                    if json_response.get('done', False):
                        break
                except json.JSONDecodeError:
                    continue
        
        return full_response

    def _cloud_prompt(self, prompt_text, model):
        """Handle cloud LLM API (e.g., OpenAI) standard JSON response"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Example for OpenAI format - adjust based on your cloud provider
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt_text}
            ],
            "max_tokens": 1000
        }
        
        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        # Handle standard JSON response
        json_response = response.json()
        return json_response["choices"][0]["message"]["content"] 