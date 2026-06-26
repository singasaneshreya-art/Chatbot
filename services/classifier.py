import math
import re

# Training Data: Map exemplar phrases to intents
TRAINING_DATA = [
    # Greetings
    ("hello", "greeting"),
    ("hi", "greeting"),
    ("hey", "greeting"),
    ("good morning", "greeting"),
    ("good evening", "greeting"),
    ("howdy", "greeting"),
    ("greetings", "greeting"),
    ("hiya", "greeting"),
    ("hello nexsupport", "greeting"),
    ("hi there", "greeting"),
    ("back to menu", "greeting"),
    ("main menu", "greeting"),
    ("menu", "greeting"),
    
    # Order Status
    ("where is my order", "order_status"),
    ("track my package", "order_status"),
    ("delivery status", "order_status"),
    ("when will my shipment arrive", "order_status"),
    ("is my order shipped", "order_status"),
    ("tracking details", "order_status"),
    ("dispatch details", "order_status"),
    ("where is my parcel", "order_status"),
    ("check my package", "order_status"),
    ("order status check", "order_status"),
    
    # Refund
    ("i want a refund", "refund"),
    ("money back guarantee", "refund"),
    ("request a return", "refund"),
    ("cancel my order and refund", "refund"),
    ("payment charge issue", "refund"),
    ("reimburse me", "refund"),
    ("cashback dispute", "refund"),
    ("billing problem", "refund"),
    ("need a refund", "refund"),
    
    # Complaint
    ("i want to lodge a complaint", "complaint"),
    ("terrible service problem", "complaint"),
    ("broken item received", "complaint"),
    ("unhappy and frustrated customer", "complaint"),
    ("worst product ever", "complaint"),
    ("unhappy with service", "complaint"),
    ("bad experience", "complaint"),
    ("complain about service", "complaint"),
    ("something is wrong", "complaint"),
    
    # Hours
    ("what are your hours", "hours"),
    ("are you open now", "hours"),
    ("when do you close", "hours"),
    ("support schedule timing", "hours"),
    ("available working hours", "hours"),
    ("support working time", "hours"),
    ("business hours", "hours"),
    
    # Goodbye
    ("bye bye", "goodbye"),
    ("goodbye", "goodbye"),
    ("see you later", "goodbye"),
    ("exit the chat", "goodbye"),
    ("thank you goodbye", "goodbye")
]

# Common English stop words to ignore during classification
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "is", "are", "was", "were", 
    "to", "for", "with", "on", "at", "by", "from", "i", "me", "my", 
    "you", "your", "we", "our", "it", "this", "that", "these", "those"
}

# Clean and tokenize text
def tokenize(text):
    if not text:
        return []
    # Tokenize alphanumeric words and lowercase them, filtering out stop words
    words = re.findall(r'\b\w+\b', text.lower())
    return [w for w in words if w not in STOP_WORDS]

# Compute Term Frequency (TF)
def compute_tf(tokens):
    tf = {}
    for token in tokens:
        tf[token] = tf.get(token, 0) + 1
    total_tokens = len(tokens)
    if total_tokens > 0:
        for token in tf:
            tf[token] = tf[token] / total_tokens
    return tf

# Precompute document frequencies (DF) for IDF calculation
vocab = set()
df = {}
num_docs = len(TRAINING_DATA)

for text, _ in TRAINING_DATA:
    tokens = set(tokenize(text))
    vocab.update(tokens)
    for token in tokens:
        df[token] = df.get(token, 0) + 1

# Precompute Inverse Document Frequency (IDF) with smoothing
idf = {}
for token in vocab:
    idf[token] = math.log((1 + num_docs) / (1 + df[token])) + 1

# Generate training vectors
TRAINING_VECTORS = []
for text, intent in TRAINING_DATA:
    tokens = tokenize(text)
    tf = compute_tf(tokens)
    vector = {}
    for token, val in tf.items():
        vector[token] = val * idf[token]
    TRAINING_VECTORS.append((vector, intent))

# Cosine Similarity between sparse vectors
def cosine_similarity(v1, v2):
    dot_product = 0.0
    for token, val1 in v1.items():
        if token in v2:
            dot_product += val1 * v2[token]
            
    norm1 = math.sqrt(sum(val**2 for val in v1.values()))
    norm2 = math.sqrt(sum(val**2 for val in v2.values()))
    
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
        
    return dot_product / (norm1 * norm2)

def classify_intent(text):
    """
    Classifies intent of input text using TF-IDF feature representation
    and Cosine Similarity matching against the training corpus.
    Returns: (intent_name, confidence_score)
    """
    if not text:
        return 'fallback', 0.0
        
    user_tokens = tokenize(text)
    if not user_tokens:
        return 'fallback', 0.0
        
    # Build user TF-IDF vector
    user_tf = compute_tf(user_tokens)
    user_vector = {}
    for token, val in user_tf.items():
        if token in idf:
            user_vector[token] = val * idf[token]
            
    best_intent = 'fallback'
    best_score = 0.0
    
    # Compare with all training exemplars
    for train_vector, intent in TRAINING_VECTORS:
        score = cosine_similarity(user_vector, train_vector)
        if score > best_score:
            best_score = score
            best_intent = intent
            
    # Set a minimum confidence threshold for classification
    if best_score < 0.15:
        return 'fallback', best_score
        
    return best_intent, best_score
