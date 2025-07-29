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
    try:
        user_message = chat_message.message.lower()
        
        # Get relevant information from RAG based on the message
        workout_info = retrieve_workouts(chat_message.message)
        nutrition_info = retrieve_nutrition(chat_message.message)
        
        # Create a context-aware prompt for the chat
        prompt = f"""
You are an expert AI fitness coach and nutritionist. You have access to research-based information about fitness and nutrition.

User Question: {chat_message.message}

Relevant Workout Information:
{' '.join(workout_info[:2])}

Relevant Nutrition Information:
{' '.join(nutrition_info[:2])}

Instructions:
1. Answer the user's question directly and helpfully
2. Use the provided research information when relevant
3. If the user is asking for a personalized plan, ask them for their details (age, weight, height, goal, etc.)
4. Keep responses conversational but informative
5. If you need more information to give a proper answer, ask specific questions
6. Be encouraging and supportive
7. If the question is not fitness/nutrition related, politely redirect to fitness topics

Provide a helpful, accurate response based on the research information available.
"""
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        
        return {"response": response.text}
        
    except Exception as e:
        return {"response": f"I'm sorry, I'm having trouble processing your request right now. Error: {str(e)}"}

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