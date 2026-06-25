import os
import random
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

from services.classifier import classify_intent
import services.gemini_service as gemini_service
import services.session_manager as session_manager
import services.order_service as order_service

load_dotenv()

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
    session_manager.clear_history()
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json or {}
    message = data.get('message', '').strip()
    simulate_claude = data.get('simulate_claude', False)
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400

    # Record user message in history
    session_manager.add_message('user', message)
    
    cleaned_msg = message.lower().strip()
    flow = session_manager.get_flow()
    
    # 1. Check for cancel keywords to exit active flow
    if cleaned_msg in ['cancel', 'back', 'menu', 'exit', 'back to main menu', 'back to menu']:
        session_manager.set_flow(None)
        response_text = "Action cancelled. Back to the main menu!"
        chips = ["Track my order", "I need a refund", "What are your hours?"]
        session_manager.add_message('assistant', response_text)
        return jsonify({
            'intent': 'greeting',
            'confidence': 1.0,
            'response': response_text,
            'chips': chips
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

    # 3. Check if a valid Order ID is in the message
    extracted_id = order_service.extract_order_id(message)
    if extracted_id:
        order = order_service.get_order(extracted_id)
        if order:
            if flow == 'refund':
                session_manager.set_flow(None) # exit flow
                session_manager.set_active_order_id(None) # clear active order ID since it's completed
                response_text = (
                    f"💳 **Refund Initiated for Order {order['id']}**\n\n"
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
                eta_line = f"ETA:     ~{order['eta']}\n" if order['eta'] else ""
                response_text = (
                    f"📦 **Order {order['id']}**\n\n"
                    f"Status:  {order['status']}\n"
                    f"Item:    1× {order['item']}\n"
                    f"Price:   {order['price']}\n"
                    f"{eta_line}"
                )
                chips = ["Back to main menu"]
                session_manager.add_message('assistant', response_text)
                return jsonify({
                    'intent': 'order_status',
                    'confidence': 1.0,
                    'response': response_text,
                    'chips': chips
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
                "I understand your query! I am **NexSupport**, your AI fallback. "
                "I can assist with **billing**, **refunds**, or help guide you in building your "
                "**custom NLP classifier**. Let me know how I can assist!"
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
                        "\"Hello! I am **NexSupport**. I apologize, but my Gemini AI core is temporarily unavailable. Please make sure your API key is valid and you have internet access!\""
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
