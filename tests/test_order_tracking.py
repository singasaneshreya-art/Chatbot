import unittest
import unittest.mock
import sys
import os

# Set testing environment variable before importing app to prevent module-level side effects
os.environ['TESTING'] = 'true'

# Adjust path to import from root directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from services.order_service import (
    get_order,
    extract_order_id,
    create_random_order
)
import services.session_manager as session_manager

@unittest.mock.patch.dict('os.environ', {'TESTING': 'true', 'GEMINI_API_KEY': 'dummy_test_key'})
class TestOrderTracking(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        # Clear mock order customer details before each test
        from services.order_service import MOCK_ORDERS
        for order in MOCK_ORDERS.values():
            order['customer_name'] = None
            order['customer_email'] = None

        # Isolate unit tests from live MongoDB Atlas database
        self.get_db_patcher = unittest.mock.patch('services.order_service.get_db', side_effect=Exception("MongoDB disabled for unit tests"))
        self.get_db_patcher.start()

    def tearDown(self):
        self.get_db_patcher.stop()

    def test_extract_standard_format(self):
        # Test standard uppercase ORD-XXXXXX
        self.assertEqual(extract_order_id("My order ORD-789012 is late"), "ORD-789012")
        # Test lowercase ord-xxxxxx
        self.assertEqual(extract_order_id("track ord-123456"), "ORD-123456")
        # Test mixed case
        self.assertEqual(extract_order_id("OrD-456789 tracking details"), "ORD-456789")

    def test_extract_numeric_fallback(self):
        # Test 6-digit fallback that exists in the database
        self.assertEqual(extract_order_id("order is 789012"), "ORD-789012")
        # Test 6-digit fallback that DOES NOT exist in the database (should return None)
        self.assertIsNone(extract_order_id("order is 999999"))

    def test_extract_invalid(self):
        # Invalid format
        self.assertIsNone(extract_order_id("abc invalid 99"))
        self.assertIsNone(extract_order_id("ORD-123"))
        self.assertIsNone(extract_order_id("12345"))
        self.assertIsNone(extract_order_id(""))
        self.assertIsNone(extract_order_id(None))

    def test_get_order_found(self):
        order = get_order("ORD-123456")
        self.assertIsNotNone(order)
        self.assertEqual(order["status"], "Delivered")
        self.assertEqual(order["item"], "Wireless Headset")

    def test_get_order_not_found(self):
        order = get_order("ORD-000000")
        self.assertIsNone(order)

    def test_create_random_order(self):
        new_id = create_random_order()
        self.assertTrue(new_id.startswith("ORD-"))
        self.assertEqual(len(new_id), 10)
        
        # Verify it exists in store
        order = get_order(new_id)
        self.assertIsNotNone(order)
        self.assertIn(order["status"], ["Processing", "Shipped — In Transit", "Delivered"])
        self.assertIsNotNone(order["item"])
        self.assertIsNotNone(order["price"])

    def test_session_flow_set_get(self):
        # We need to run inside a Flask request context to access session
        with app.test_request_context():
            session_manager.set_flow("order_tracking")
            self.assertEqual(session_manager.get_flow(), "order_tracking")

    def test_session_flow_clear(self):
        with app.test_request_context():
            session_manager.set_flow("order_tracking")
            session_manager.set_flow(None)
            self.assertIsNone(session_manager.get_flow())

    def test_api_chat_initiate_flow(self):
        client = app.test_client()
        with client.session_transaction() as sess:
            sess['flow'] = None
            
        response = client.post('/api/chat', json={'message': 'where is my package'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['intent'], 'order_status')
        self.assertIn('Get My Order ID', data['chips'])
        
        # Verify flow state is set in session
        with client.session_transaction() as sess:
            self.assertEqual(sess.get('flow'), 'order_tracking')

    def test_api_chat_invalid_id(self):
        client = app.test_client()
        with client.session_transaction() as sess:
            sess['flow'] = 'order_tracking'
            
        response = client.post('/api/chat', json={'message': 'invalid123'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("doesn't look like a valid Order ID", data['response'])
        self.assertIn('Get My Order ID', data['chips'])
        
        # Verify still in order_tracking flow
        with client.session_transaction() as sess:
            self.assertEqual(sess.get('flow'), 'order_tracking')

    def test_api_chat_generate_test_order(self):
        client = app.test_client()
        with client.session_transaction() as sess:
            sess['flow'] = 'order_tracking'
            
        response = client.post('/api/chat', json={'message': 'get my order id'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('Order ID Retrieved!', data['response'])
        
        # Verify still in order_tracking flow
        with client.session_transaction() as sess:
            self.assertEqual(sess.get('flow'), 'order_tracking')

    def test_api_chat_valid_order_id(self):
        client = app.test_client()
        with client.session_transaction() as sess:
            sess['flow'] = 'order_tracking'
            
        # Step 1: Send Order ID
        response = client.post('/api/chat', json={'message': 'ORD-123456'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('tell me your full name', data['response'])
        
        with client.session_transaction() as sess:
            self.assertEqual(sess.get('flow'), 'collecting_name')
            self.assertEqual(sess.get('active_order_id'), 'ORD-123456')
            
        # Step 2: Send Name
        response = client.post('/api/chat', json={'message': 'John Doe'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('enter your email address', data['response'])
        
        with client.session_transaction() as sess:
            self.assertEqual(sess.get('flow'), 'collecting_email')
            
        # Step 3: Send Email
        response = client.post('/api/chat', json={'message': 'john.doe@example.com'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('Order ORD-123456', data['response'])
        self.assertIn('Customer: John Doe (john.doe@example.com)', data['response'])
        self.assertIn('Delivered', data['response'])
        self.assertIn('Back to main menu', data['chips'])
        
        # Verify exited collection and tracking flow
        with client.session_transaction() as sess:
            self.assertIsNone(sess.get('flow'))
            self.assertIsNone(sess.get('active_order_id'))

    def test_api_chat_cancel_flow(self):
        client = app.test_client()
        with client.session_transaction() as sess:
            sess['flow'] = 'order_tracking'
            
        response = client.post('/api/chat', json={'message': 'cancel'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['intent'], 'greeting')
        self.assertIn('cancelled', data['response'])
        
        # Verify exited order_tracking flow
        with client.session_transaction() as sess:
            self.assertIsNone(sess.get('flow'))

    def test_api_chat_initiate_refund_flow(self):
        client = app.test_client()
        with client.session_transaction() as sess:
            sess['flow'] = None
            
        response = client.post('/api/chat', json={'message': 'I need a refund'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['intent'], 'refund')
        self.assertIn('Get My Order ID', data['chips'])
        
        # Verify flow state is set to refund
        with client.session_transaction() as sess:
            self.assertEqual(sess.get('flow'), 'refund')

    def test_api_chat_refund_valid_id(self):
        client = app.test_client()
        with client.session_transaction() as sess:
            sess['flow'] = 'refund'
            
        # Step 1: Send Order ID
        response = client.post('/api/chat', json={'message': 'ORD-123456'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('tell me your full name', data['response'])
        
        # Step 2: Send Name
        response = client.post('/api/chat', json={'message': 'John Doe'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('enter your email address', data['response'])
        
        # Step 3: Send Email
        response = client.post('/api/chat', json={'message': 'john.doe@example.com'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['intent'], 'refund')
        self.assertIn('Refund Options for Order ORD-123456', data['response'])
        self.assertIn('Customer: **John Doe** (john.doe@example.com)', data['response'])
        
        # Verify in refund flow
        with client.session_transaction() as sess:
            self.assertEqual(sess.get('flow'), 'refund')

    def test_api_chat_refund_invalid_id(self):
        client = app.test_client()
        with client.session_transaction() as sess:
            sess['flow'] = 'refund'
            
        response = client.post('/api/chat', json={'message': 'invalid123'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['intent'], 'refund')
        self.assertIn("doesn't look like a valid Order ID", data['response'])
        self.assertIn('Get My Order ID', data['chips'])
        
        # Verify still in refund flow
        with client.session_transaction() as sess:
            self.assertEqual(sess.get('flow'), 'refund')

    def test_api_chat_refund_generate_test_order(self):
        client = app.test_client()
        with client.session_transaction() as sess:
            sess['flow'] = 'refund'
            
        response = client.post('/api/chat', json={'message': 'get my order id'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['intent'], 'refund')
        self.assertIn('Order ID Retrieved!', data['response'])
        
        # Verify still in refund flow
        with client.session_transaction() as sess:
            self.assertEqual(sess.get('flow'), 'refund')

    def test_api_chat_refund_cancel_flow(self):
        client = app.test_client()
        with client.session_transaction() as sess:
            sess['flow'] = 'refund'
            
        response = client.post('/api/chat', json={'message': 'cancel'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['intent'], 'greeting')
        self.assertIn('cancelled', data['response'])
        
        # Verify exited refund flow
        with client.session_transaction() as sess:
            self.assertIsNone(sess.get('flow'))

    @unittest.mock.patch('services.gemini_service.call_gemini')
    def test_api_chat_gemini_fallback_mocked(self, mock_call):
        mock_call.return_value = "Mocked Gemini Response!"
        client = app.test_client()
        
        response = client.post('/api/chat', json={'message': 'tell me a joke'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['intent'], 'fallback')
        self.assertEqual(data['response'], "Mocked Gemini Response!")

    @unittest.mock.patch('services.gemini_service.call_gemini')
    def test_api_chat_gemini_missing_key(self, mock_call):
        mock_call.side_effect = ValueError("Gemini API key is not configured.")
        client = app.test_client()
        
        response = client.post('/api/chat', json={'message': 'tell me a joke'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['intent'], 'fallback')
        self.assertEqual(data['error'], 'API_KEY_REQUIRED')
        self.assertIn('Gemini AI API Key Required', data['response'])

    def test_api_chat_generate_test_order_preserves_id(self):
        client = app.test_client()
        with client.session_transaction() as sess:
            sess['flow'] = 'order_tracking'
            
        # First call
        response1 = client.post('/api/chat', json={'message': 'get my order id'})
        data1 = response1.get_json()
        chips1 = data1['chips']
        order_id1 = chips1[0]
        
        # Second call in same session context (using transaction to simulate persistent session)
        with client.session_transaction() as sess:
            self.assertEqual(sess.get('active_order_id'), order_id1)
            
        response2 = client.post('/api/chat', json={'message': 'get my order id'})
        data2 = response2.get_json()
        chips2 = data2['chips']
        order_id2 = chips2[0]
        
        self.assertEqual(order_id1, order_id2)

    def test_api_chat_lookup_clears_active_id(self):
        # Set name and email in mock order so it bypasses collection
        from services.order_service import MOCK_ORDERS
        MOCK_ORDERS['ORD-123456']['customer_name'] = 'John Doe'
        MOCK_ORDERS['ORD-123456']['customer_email'] = 'john@example.com'
        
        client = app.test_client()
        with client.session_transaction() as sess:
            sess['flow'] = 'order_tracking'
            sess['active_order_id'] = 'ORD-123456'
            
        response = client.post('/api/chat', json={'message': 'ORD-123456'})
        self.assertEqual(response.status_code, 200)
        
        with client.session_transaction() as sess:
            self.assertIsNone(sess.get('active_order_id'))

    def test_api_chat_custom_image_url(self):
        # Seed custom order with a Cloudinary image URL
        from services.order_service import MOCK_ORDERS
        MOCK_ORDERS['ORD-123456']['customer_name'] = 'Alice Smith'
        MOCK_ORDERS['ORD-123456']['customer_email'] = 'alice@example.com'
        MOCK_ORDERS['ORD-123456']['image_url'] = 'https://res.cloudinary.com/demo/image/upload/sample.jpg'
        
        client = app.test_client()
        with client.session_transaction() as sess:
            sess['flow'] = 'order_tracking'
            
        response = client.post('/api/chat', json={'message': 'ORD-123456'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        self.assertIn('order_card', data)
        self.assertIsNotNone(data['order_card'])
        self.assertEqual(data['order_card']['image'], 'https://res.cloudinary.com/demo/image/upload/sample.jpg')

if __name__ == '__main__':
    unittest.main()
