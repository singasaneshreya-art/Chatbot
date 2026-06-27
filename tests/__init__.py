import os

# Set global environment variables for the test suite
# This ensures that all tests run in an isolated environment without relying on .env
os.environ['TESTING'] = 'true'
os.environ['GEMINI_API_KEY'] = 'test-dummy-api-key'
