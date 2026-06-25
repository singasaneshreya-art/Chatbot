
INTENTS = {
    'greeting': [
        'hello', 'hi', 'hey', 'good morning', 'good evening', 'howdy', 'greetings', 'hiya',
        'hello again', 'hi again', 'back to main menu', 'back to menu', 'menu', 'main menu'
    ],
    'order_status': [
        'order', 'package', 'delivery', 'shipment', 'shipped', 'tracking', 'where is my', 
        'arrive', 'dispatch', 'parcel'
    ],
    'refund': [
        'refund', 'money back', 'return', 'cancel', 'charge', 'payment', 'reimburse', 
        'cashback', 'dispute', 'billing'
    ],
    'complaint': [
        'complaint', 'problem', 'issue', 'bad', 'terrible', 'awful', 'worst', 'angry', 
        'frustrated', 'unhappy', 'disappointed', 'wrong', 'broken', 'not working'
    ],
    'hours': [
        'hours', 'open', 'close', 'timing', 'available', 'when', 'schedule', 
        'working hours', 'support time'
    ],
    'goodbye': [
        'bye', 'goodbye', 'see you', 'later', 'thanks', 'thank you', "that's all", 'done', 'exit'
    ]
}

def classify_intent(text):
    if not text:
        return 'fallback', 0.0
        
    normalized_text = text.lower().strip()
    best_intent = 'fallback'
    best_score = 0.0

    for intent_name, patterns in INTENTS.items():
        match_count = 0.0
        for pattern in patterns:
            if pattern in normalized_text:
                if ' ' in pattern:
                    match_count += 1.5
                else:
                    match_count += 1.0
        
        score = min(match_count / 3.0, 1.0)
        if score > best_score:
            best_score = score
            best_intent = intent_name

    if best_score < 0.15:
        return 'fallback', best_score
        
    return best_intent, best_score
