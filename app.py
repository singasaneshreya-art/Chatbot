import os
import random
import re
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

# Load environment variables FIRST, before importing any local services
# that might rely on them during initialization.
load_dotenv()

from services.classifier import classify_intent
import services.gemini_service as gemini_service
import services.session_manager as session_manager
import services.order_service as order_service
from services.mongodb_service import seed_db_if_empty
import services.translation_service as translation_service

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'nexsupport-super-secret-key-1234')

# Standard Responses mapped by intent
RESPONSES = {
    'greeting': [
        "👋 Hello! Welcome to NexSupport. I can help you track your **order**, process a **refund**, or check our **support hours**! What can I do for you today?",
        "👋 Hi there! NexSupport is at your service. Let me know if you have questions about your recent **orders** or **refunds**!"
    ],
    'order_status': [
        "📦 I can certainly help check your order status. Could you please provide your **Order ID**? Standard delivery takes **3-5 business days**. You can also track your shipment here: `https://track.nexsupport.com/`",
        "📦 Sure, let's check your shipment. Please share your **Order ID**! Once shipped, standard delivery takes **3-5 days**, and you will receive a tracking link via email."
    ],
    'refund': [
        "💳 We offer a **30-day refund policy** for all products. If you are within this window, please provide your **Order ID** and the reason for return so I can initiate the refund.",
        "💳 No worries! Refunds are fully supported within **30 days** of purchase. Please share your **Order ID** and we'll get that processed for you."
    ],
    'complaint': [
        "😤 I am truly sorry to hear that you are experiencing issues. I have recorded your complaint and escalated it to our high-priority support team. A manager will reach out within **2 hours**.",
        "😤 I apologize for the frustration this has caused. I am escalating this immediately. Our premium support agents will contact you within **2 hours** to resolve this issue."
    ],
    'hours': [
        "🕐 NexSupport is open from **Monday to Friday: 9AM – 7PM IST** and **Saturday: 10AM – 4PM IST**. We are closed on Sundays.",
        "🕐 Our support hours are **Mon-Fri 9:00 AM – 7:00 PM IST** and **Saturday 10:00 AM – 4:00 PM IST**. On Sundays, we are closed."
    ],
    'goodbye': [
        "👋 Goodbye! Thank you for choosing NexSupport. Feel free to reach out if you need anything else. Have a wonderful day!",
        "👋 Thanks for chatting! I'm closing this session. Let me know if you need help in the future. Take care!"
    ]
}

@app.route('/')
def home():
    # Keep the selected language in session, but clear history/collect states
    session_manager.clear_history()
    session_manager.clear_collect_state()
    lang = session_manager.get_language()
    
    welcome_text = "👋 Hi! I'm **Support AI** — your AI-powered customer service agent.\n\nI can help you track your **order**, process a **refund**, or check our **support hours**! What can I do for you today?"
    welcome_chips = ["Track my order", "I need a refund", "What are your hours?"]
    
    welcome_text = translation_service.translate_to_language(welcome_text, lang)
    welcome_chips = [translation_service.translate_to_language(chip, lang) for chip in welcome_chips]
    
    sidebar_hours_raw = [
        {"icon": "clock", "label": "Mon-Fri: 9 AM - 7 PM"},
        {"icon": "calendar", "label": "Sat: 10 AM - 4 PM"},
        {"icon": "calendar", "label": "Sun: Closed"}
    ]
    sidebar_hours = []
    for item in sidebar_hours_raw:
        sidebar_hours.append({
            "icon": item["icon"],
            "label": translation_service.translate_to_language(item["label"], lang)
        })
    operating_hours_title = translation_service.translate_to_language("Operating Hours", lang)

    return render_template(
        'index.html',
        active_language=lang,
        welcome_text=welcome_text,
        welcome_chips=welcome_chips,
        sidebar_hours=sidebar_hours,
        operating_hours_title=operating_hours_title
    )

@app.route('/api/language', methods=['POST'])
def set_language():
    data = request.json or {}
    lang = data.get('language', 'en')
    session_manager.set_language(lang)
    session_manager.clear_history()
    session_manager.clear_collect_state()
    return jsonify({'success': True, 'language': lang})

