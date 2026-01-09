import os
import requests

HF_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")
url = "https://router.huggingface.co/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [
        {"role": "user", "content": "Prueba de inferencia"}
    ],
    "max_new_tokens": 100
}

response = requests.post(url, headers=headers, json=payload)
print(response.status_code)
print(response.text)