from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import generate_plan
import google.generativeai as genai
import os
from dotenv import load_dotenv
from retriever import retrieve_workouts, retrieve_nutrition

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI(title="AI Fitness & Diet Coach API", description="Personalized meal and workout plans using RAG + Gemini AI")

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "AI Fitness & Diet Coach API is running!",
        "endpoints": {
            "health": "/api/health",
            "generate_plan": "/api/generate-plan",
            "chat": "/chat",
            "test_scenarios": "/api/test-scenarios"
        }
    }

# Add CORS middleware for Next.js frontend
# CORS configuration for production
allowed_origins = [
    "http://localhost:3000",  # Local development
    "https://localhost:3000", # Local HTTPS
]

# Add environment-specific origins
if os.getenv("FRONTEND_URL"):
    allowed_origins.append(os.getenv("FRONTEND_URL"))

# Add your deployed frontend URL
allowed_origins.extend([
    "https://gym-chatbot-404devr.vercel.app",  # Your Vercel deployment
    "https://gym-agent-six.vercel.app",  # Your current Vercel deployment
    "https://*.vercel.app",  # Any Vercel preview deployments
])

# For development, allow all origins
if os.getenv("ENVIRONMENT") == "development":
    allowed_origins = ["*"]

# Allow all origins for production (temporary fix)
allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

class UserData(BaseModel):
    age: int
    weight: float
    height: float
    gender: str
    goal: str
    activity: str
    diet: str
    days: int
    # New fields for flexibility
    living_situation: str = "home"  # home, hostel, apartment, shared
    cooking_ability: str = "can_cook"  # can_cook, no_cooking, limited_cooking
    gym_access: str = "full_gym"  # full_gym, home_gym, no_gym, bodyweight_only
    equipment_available: list = []  # dumbbells, resistance_bands, pull_up_bar, etc.
    dietary_restrictions: list = []  # vegetarian, vegan, lactose_intolerant, etc.
    budget_level: str = "moderate"  # low, moderate, high

class ChatMessage(BaseModel):
    message: str

@app.post("/api/generate-plan")
def get_plan(user: UserData):
    """Generate personalized fitness and diet plan"""
    try:
        plan = generate_plan(user.dict())
        return {"success": True, "plan": plan}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    import os
    
    health_status = {
        "status": "healthy",
        "timestamp": str(os.popen('date').read().strip()) if os.name != 'nt' else "unknown",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "port": os.getenv("PORT", "8000"),
        "indexes_loaded": False,
        "data_directory_exists": os.path.exists("data"),
        "files_in_data": []
    }
    
    try:
        # Check data directory contents
        if os.path.exists("data"):
            health_status["files_in_data"] = os.listdir("data")
        
        # Check if indexes are loaded (with fallback)
        try:
            from retriever import workout_index, nutrition_index
            health_status["indexes_loaded"] = workout_index is not None and nutrition_index is not None
        except Exception as idx_error:
            health_status["index_error"] = str(idx_error)
            health_status["indexes_loaded"] = False
        
        return health_status
        
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        return health_status