def chat_internal(message_orig, message_trans, simulate_claude=False):
    message = message_trans
    
    # Record user message in history (using English version for clean context)
    session_manager.add_message('user', message)
    
    cleaned_msg = message.lower().strip()
    flow = session_manager.get_flow()
    
    # 1. Check for cancel keywords to exit active flow
    if cleaned_msg in ['cancel', 'back', 'menu', 'exit', 'back to main menu', 'back to menu']:
        session_manager.set_flow(None)
        session_manager.clear_collect_state()
        response_text = "Action cancelled. Back to the main menu!"
        chips = ["Track my order", "I need a refund", "What are your hours?"]
        session_manager.add_message('assistant', response_text)
        return jsonify({
            'intent': 'greeting',
            'confidence': 1.0,
            'response': response_text,
            'chips': chips
        })

    # 2. Check if collecting customer details for order lookup
    if flow == 'collecting_name':
        user_name = message_orig.strip()
        session_manager.set_user_name(user_name)
        session_manager.set_flow('collecting_email')
        response_text = f"Thanks, **{user_name}**! Now, please enter your email address so we can associate it with this order."
        chips = ["Cancel"]
        session_manager.add_message('assistant', response_text)
        return jsonify({
            'intent': 'order_status',
            'confidence': 1.0,
            'response': response_text,
            'chips': chips
        })

    elif flow == 'collecting_email':
        email = message_orig.strip()
        if '@' not in email or '.' not in email:
            response_text = "That doesn't look like a valid email address. Please enter a valid email (e.g. name@example.com):"
            chips = ["Cancel"]
            session_manager.add_message('assistant', response_text)
            return jsonify({
                'intent': 'order_status',
                'confidence': 0.5,
                'response': response_text,
                'chips': chips
            })

        user_name = session_manager.get_user_name()
        order_id = session_manager.get_active_order_id()
        
        # Save customer details to MongoDB Atlas
        order = order_service.update_order_customer(order_id, user_name, email)
        
        pre_collect_flow = session_manager.get_pre_collect_flow()
        session_manager.clear_collect_state()
        
        if pre_collect_flow == 'refund':
            session_manager.set_flow('refund')
            session_manager.set_active_order_id(order_id)
            response_text = (
                f"💳 **Refund Options for Order {order_id}**\n\n"
                f"Customer: **{user_name}** ({email})\n\n"
                f"Since your package was marked delivered but not received, we can:\n"
                f"1. **Re-ship** the {order['item']} immediately.\n"
                f"2. Issue a **full refund of {order['price']}** back to your original payment method.\n\n"
                f"Would you like me to process a full refund?"
            )
            chips = ["Yes, issue refund", "Contact to Customer", "Back to main menu"]
            session_manager.add_message('assistant', response_text)
            return jsonify({
                'intent': 'refund',
                'confidence': 1.0,
                'response': response_text,
                'chips': chips
            })
        elif order_id == 'ORD-8821':
            session_manager.set_active_order_id('ORD-8821')
            response_text = (
                f"Hello, **{user_name}** ({email})! I understand your concern regarding **Order #8821**. I've looked into the tracking logs for you.\n\n"
                "According to our detailed dispatch records:\n\n"
                "* The package was marked delivered at **9:45 AM**.\n"
                "* Location: **Secured Parcel Locker #12**.\n"
                "* The signature was provided by **\"Front Desk Personnel\"**.\n\n"
                "Would you like me to initiate a **GPS verification request** with the courier or contact your building management directly?"
            )
            chips = ["Track GPS", "Contact to Customer", "Refund Options"]
            session_manager.add_message('assistant', response_text)
            return jsonify({
                'intent': 'order_status',
                'confidence': 1.0,
                'response': response_text,
                'chips': chips,
                'order_card': {
                    'item': order['item'],
                    'model': order.get('model', 'Model: 2024-Charcoal'),
                    'price': order['price'],
                    'badge': order.get('badge', 'Active Dispute'),
                    'image': order.get('image_url') or '/static/images/chair.png'
                }
            })

        # Construct dynamic prompt context for Gemini
        order_context = (
            f"You are showing the order status to the customer.\n"
            f"Order Details:\n"
            f"- Order ID: {order['id']}\n"
            f"- Customer: {user_name} ({email})\n"
            f"- Status: {order['status']}\n"
            f"- Item Name: {order['item']}\n"
            f"- Price: {order['price']}\n"
            f"- Estimated Time of Delivery (ETA): {order['eta'] or 'Not available'}\n"
            f"- Image URL: {order.get('image_url')}\n\n"
            f"Please address the customer by name, mention the name of the product, "
            f"its delivery status (shipment/delivered), and its ETA. Keep it friendly and under 4 lines."
        )
        
        try:
            history = session_manager.get_history()
            response_text = gemini_service.call_gemini(history, order_context=order_context)
        except Exception as e:
            if not app.config.get('TESTING'):
                print(f"Gemini call failed for order status, using fallback: {e}")
            eta_line = f"ETA:     ~{order['eta']}\n" if order.get('eta') else ""
            response_text = (
                f"📦 **Order {order['id']}**\n\n"
                f"Customer: {user_name} ({email})\n"
                f"Status:  {order['status']}\n"
                f"Item:    1× {order['item']}\n"
                f"Price:   {order['price']}\n"
                f"{eta_line}"
            )
            
        chips = ["Back to main menu"]
        
        # Clear active order ID if not ORD-8821 (which has active interactive dispute options)
        if order_id != 'ORD-8821':
            session_manager.set_active_order_id(None)
        
        order_card = None
        image_path = order.get('image_url') or order.get('image')
        if image_path:
            order_card = {
                'item': order['item'],
                'model': order.get('model', 'Model: Default' if order['id'] != 'ORD-8821' else 'Model: 2024-Charcoal'),
                'price': order['price'],
                'badge': order.get('badge', 'Active Order' if order['id'] != 'ORD-8821' else 'Active Dispute'),
                'image': image_path
            }
        
        session_manager.add_message('assistant', response_text)
        return jsonify({
            'intent': 'order_status',
            'confidence': 1.0,
            'response': response_text,
            'chips': chips,
            'order_card': order_card
        })


    # 2. Check for test order generation keywords when in an active flow
    if flow in ['order_tracking', 'refund'] and cleaned_msg in ['generate test order', 'simulate test order', 'test order', 'current order id', 'order id', 'generate order id', 'generate orderid', 'get my order id', 'get order id']:
        existing_id = session_manager.get_active_order_id()
        if existing_id and order_service.get_order(existing_id):
            new_id = existing_id
        else:
            new_id = order_service.create_random_order()
            session_manager.set_active_order_id(new_id)
            
        if flow == 'refund':
            response_text = (
                f"📋 **Order ID Retrieved!**\n\n"
                f"Your active Order ID is: `{new_id}`\n\n"
                f"You can now copy and paste this ID or type it to request a refund."
            )
            chips = [new_id, "Back to main menu"]
            session_manager.add_message('assistant', response_text)
            return jsonify({
                'intent': 'refund',
                'confidence': 1.0,
                'response': response_text,
                'chips': chips
            })
        else:
            response_text = (
                f"📋 **Order ID Retrieved!**\n\n"
                f"Your active Order ID is: `{new_id}`\n\n"
                f"You can now copy and paste this ID or type it to track this order."
            )
            chips = [new_id, "Back to main menu"]
            session_manager.add_message('assistant', response_text)
            return jsonify({
                'intent': 'order_status',
                'confidence': 1.0,
                'response': response_text,
                'chips': chips
            })

    # Handle active refund decisions (re-ship vs refund)
    active_order_id = session_manager.get_active_order_id()
    if flow == 'refund' and active_order_id:
        order = order_service.get_order(active_order_id)
        if order:
            if any(k in cleaned_msg for k in ['re-ship', 'reship', 're ship', '1', 're-shipment']):
                response_text = (
                    f"📦 **Replacement Order Confirmed**\n\n"
                    f"We have successfully initiated a replacement order for your **{order['item']}** (Order {active_order_id}).\n"
                    f"A new confirmation email with tracking details will be sent to you shortly."
                )
                chips = ["Back to main menu"]
                session_manager.clear_collect_state()
                session_manager.set_flow(None)
                session_manager.set_active_order_id(None)
                session_manager.add_message('assistant', response_text)
                return jsonify({
                    'intent': 'refund',
                    'confidence': 1.0,
                    'response': response_text,
                    'chips': chips
                })
            elif any(k in cleaned_msg for k in ['yes, issue refund', 'issue refund', 'refund', '2', 'refund options']):
                response_text = (
                    f"💳 **Refund Initiated**\n\n"
                    f"We have successfully initiated a full refund of **{order['price']}** for your **{order['item']}**.\n"
                    f"The credit will appear back on your original payment method within **3-5 business days**."
                )
                chips = ["Back to main menu"]
                session_manager.clear_collect_state()
                session_manager.set_flow(None)
                session_manager.set_active_order_id(None)
                session_manager.add_message('assistant', response_text)
                return jsonify({
                    'intent': 'refund',
                    'confidence': 1.0,
                    'response': response_text,
                    'chips': chips
                })

    # Mockup interactive flows for active order ORD-8821
    if active_order_id == 'ORD-8821':
        if any(k in cleaned_msg for k in ['empty', 'gps', 'courier', 'track gps', 'check with the courier']):
            response_text = (
                "📍 **GPS Verification Request Initiated**\n\n"
                "I have contacted the courier to retrieve the exact GPS coordinates and time of the scan. "
                "I am also opening a priority dispute ticket for you. An agent will contact you shortly."
            )
            chips = ["Contact to Customer", "Refund Options", "Back to main menu"]
            session_manager.add_message('assistant', response_text)
            return jsonify({
                'intent': 'order_status',
                'confidence': 1.0,
                'response': response_text,
                'chips': chips
            })
        elif any(k in cleaned_msg for k in ['contact', 'customer']):
            response_text = (
                "📞 **Priority Support Escalation**\n\n"
                "I've escalated your issue regarding Order #8821 to a senior support representative. "
                "A live agent will call or email you in **less than 10 minutes** to resolve this."
            )
            chips = ["Refund Options", "Back to main menu"]
            session_manager.add_message('assistant', response_text)
            return jsonify({
                'intent': 'complaint',
                'confidence': 1.0,
                'response': response_text,
                'chips': chips
            })
        elif any(k in cleaned_msg for k in ['refund', 'refund options']):
            response_text = (
                "💳 **Refund Options for Order ORD-8821**\n\n"
                "Since your package was marked delivered but not received, we can:\n"
                "1. **Re-ship** the ErgoCore Pro Series X immediately.\n"
                "2. Issue a **full refund of $499.00** back to your original payment method.\n\n"
                "Would you like me to process a full refund?"
            )
            chips = ["Yes, issue refund", "Contact to Customer", "Back to main menu"]
            session_manager.add_message('assistant', response_text)
            return jsonify({
                'intent': 'refund',
                'confidence': 1.0,
                'response': response_text,
                'chips': chips
            })
        elif 'yes, issue refund' in cleaned_msg:
            response_text = (
                "💳 **Refund Initiated**\n\n"
                "We have successfully initiated a full refund of **$499.00** for your **ErgoCore Pro Series X**.\n"
                "The credit will appear on your account within **3-5 business days**."
            )
            chips = ["Back to main menu"]
            session_manager.add_message('assistant', response_text)
            return jsonify({
                'intent': 'refund',
                'confidence': 1.0,
                'response': response_text,
                'chips': chips
            })

    # 3. Check if a valid Order ID is in the message
    extracted_id = order_service.extract_order_id(message)
    if extracted_id:
        order = order_service.get_order(extracted_id)
        if order:
            # If order has no customer details yet, collect them first
            if not order.get('customer_name') or not order.get('customer_email'):
                session_manager.set_active_order_id(extracted_id)
                session_manager.set_pre_collect_flow(flow)
                session_manager.set_flow('collecting_name')
                
                response_text = (
                    f"I found Order **{extracted_id}**. To retrieve your order details, "
                    f"please tell me your full name."
                )
                chips = ["Cancel"]
                session_manager.add_message('assistant', response_text)
                return jsonify({
                    'intent': 'order_status',
                    'confidence': 1.0,
                    'response': response_text,
                    'chips': chips
                })
                
            user_name = order.get('customer_name')
            email = order.get('customer_email')
            
            if order['id'] == 'ORD-8821':
                session_manager.set_active_order_id('ORD-8821')
                response_text = (
                    f"Hello, **{user_name}** ({email})! I understand your concern regarding **Order #8821**. I've looked into the tracking logs for you.\n\n"
                    "According to our detailed dispatch records:\n\n"
                    "* The package was marked delivered at **9:45 AM**.\n"
                    "* Location: **Secured Parcel Locker #12**.\n"
                    "* The signature was provided by **\"Front Desk Personnel\"**.\n\n"
                    "Would you like me to initiate a **GPS verification request** with the courier or contact your building management directly?"
                )
                chips = ["Track GPS", "Contact to Customer", "Refund Options"]
                session_manager.add_message('assistant', response_text)
                return jsonify({
                    'intent': 'order_status',
                    'confidence': 1.0,
                    'response': response_text,
                    'chips': chips,
                    'order_card': {
                        'item': order['item'],
                        'model': order.get('model', 'Model: 2024-Charcoal'),
                        'price': order['price'],
                        'badge': order.get('badge', 'Active Dispute'),
                        'image': order.get('image_url') or '/static/images/chair.png'
                    }
                })
            elif flow == 'refund':
                session_manager.set_flow(None) # exit flow
                session_manager.set_active_order_id(None) # clear active order ID since it's completed
                response_text = (
                    f"💳 **Refund Initiated for Order {order['id']}**\n\n"
                    f"Customer: **{user_name}** ({email})\n\n"
                    f"We have successfully initiated a refund of **{order['price']}** for your **{order['item']}**.\n"
                    f"The funds should appear back in your account within **3–5 business days**."
                )
                chips = ["Track my order", "Back to main menu"]
                session_manager.add_message('assistant', response_text)
                return jsonify({
                    'intent': 'refund',
                    'confidence': 1.0,
                    'response': response_text,
                    'chips': chips
                })
            else:
                session_manager.set_flow(None) # exit flow
                session_manager.set_active_order_id(None) # clear active order ID since it's completed
                
                # Construct dynamic prompt context for Gemini
                order_context = (
                    f"You are showing the order status to the customer.\n"
                    f"Order Details:\n"
                    f"- Order ID: {order['id']}\n"
                    f"- Customer: {user_name} ({email})\n"
                    f"- Status: {order['status']}\n"
                    f"- Item Name: {order['item']}\n"
                    f"- Price: {order['price']}\n"
                    f"- Estimated Time of Delivery (ETA): {order['eta'] or 'Not available'}\n"
                    f"- Image URL: {order.get('image_url')}\n\n"
                    f"Please address the customer by name, mention the name of the product, "
                    f"its delivery status (shipment/delivered), and its ETA. Keep it friendly and under 4 lines."
                )
                
                try:
                    history = session_manager.get_history()
                    response_text = gemini_service.call_gemini(history, order_context=order_context)
                except Exception as e:
                    if not app.config.get('TESTING'):
                        print(f"Gemini call failed for order status, using fallback: {e}")
                    eta_line = f"ETA:     ~{order['eta']}\n" if order['eta'] else ""
                    response_text = (
                        f"📦 **Order {order['id']}**\n\n"
                        f"Customer: {user_name} ({email})\n"
                        f"Status:  {order['status']}\n"
                        f"Item:    1× {order['item']}\n"
                        f"Price:   {order['price']}\n"
                        f"{eta_line}"
                    )
                    
                chips = ["Back to main menu"]
                
                # Check for dynamic order card
                order_card = None
                image_path = order.get('image_url') or order.get('image')
                if image_path:
                    order_card = {
                        'item': order['item'],
                        'model': order.get('model', 'Model: Default'),
                        'price': order['price'],
                        'badge': order.get('badge', 'Active Order'),
                        'image': image_path
                    }
                
                session_manager.add_message('assistant', response_text)
                return jsonify({
                    'intent': 'order_status',
                    'confidence': 1.0,
                    'response': response_text,
                    'chips': chips,
                    'order_card': order_card
                })
        else:
            response_text = (
                f"That Order ID (**{extracted_id}**) could not be found in our database. "
                "Please double check the ID and try again."
            )
            chips = ["Get My Order ID", "Back to main menu"]
            session_manager.add_message('assistant', response_text)
            return jsonify({
                'intent': flow or 'order_status',
                'confidence': 0.5,
                'response': response_text,
                'chips': chips
            })

    # 4. No Order ID found in message. Run NLP Intent Classification
    intent, score = classify_intent(message)
    
    # 5. Route based on intent
    if intent == 'greeting':
        session_manager.set_flow(None)
        choices = RESPONSES.get('greeting', ["Hello!"])
        response_text = random.choice(choices)
        chips = ["Track my order", "I need a refund", "What are your hours?"]
        session_manager.add_message('assistant', response_text)
        return jsonify({
            'intent': intent,
            'confidence': score,
            'response': response_text,
            'chips': chips
        })

    elif intent == 'goodbye':
        session_manager.set_flow(None)
        choices = RESPONSES.get('goodbye', ["Goodbye!"])
        response_text = random.choice(choices)
        chips = ["Hello again"]
        session_manager.add_message('assistant', response_text)
        return jsonify({
            'intent': intent,
            'confidence': score,
            'response': response_text,
            'chips': chips
        })

    elif intent == 'hours':
        session_manager.set_flow(None)
        choices = RESPONSES.get('hours', ["Our hours are Mon-Fri 9am-7pm IST."])
        response_text = random.choice(choices)
        chips = ["Track my order", "Back to main menu"]
        session_manager.add_message('assistant', response_text)
        return jsonify({
            'intent': intent,
            'confidence': score,
            'response': response_text,
            'chips': chips
        })

    elif intent == 'complaint':
        session_manager.set_flow(None)
        choices = RESPONSES.get('complaint', ["Sorry for the trouble..."])
        response_text = random.choice(choices)
        chips = ["What are your hours?", "Back to main menu"]
        session_manager.add_message('assistant', response_text)
        return jsonify({
            'intent': intent,
            'confidence': score,
            'response': response_text,
            'chips': chips
        })

    elif intent == 'order_status':
        if flow == 'order_tracking':
            existing_id = session_manager.get_active_order_id()
            if existing_id and order_service.get_order(existing_id):
                new_id = existing_id
            else:
                new_id = order_service.create_random_order()
                session_manager.set_active_order_id(new_id)
            response_text = (
                f"📋 **Order ID Retrieved!**\n\n"
                f"Your active Order ID is: `{new_id}`\n\n"
                f"You can now copy and paste this ID or type it to track this order."
            )
            chips = [new_id, "Back to main menu"]
            session_manager.add_message('assistant', response_text)
            return jsonify({
                'intent': 'order_status',
                'confidence': 1.0,
                'response': response_text,
                'chips': chips
            })
        else:
            session_manager.set_flow('order_tracking')
            choices = RESPONSES.get('order_status', ["Please enter your Order ID."])
            response_text = random.choice(choices)
            chips = ["Get My Order ID", "Back to main menu"]
            session_manager.add_message('assistant', response_text)
            return jsonify({
                'intent': 'order_status',
                'confidence': score,
                'response': response_text,
                'chips': chips
            })

    elif intent == 'refund':
        if flow == 'refund':
            existing_id = session_manager.get_active_order_id()
            if existing_id and order_service.get_order(existing_id):
                new_id = existing_id
            else:
                new_id = order_service.create_random_order()
                session_manager.set_active_order_id(new_id)
            response_text = (
                f"📋 **Order ID Retrieved!**\n\n"
                f"Your active Order ID is: `{new_id}`\n\n"
                f"You can now copy and paste this ID or type it to request a refund."
            )
            chips = [new_id, "Back to main menu"]
            session_manager.add_message('assistant', response_text)
            return jsonify({
                'intent': 'refund',
                'confidence': 1.0,
                'response': response_text,
                'chips': chips
            })
        else:
            session_manager.set_flow('refund')
            choices = RESPONSES.get('refund', ["Please enter your Order ID for refund."])
            response_text = random.choice(choices)
            chips = ["Get My Order ID", "Back to main menu"]
            session_manager.add_message('assistant', response_text)
            return jsonify({
                'intent': 'refund',
                'confidence': score,
                'response': response_text,
                'chips': chips
            })

    # 6. Fallback/Unrecognized Intent
    else:
        # Check simulation override
        if simulate_claude or cleaned_msg == 'simulate claude response' or cleaned_msg == 'simulate ai response':
            response_text = (
                "🤖 **[Simulated AI Response]**:\n"
                "I am **NexSupport**, your AI assistant. I can only help you with your orders only."
            )
            chips = ["Track my order", "Back to main menu"]
            session_manager.add_message('assistant', response_text)
            return jsonify({
                'intent': intent,
                'confidence': score,
                'response': response_text,
                'chips': chips
            })

        # If currently in order tracking flow but typed unrecognized text, return format warning
        if flow == 'order_tracking':
            response_text = (
                "That doesn't look like a valid Order ID.\n\n"
                "Order IDs follow this format: **ORD-XXXXXX**\n"
                "(Example: **ORD-789012**)\n\n"
                "You can find your Order ID in your confirmation email."
            )
            chips = ["Get My Order ID", "Back to main menu"]
            session_manager.add_message('assistant', response_text)
            return jsonify({
                'intent': 'order_status',
                'confidence': 0.5,
                'response': response_text,
                'chips': chips
            })

        # If currently in refund flow but typed unrecognized text, return format warning
        elif flow == 'refund':
            response_text = (
                "That doesn't look like a valid Order ID.\n\n"
                "Please provide a valid Order ID (e.g., **ORD-789012**) to process your refund."
            )
            chips = ["Get My Order ID", "Back to main menu"]
            session_manager.add_message('assistant', response_text)
            return jsonify({
                'intent': 'refund',
                'confidence': 0.5,
                'response': response_text,
                'chips': chips
            })

        # No active flow: use Gemini / AI fallback
        else:
            history = session_manager.get_history()
            try:
                response_text = gemini_service.call_gemini(history)
                chips = ["Back to main menu", "Track my order"]
            except ValueError:
                return jsonify({
                    'intent': intent,
                    'confidence': score,
                    'error': 'API_KEY_REQUIRED',
                    'response': (
                        "⚠️ **Gemini AI API Key Required**\n\n"
                        "To use the AI fallback, please set the **GEMINI_API_KEY** variable in your backend environment or in a **.env** file in the project root:\n\n"
                        "```env\nGEMINI_API_KEY=your_key_here\n```\n"
                        "You can also click the button below to simulate the AI fallback response."
                    ),
                    'chips': ["Simulate Claude Response", "Back to main menu"]
                })
            except Exception as e:
                return jsonify({
                    'intent': intent,
                    'confidence': score,
                    'error': 'API_CALL_FAILED',
                    'response': (
                        f"⚠️ **API Fallback Failed**: {str(e)}\n\n"
                        "Your Flask backend is running successfully, but the Gemini API call returned an error. Here is a simulated response:\n\n"
                        "\"I apologize, but my Gemini AI core is temporarily unavailable. Please note that I can only help you with your orders only.\""
                    ),
                    'chips': ["Simulate Claude Response", "Back to main menu"]
                })
            
            session_manager.add_message('assistant', response_text)
            return jsonify({
                'intent': intent,
                'confidence': score,
                'response': response_text,
                'chips': chips
            })

