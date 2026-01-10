"""
Script to STRUCTURE raw cooking instructions using Hugging Face Router API 
(
        Ve a 👉 https://huggingface.co
        Crea cuenta
        Ve a Settings → Access Tokens
        Crea un token READ
        Guarda el token (ej: hf_xxxxxxxxx)
)
Model: meta-llama/Llama-3.1-8B-Instruct

Input : cbr_menu_database.json
Output: cbr_dataset_estructurado.json

Dependencies:
- requests
- beautifulsoup4

Install:
pip install requests beautifulsoup4
"""

import json
import os
import copy
import time
import requests
import re

# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------
INPUT_JSON = r'C:\Users\jiaha\Documents\Universidad\SBC\SBC-MENU\PART2\cbr_menu_database.json'
OUTPUT_JSON = r'C:\Users\jiaha\Documents\Universidad\SBC\SBC-MENU\PART2\cbr_dataset_estructurado.json'

HF_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")
HF_MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
HF_CHAT_URL = "https://router.huggingface.co/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json"
}

REQUEST_DELAY = 2  # seconds between API calls

# -------------------------------------------------
# UTILS
# -------------------------------------------------
def clean_llm_json(text):
    """
    Elimina backticks y markdown antes de parsear JSON
    """
    text = re.sub(r"^```json", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"^```", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"```$", "", text.strip(), flags=re.IGNORECASE)
    return text.strip()

def parse_llm_response(content):
    """
    Convierte la respuesta del LLM en JSON, capturando errores
    """
    text = clean_llm_json(content)
    try:
        return json.loads(text)
    except Exception as e:
        return {"error": "json_parse_failed", "details": str(e), "raw": text}

# -------------------------------------------------
# LLM CALL
# -------------------------------------------------
def structure_with_llm(raw_instructions, ingredients=""):
    if not HF_API_KEY:
        return {"error": "HUGGINGFACE_API_KEY not set"}

    prompt = f"""
You are a cooking knowledge extraction system.

Take the following raw cooking instructions and split them into steps. 
In raw cooking instructions, each sentence may contain multiple actions or steps (specially separated by commas or conjunctions like "and" or "then").
Also, don't repeat information in multiple atributes within steps. 

For each step, extract:
- order (integer)
- preparation action (main verb about the prepraration in infinitive form)
- where (list, may be empty)
- ingredients (list, may be empty)
- tools (list, may be empty)
- temperature (string or null, it can be a word like "high", "medium", "low", a numeric value with unit like "180C", "350F", etc, or an expression like "room temperature")
- time (string or null, similar to temperature)

Return ONLY valid JSON. Do NOT include explanations or markdown.

Raw instructions:
{raw_instructions}

Take into account that the following is all the ingredients used in the recipe (so you can identify them in the instructions):
{ingredients}
"""

    payload = {
        "model": HF_MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_new_tokens": 1000
    }

    try:
        response = requests.post(HF_CHAT_URL, headers=HEADERS, json=payload, timeout=120)
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}", "details": response.text}

        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return parse_llm_response(content)

    except Exception as e:
        return {"error": "llm_call_failed", "details": str(e)}

# -------------------------------------------------
# MAIN PROCESS
# -------------------------------------------------
def structure_dataset(input_path, output_path):
    print(f"📖 Loading dataset: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        database = json.load(f)

    structured_db = copy.deepcopy(database)
    total_structured = 0

    for menu_idx, menu in enumerate(structured_db.get("menus", []), 1):
        print(f"\n🍽️  Menu {menu_idx}: {menu.get('menu_name', 'Unnamed menu')}")

        for course_type in ["starter", "main", "dessert"]:
            course = menu.get("courses", {}).get(course_type)

            if not course or "instructions" not in course:
                continue

            title = course.get("title", "Unknown recipe")
            print(f"  🍳 Structuring {course_type}: {title}")

            raw_instructions = course["instructions"]
            ingredients = ", ".join(course.get("ingredients", []))
            
            structured = structure_with_llm(raw_instructions, ingredients)
            course["structured_instructions"] = structured

            total_structured += 1
            time.sleep(REQUEST_DELAY)

    print(f"\n💾 Saving structured dataset: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(structured_db, f, ensure_ascii=False, indent=2)

    print(f"✅ Done! Structured instructions for {total_structured} recipes")

# -------------------------------------------------
# ENTRY POINT
# -------------------------------------------------
if __name__ == "__main__":
    structure_dataset(INPUT_JSON, OUTPUT_JSON)
