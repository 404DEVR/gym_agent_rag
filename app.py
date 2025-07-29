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

# Add CORS middleware for Next.js frontend
# CORS configuration for production
allowed_origins = [
    "http://localhost:3000",  # Local development
    "https://localhost:3000", # Local HTTPS
]

# Add environment-specific origins
if os.getenv("FRONTEND_URL"):
    allowed_origins.append(os.getenv("FRONTEND_URL"))

# For development, allow all origins
if os.getenv("ENVIRONMENT") == "development":
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    try:
        # Check if indexes are loaded
        from retriever import workout_index, nutrition_index
        indexes_loaded = workout_index is not None and nutrition_index is not None
        
        return {
            "status": "healthy",
            "indexes_loaded": indexes_loaded,
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "environment": os.getenv("ENVIRONMENT", "development")
        }

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