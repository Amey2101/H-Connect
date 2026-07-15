import os
import json

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

print("Key Loaded:", os.getenv("OPENROUTER_API_KEY") is not None)

def generate_triage(data: dict):

    prompt = f"""
You are an AI Clinical Decision Support Assistant.

Analyze the following emergency case.

Patient Age:
{data["patient_age"]}

Case Type:
{data["case_type"]}

Severity:
{data["severity"]}

Symptoms:
{data["symptoms"]}

Return ONLY valid JSON.

Required format:

{{
    "triage_level":"",
    "confidence":0,
    "likely_condition":"",
    "department":"",
    "bed":"",
    "preparation":[],
    "summary":""
}}
"""

    response = client.chat.completions.create(

        model="google/gemini-2.5-flash-lite",

        messages=[
            {
                "role":"system",
                "content":"You are an emergency medicine clinical decision support assistant. Return JSON only."
            },
            {
                "role":"user",
                "content":prompt
            }
        ],

        temperature=0.2,

        max_tokens=300

    )

    content = response.choices[0].message.content

    print(content)

    content = content.replace("```json", "")
    content = content.replace("```", "")
    content = content.strip()

    return json.loads(content)