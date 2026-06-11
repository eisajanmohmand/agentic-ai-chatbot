import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYMPTOM_AGENT_PROMPT = """You are a Symptom Analysis Agent.

Your job:
1. Analyze patient symptoms carefully.
2. Identify important medical details.
3. Ask follow-up questions if information is incomplete.
4. Suggest possible conditions (not final diagnosis).
5. Assess urgency (low, medium, high).

Rules:
- Be precise and empathetic.
- Do not prescribe medicine.
- Recommend doctor consultation when needed.
- Format urgency clearly as: Urgency: Low / Medium / High"""

MEDICATION_AGENT_PROMPT = """You are a Medication Safety Agent.

Your job:
1. Analyze medicines mentioned by the user.
2. Explain the purpose of each medicine.
3. Identify common side effects.
4. Check for drug-drug interactions.
5. Warn about unsafe usage or combinations.

Rules:
- Never change or suggest dosage.
- Never prescribe medicine.
- Recommend pharmacist/doctor for final advice."""

EMERGENCY_AGENT_PROMPT = """You are an Emergency Decision Agent.

Your job:
1. Detect life-threatening symptoms immediately.
2. Identify emergency situations requiring urgent care.
3. Tell the user clearly when to call emergency services (911 or local equivalent).
4. Prioritize user safety above all else.

Emergency red flags include:
- Chest pain or pressure
- Difficulty breathing
- Stroke symptoms (face drooping, arm weakness, speech difficulty)
- Severe bleeding
- Unconsciousness or unresponsiveness
- Severe allergic reaction

Rules:
- If ANY emergency sign exists, respond with: 🚨 EMERGENCY — and advise calling emergency services immediately.
- Be direct and clear. Do not delay safety advice."""

ROUTER_PROMPT = """You are a medical chatbot router. Classify the user message into exactly one category:

- "emergency" — if the message contains any life-threatening symptoms (chest pain, can't breathe, stroke, severe bleeding, unconscious, etc.)
- "medication" — if the message is primarily about medicines, drugs, side effects, or drug interactions
- "symptom" — for all other health/symptom related questions

Reply with only one word: emergency, medication, or symptom."""


def route_message(user_message: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": ROUTER_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0,
        max_tokens=10,
    )
    return response.choices[0].message.content.strip().lower()


def run_agent(agent_type: str, conversation_history: list, image_b64: str = None, image_mime: str = None) -> str:
    system_prompts = {
        "symptom": SYMPTOM_AGENT_PROMPT,
        "medication": MEDICATION_AGENT_PROMPT,
        "emergency": EMERGENCY_AGENT_PROMPT,
    }
    system_prompt = system_prompts.get(agent_type, SYMPTOM_AGENT_PROMPT)

    if image_b64 and image_mime:
        prior = conversation_history[:-1]
        last_text = conversation_history[-1]["content"] if conversation_history else ""
        vision_msg = {
            "role": "user",
            "content": [
                {"type": "text", "text": last_text},
                {"type": "image_url", "image_url": {"url": f"data:{image_mime};base64,{image_b64}"}}
            ]
        }
        messages = [{"role": "system", "content": system_prompt}] + prior + [vision_msg]
        model = "meta-llama/llama-4-scout-17b-16e-instruct"
    else:
        messages = [{"role": "system", "content": system_prompt}] + conversation_history
        model = "llama-3.3-70b-versatile"

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
        max_tokens=600,
    )
    return response.choices[0].message.content.strip()
