#!/usr/bin/env python3
"""
Test script to show what the terminal output looks like when the chatbot hits the Python API
Run this to see the detailed logging output
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import chat_with_agent, ChatMessage
import time

def test_api_responses():
    """Test different types of messages to show terminal output"""
    
    print("🧪 TESTING FITNESS RAG AGENT API RESPONSES")
    print("=" * 80)
    print("This shows what you'll see in the terminal when your chatbot hits the Python API\n")
    
    # Test cases that represent typical user interactions
    test_messages = [
        "Hi there!",  # Greeting
        "I want to lose weight",  # Simple goal
        "I'm 25 years old, weigh 70kg, 175cm tall, male, and want to build muscle",  # Personal details
        "What should I eat for breakfast?",  # Nutrition question
        "Give me a workout plan",  # Workout request
        "I'm a student living in a hostel with no cooking facilities, help me with nutrition"  # Complex scenario
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n🧪 TEST CASE {i}/{len(test_messages)}")
        print(f"Simulating user message: '{message}'")
        print("-" * 60)
        
        try:
            # Create ChatMessage object
            chat_msg = ChatMessage(message=message)
            
            # Call the chat function (this will show all the logging)
            response = chat_with_agent(chat_msg)
            
            print(f"✅ Final API Response Length: {len(response['response'])} characters")
            
        except Exception as e:
            print(f"❌ Error occurred: {e}")
        
        print("\n" + "=" * 80)
        
        # Small delay to make output readable
        time.sleep(0.5)

if __name__ == "__main__":
    print("Starting API response test...")
    print("This will show you exactly what appears in the terminal when your chatbot hits the Python API\n")
    
    test_api_responses()
    
    print("\n🎉 Test completed!")
    print("\nTo run the actual API server, use:")
    print("cd fitness_rag_agent")
    print("python -m uvicorn app:app --reload --port 8000")
    print("\nThen your Next.js chatbot will hit this API and you'll see similar output in the terminal.")