@app.post("/chat")
def chat_with_agent(chat_message: ChatMessage):
    """Chat endpoint for conversational interactions with the fitness agent"""
    from cache_manager import ResponseCache
    from fallback_responses import FallbackResponseSystem
    from macros import MacroCalculator
    
    # Initialize systems
    cache = ResponseCache()
    fallback = FallbackResponseSystem()
    calculator = MacroCalculator()
    
    try:
        user_message = chat_message.message.strip()
        
        # Step 1: Check cache first
        cached_response = cache.get_cached_response(user_message)
        if cached_response:
            return {"response": cached_response}
        
        # Step 2: Handle simple greetings without API
        if fallback.is_greeting(user_message):
            response = fallback.get_greeting_response()
            cache.cache_response(user_message, response)
            return {"response": response}
        
        # Step 3: Try macro calculator (no API needed)
        calc_response = calculator.generate_response(user_message)
        if calc_response:
            cache.cache_response(user_message, calc_response)
            return {"response": calc_response}
        
        # Step 4: Check if we should use API or fallback
        should_use_api = _should_use_api(user_message)
        
        if not should_use_api:
            # Use fallback response
            response = fallback.get_fallback_response(user_message)
            cache.cache_response(user_message, response)
            return {"response": response}
        
        # Step 5: Use API with RAG (only when necessary)
        workout_info = retrieve_workouts(user_message)
        nutrition_info = retrieve_nutrition(user_message)
        
        # Only proceed with API if we have relevant RAG data
        if not workout_info and not nutrition_info:
            response = fallback.get_fallback_response(user_message)
            cache.cache_response(user_message, response)
            return {"response": response}
        
        # Create a more focused prompt to reduce token usage
        prompt = f"""
You are a fitness coach. Answer briefly and practically.

Question: {user_message}

Context: {' '.join(workout_info[:1])} {' '.join(nutrition_info[:1])}

Provide a concise, helpful answer (max 150 words).
"""
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        
        # Cache the API response
        api_response = response.text
        cache.cache_response(user_message, api_response)
        
        return {"response": api_response}
        
    except Exception as e:
        error_message = str(e)
        
        # Handle specific API quota exceeded error
        if "429" in error_message and "quota" in error_message.lower():
            friendly_message = """
🤖 **Oops! I've reached my daily limit** 

I'm sorry, but I've used up all my AI credits for today! 😅 

**Please try again in 24 hours** - my credits will refresh and I'll be ready to help you with your fitness journey again!

In the meantime, here are some general tips:
• Stay hydrated 💧
• Get enough sleep (7-9 hours) 😴
• Take a walk or do some light stretching 🚶‍♂️
• Plan your meals ahead 🥗

Thank you for your patience! 🙏
            """.strip()
            return {"response": friendly_message}
        
        # Handle other API errors - use fallback instead of error
        elif "429" in error_message:
            response = fallback.get_fallback_response(user_message)
            return {"response": response}
        
        # Handle general errors with fallback
        else:
            response = fallback.get_fallback_response(user_message)
            return {"response": response}

def _should_use_api(message: str) -> bool:
    """Determine if we should use the API or fallback response"""
    message_lower = message.lower()
    
    # Use API for complex questions that need personalized responses
    api_triggers = [
        'personalized', 'custom', 'specific', 'my situation', 'my case',
        'calculate', 'how much', 'how many', 'what should i',
        'plan for me', 'help me create', 'design a plan'
    ]
    
    # Don't use API for simple questions
    simple_patterns = [
        'what is', 'define', 'explain', 'tell me about',
        'benefits of', 'why', 'how does', 'what are'
    ]
    
    # Check for API triggers
    for trigger in api_triggers:
        if trigger in message_lower:
            return True
    
    # Check for simple patterns
    for pattern in simple_patterns:
        if pattern in message_lower:
            return False
    
    # Default to fallback for shorter messages
    return len(message.split()) > 8

@app.post("/api/test-scenarios")
def test_scenarios():
    """Test different user scenarios"""
    from test_scenarios import hostel_student, home_gym_user, busy_professional
    
    scenarios = {
        "hostel_student": hostel_student,
        "home_gym_user": home_gym_user,
        "busy_professional": busy_professional
    }
    
    results = {}
    for name, scenario in scenarios.items():
        try:
            plan = generate_plan(scenario)
            results[name] = {
                "success": True,
                "scenario": scenario,
                "plan": plan[:500] + "..." if len(plan) > 500 else plan  # Truncate for demo
            }
        except Exception as e:
            results[name] = {
                "success": False,
                "scenario": scenario,
                "error": str(e)
            }
    
    return results

# Run the API:
# uvicorn app:app --reload --port 8000 