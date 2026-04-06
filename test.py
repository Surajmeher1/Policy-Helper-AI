import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Test Groq API connection for text simplification
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "llama-3.3-70b-versatile"

def test_groq_api():
    """Test that Groq API is properly configured"""
    if not GROQ_API_KEY:
        print("❌ GROQ_API_KEY not found in .env")
        return False
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }
        
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "user",
                    "content": "Say 'Hello from Groq API' in one sentence."
                }
            ],
            "temperature": 0.5,
            "max_tokens": 100
        }
        
        response = requests.post(GROQ_API_URL, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            reply = result["choices"][0]["message"]["content"]
            print(f"✓ Groq API is working correctly!")
            print(f"✓ Response: {reply}")
            return True
        else:
            print(f"❌ Groq API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Groq API: {e}")
        return False

if __name__ == "__main__":
    print("Testing Groq API configuration...")
    print(f"API URL: {GROQ_API_URL}")
    print(f"Model: {MODEL_NAME}")
    print()
    
    success = test_groq_api()
    
    if success:
        print("\n✓ All tests passed! The application is ready to use.")
    else:
        print("\n❌ Tests failed. Please check your Groq API configuration.")