@app.route('/api/chat', methods=['POST'])
def chat():
    lang = session_manager.get_language()
    
    data = request.json or {}
    message = data.get('message', '').strip()
    simulate_claude = data.get('simulate_claude', False)
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
        
    # Translate user input to English if not 'en'
    translated_msg = message
    if lang != 'en':
        translated_msg = translation_service.translate_to_english(message)
        
    # Call internal chat logic
    response_val = chat_internal(message, translated_msg, simulate_claude=simulate_claude)
    
    # Unpack Response or tuple
    if isinstance(response_val, tuple):
        res_obj, status_code = response_val
    else:
        res_obj = response_val
        status_code = 200
        
    # Extract JSON data
    if hasattr(res_obj, 'get_json'):
        res_data = res_obj.get_json()
    else:
        res_data = res_obj
        
    # Translate response elements back to target language if not 'en'
    if res_data and lang != 'en':
        if 'response' in res_data and res_data['response']:
            res_data['response'] = translation_service.translate_to_language(res_data['response'], lang)
            
        if 'chips' in res_data and res_data['chips']:
            translated_chips = []
            for chip in res_data['chips']:
                if re.match(r'^ord-\d+$', chip.lower().strip()):
                    translated_chips.append(chip)
                else:
                    translated_chips.append(translation_service.translate_to_language(chip, lang))
            res_data['chips'] = translated_chips
            
        if 'order_card' in res_data and res_data['order_card'] and 'badge' in res_data['order_card']:
            res_data['order_card']['badge'] = translation_service.translate_to_language(res_data['order_card']['badge'], lang)
            
    return jsonify(res_data), status_code

if __name__ == '__main__':
    # Seed MongoDB on startup if it's empty
    try:
        seed_db_if_empty()
    except Exception as e:
        print(f"Warning: Could not seed MongoDB on startup: {e}")
        
    app.run(debug=True, port=5000)