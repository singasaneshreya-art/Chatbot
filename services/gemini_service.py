import os
import requests

def call_gemini(conversation_history, order_context=None):
    """
    Calls Google Gemini API using REST endpoint.
    Maps Flask session role names ('user', 'assistant') to Gemini roles ('user', 'model').
    """
    key = os.getenv('GEMINI_API_KEY')
    if not key:
        raise ValueError("Gemini API key is not configured.")

    # Rest API Endpoint for Gemini
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
    headers = {
        'Content-Type': 'application/json'
    }

    # Map roles from user/assistant to user/model
    contents = []
    for msg in conversation_history:
        role = 'user' if msg.get('role') == 'user' else 'model'
        contents.append({
            'role': role,
            'parts': [{'text': msg.get('content', '')}]
        })

    instruction_text = (
        "You are NexSupport, a professional customer service AI. "
        "You can ONLY help users with queries regarding their orders (such as tracking, status, items, or disputes). "
        "If the user asks about anything else (including general questions, chit-chat, jokes, coding, or off-topic subjects), "
        "you MUST politely refuse and state: 'I can only help you with your orders only.' "
        "Keep responses under 4 lines. Use **bold** for emphasis."
    )
    if order_context:
        instruction_text += f"\n\n[Active Context]\n{order_context}"

    system_instruction = {
        "parts": [{
            "text": instruction_text
        }]
    }

    body = {
        "contents": contents,
        "systemInstruction": system_instruction,
        "generationConfig": {
            "maxOutputTokens": 1000
        }
    }

    try:
        response = requests.post(url, headers=headers, json=body, timeout=30)
        if response.status_code != 200:
            try:
                error_info = response.json()
                error_msg = error_info.get('error', {}).get('message', f"HTTP {response.status_code}")
            except Exception:
                error_msg = f"HTTP {response.status_code}: {response.text}"
            raise Exception(error_msg)

        data = response.json()
        text = data['candidates'][0]['content']['parts'][0]['text']
        return text
    except requests.exceptions.Timeout:
        raise Exception("Connection timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error: {str(e)}")
