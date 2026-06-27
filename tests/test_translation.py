import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add root directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app
from services import translation_service

class TestTranslation(unittest.TestCase):
    def setUp(self):
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()

    def test_local_translation(self):
        # Test translation of welcome message to Spanish
        welcome_en = "👋 Hi! I'm **Support AI** — your AI-powered customer service agent.\n\nI can help you track your **order**, process a **refund**, or check our **support hours**! What can I do for you today?"
        translated = translation_service.translate_to_language(welcome_en, 'es')
        self.assertIn("¡Hola!", translated)
        self.assertIn("reembolso", translated)

    def test_local_translation_chips(self):
        # Test chip translation
        chip_en = "Track my order"
        translated = translation_service.translate_to_language(chip_en, 'hi')
        self.assertEqual(translated, "मेरा ऑर्डर ट्रैक करें")

    @patch('services.translation_service.requests.post')
    def test_dynamic_translation(self, mock_post):
        # Mock Gemini API response for dynamic translation
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'candidates': [{
                'content': {
                    'parts': [{'text': 'Hola'}]
                }
            }]
        }
        mock_post.return_value = mock_response

        # Use a non-local string to trigger dynamic translation
        translated = translation_service.translate_to_language("Hello dynamic", 'es')
        self.assertEqual(translated, "Hola")

    def test_language_endpoint(self):
        # Send POST request to set language to Spanish
        response = self.client.post('/api/language', json={'language': 'es'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['success'])
        self.assertEqual(response.json['language'], 'es')

    def test_reverse_local_translation(self):
        # Verify that we can translate "मेरा ऑर्डर ट्रैक करें" back to "Track my order" locally
        translated_back = translation_service.translate_to_english("मेरा ऑर्डर ट्रैक करें")
        self.assertEqual(translated_back, "Track my order")

    def test_dynamic_hours_translation(self):
        # Test translation of arbitrary weekday hours in Spanish
        translated = translation_service.translate_to_language("Mon-Fri: 8 AM - 8 PM", "es")
        self.assertEqual(translated, "Lun-Vie: 8 AM - 8 PM")
        
        # Test translation of arbitrary Saturday hours in German (24h conversion)
        translated_sat = translation_service.translate_to_language("Sat: 9 AM - 5 PM", "de")
        self.assertEqual(translated_sat, "Sa: 9:00 Uhr - 17:00 Uhr")
        
        # Test translation of arbitrary Sunday hours in Japanese (full-width colon)
        translated_sun = translation_service.translate_to_language("Sun: Closed", "ja")
        self.assertEqual(translated_sun, "日：休業日")

        # Test translation of weekday hours in Hindi
        translated_hi = translation_service.translate_to_language("Mon-Fri: 9 AM - 6 PM", "hi")
        self.assertEqual(translated_hi, "सोम-शुक्र: सुबह 9 बजे – शाम 6 बजे")

    def test_dynamic_templates_translation(self):
        # 1. Test "I found Order {order_id}..." in Hindi
        text = "I found Order **ORD-123456**. To retrieve your order details, please tell me your full name."
        translated = translation_service.translate_to_language(text, "hi")
        self.assertEqual(translated, "मुझे ऑर्डर **ORD-123456** मिला। आपके ऑर्डर का विवरण प्राप्त करने के लिए, कृपया मुझे अपना पूरा नाम बताएं।")

        # 2. Test "Thanks, **{user_name}**!..." in Spanish
        text = "Thanks, **Alex**! Now, please enter your email address so we can associate it with this order."
        translated = translation_service.translate_to_language(text, "es")
        self.assertEqual(translated, "¡Gracias, **Alex**! Ahora, por favor ingresa tu dirección de correo electrónico para que podamos asociarla con este pedido.")

        # 3. Test "📋 **Order ID Retrieved!**..." in Japanese
        text = "📋 **Order ID Retrieved!**\n\nYour active Order ID is: `ORD-999888`\n\nYou can now copy and paste this ID or type it to track this order."
        translated = translation_service.translate_to_language(text, "ja")
        self.assertIn("注文IDを取得しました", translated)
        self.assertIn("ORD-999888", translated)

if __name__ == '__main__':
    unittest.main()
