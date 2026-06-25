import os
import requests

def call_claude(conversation_history):
    # Retrieve key solely from environment variables
    key = os.getenv('ANTHROPIC_API_KEY')
    if not key:
        raise ValueError("Anthropic API key is not configured.")

    url = 'https://api.anthropic.com/v1/messages'
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': key,
        'anthropic-version': '2023-06-01'
    }
    
    body = {
        'model': 'claude-sonnet-4-6',
        'max_tokens': 1000,
        'system': "You are NexSupport, a professional customer service AI. Help users with orders, refunds, complaints. Also guide CS/AI students building NLP chatbot projects. Keep responses under 4 lines. Use **bold** for emphasis.",
        'messages': conversation_history
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
        return data['content'][0]['text']
    except requests.exceptions.Timeout:
        raise Exception("Connection timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error: {str(e)}")
