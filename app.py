from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import generate_plan
import google.generativeai as genai
import os
import re
from datetime import datetime
from dotenv import load_dotenv
from retriever import retrieve_workouts, retrieve_nutrition

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Old extraction functions removed - now using AI-generated JSON directly

def _extract_user_context(user_message):
    """Extract user context from message to personalize nutrition planning"""
    message_lower = user_message.lower()
    
    # Detect living situation
    living_situation = "home"  # default
    if any(word in message_lower for word in ["hostel", "dorm", "dormitory", "college", "university"]):
        living_situation = "hostel"
    elif any(word in message_lower for word in ["apartment", "flat", "shared", "roommate"]):
        living_situation = "apartment"
    
    # Detect cooking ability
    cooking_ability = "can_cook"  # default
    if any(phrase in message_lower for phrase in [
        "can't cook", "cannot cook", "don't cook", "no cooking", "hostel", 
        "no kitchen", "no stove", "student", "busy", "no time to cook"
    ]):
        cooking_ability = "no_cooking"
    elif any(phrase in message_lower for phrase in [
        "limited cooking", "basic cooking", "simple meals", "quick meals",
        "minimal cooking", "easy recipes"
    ]):
        cooking_ability = "limited_cooking"
    
    # Detect time availability
    time_availability = "moderate"  # default
    if any(phrase in message_lower for phrase in [
        "very busy", "no time", "hectic schedule", "working professional",
        "long hours", "tight schedule"
    ]):
        time_availability = "low"
    elif any(phrase in message_lower for phrase in [
        "plenty of time", "flexible schedule", "student", "free time"
    ]):
        time_availability = "high"
    
    # Detect budget level
    budget_level = "moderate"  # default
    if any(phrase in message_lower for phrase in [
        "low budget", "cheap", "affordable", "student budget", "tight budget",
        "money is tight", "budget-friendly"
    ]):
        budget_level = "low"
    elif any(phrase in message_lower for phrase in [
        "high budget", "premium", "expensive", "money is not an issue"
    ]):
        budget_level = "high"
    
    return {
        "living_situation": living_situation,
        "cooking_ability": cooking_ability,
        "time_availability": time_availability,
        "budget_level": budget_level
    }

app = FastAPI(title="AI Fitness & Diet Coach API", description="Personalized meal and workout plans using RAG + Gemini AI")

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "AI Fitness & Diet Coach API is running!",
        "endpoints": {
            "health": "/api/health",
            "generate_plan": "/api/generate-plan",
            "meal_plan": "/meal-plan",
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

class MealPlanRequest(BaseModel):
    goal: str
    ingredients: list
    dietary_restrictions: list = []
    target_calories: int = None

class WorkoutPlanAction(BaseModel):
    user_id: str
    action: str  # "update" or "add"
    workout_plan: dict

@app.post("/api/generate-plan")
def get_plan(user: UserData):
    """Generate personalized fitness and diet plan"""
    try:
        plan = generate_plan(user.dict())
        return {"success": True, "plan": plan}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/check-existing-plans")
def check_existing_plans(request: dict):
    """Check if user has existing workout plans and return options"""
    try:
        user_id = request.get("user_id")
        if not user_id:
            return {"success": False, "error": "User ID required"}
        
        existing_plans = check_existing_workout_plans(user_id)
        
        if existing_plans:
            return {
                "success": True,
                "has_existing_plans": True,
                "existing_plans": existing_plans,
                "message": f"Found {len(existing_plans)} existing workout plans. Would you like to update your current plan or add a new one?"
            }
        else:
            return {
                "success": True,
                "has_existing_plans": False,
                "existing_plans": [],
                "message": "No existing workout plans found. Creating your first plan!"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/save-workout-plan")
def save_workout_plan_endpoint(request: WorkoutPlanAction):
    """Save workout plan with specified action (update or add)"""
    try:
        user_id = request.user_id
        action = request.action  # "update" or "add"
        workout_plan = request.workout_plan
        
        # Try Supabase first
        if supabase:
            success = store_workout_plan_in_supabase(user_id, workout_plan, action)
        else:
            success = store_workout_plan_in_fallback(user_id, workout_plan, action)
        
        if success:
            action_text = "updated" if action == "update" else "added"
            return {
                "success": True,
                "message": f"Workout plan {action_text} successfully!",
                "action": action
            }
        else:
            return {"success": False, "error": "Failed to save workout plan"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/debug-supabase/{user_id}")
def debug_supabase_connection(user_id: str):
    """Debug endpoint to check Supabase connection and data"""
    try:
        if not supabase:
            return {"error": "Supabase not configured"}
        
        # Test basic connection
        result = supabase.table('workout_plans').select('*').limit(5).execute()
        
        # Get all user IDs
        all_plans = supabase.table('workout_plans').select('user_id, goal, created_at').execute()
        unique_users = list(set(plan.get('user_id') for plan in all_plans.data)) if all_plans.data else []
        
        # Check specific user
        user_plans = supabase.table('workout_plans').select('*').eq('user_id', user_id).execute()
        
        return {
            "supabase_connected": True,
            "total_plans": len(all_plans.data) if all_plans.data else 0,
            "unique_users": unique_users,
            "user_plans_count": len(user_plans.data) if user_plans.data else 0,
            "user_plans": user_plans.data,
            "sample_plans": result.data[:3] if result.data else []
        }
        
    except Exception as e:
        return {"error": str(e), "supabase_connected": False}

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

# Performance test endpoint removed - was using unused cache_manager

# Supabase configuration
try:
    from supabase import create_client, Client
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    # Use service key for backend operations to bypass RLS
    service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if supabase_url and service_key and service_key != "your_service_key_here":
        # Use service key for backend operations (bypasses RLS)
        supabase: Client = create_client(supabase_url, service_key)
    elif supabase_url and supabase_key and supabase_url != "your_supabase_url_here":
        # Fallback to anon key if service key not available
        supabase: Client = create_client(supabase_url, supabase_key)
    else:
        supabase = None
    
except ImportError:
    supabase = None
except Exception as e:
    supabase = None

# Fallback in-memory storage when Supabase is not available (global persistent)
fallback_profiles = {}

# Add a simple file-based persistence for fallback storage
import json
import os

FALLBACK_STORAGE_FILE = "fallback_profiles.json"

def load_fallback_profiles():
    """Load fallback profiles from file"""
    global fallback_profiles
    try:
        if os.path.exists(FALLBACK_STORAGE_FILE):
            with open(FALLBACK_STORAGE_FILE, 'r') as f:
                fallback_profiles = json.load(f)
    except Exception as e:
        fallback_profiles = {}

def save_fallback_profiles():
    """Save fallback profiles to file"""
    try:
        with open(FALLBACK_STORAGE_FILE, 'w') as f:
            json.dump(fallback_profiles, f)
    except Exception as e:
        pass

# Load existing profiles on startup
load_fallback_profiles()

# ========================================
# COMPREHENSIVE TOOL-BASED CHATBOT ARCHITECTURE
# ========================================

class ChatbotTools:
    """Complete tool registry for all chatbot functions"""
    
    def __init__(self):
        self.tools = {
            # Profile Management Tools
            "get_user_profile": {
                "function": self.get_user_profile_tool,
                "description": "Retrieve user's stored profile information",
                "parameters": ["user_id"]
            },
            "update_user_profile": {
                "function": self.update_user_profile_tool,
                "description": "Update user's profile with new information",
                "parameters": ["user_id", "profile_data"]
            },
            "check_profile_completeness": {
                "function": self.check_profile_completeness_tool,
                "description": "Check if user profile has required fields for plan generation",
                "parameters": ["user_profile"]
            },
            
            # Fitness Calculation Tools
            "calculate_macros": {
                "function": self.calculate_macros_tool,
                "description": "Calculate BMR, TDEE, and macro breakdown for a user",
                "parameters": ["weight", "height", "age", "gender", "goal", "activity"]
            },
            
            # RAG Knowledge Tools
            "get_workout_suggestions": {
                "function": self.get_workout_suggestions_tool,
                "description": "Get workout suggestions using RAG knowledge base",
                "parameters": ["query", "user_profile"]
            },
            "get_nutrition_suggestions": {
                "function": self.get_nutrition_suggestions_tool,
                "description": "Get nutrition suggestions using RAG knowledge base",
                "parameters": ["query", "user_profile"]
            },
            
            # Plan Generation Tools
            "generate_meal_plan": {
                "function": self.generate_meal_plan_tool,
                "description": "Generate detailed meal plan based on cooking ability and calories",
                "parameters": ["user_profile", "calories", "protein"]
            },
            "generate_full_plan": {
                "function": self.generate_full_plan_tool,
                "description": "Generate comprehensive fitness and nutrition plan",
                "parameters": ["user_profile"]
            },
            "generate_workout_json": {
                "function": self.generate_workout_json_tool,
                "description": "Generate structured workout plan JSON",
                "parameters": ["user_profile"]
            },
            
            # Conversation Tools
            "generate_greeting": {
                "function": self.generate_greeting_tool,
                "description": "Generate a friendly greeting response",
                "parameters": []
            },
            "generate_conversational_response": {
                "function": self.generate_conversational_response_tool,
                "description": "Generate natural conversational response for general topics",
                "parameters": ["user_message", "context"]
            },
            "answer_fitness_question": {
                "function": self.answer_fitness_question_tool,
                "description": "Answer general fitness/nutrition questions using AI and RAG",
                "parameters": ["question", "user_profile"]
            },
            
            # Stored Workout Plan Tools
            "get_stored_workout_plans": {
                "function": self.get_stored_workout_plans_tool,
                "description": "Retrieve user's stored workout plans from Supabase",
                "parameters": ["user_id"]
            },
            "answer_workout_plan_question": {
                "function": self.answer_workout_plan_question_tool,
                "description": "Answer questions about user's stored workout plans",
                "parameters": ["question", "user_id", "user_profile"]
            },
            
            # Stored Meal Plan Tools
            "get_stored_meal_plans": {
                "function": self.get_stored_meal_plans_tool,
                "description": "Retrieve user's stored meal plans from Supabase",
                "parameters": ["user_id"]
            },
            "answer_meal_plan_question": {
                "function": self.answer_meal_plan_question_tool,
                "description": "Answer questions about user's stored meal plans",
                "parameters": ["question", "user_id", "user_profile"]
            },
            
            # Smart Data-Aware Tools
            "get_next_workout": {
                "function": self.get_next_workout_tool,
                "description": "Get user's next workout based on their stored plans and current day",
                "parameters": ["user_id", "query_type"]
            },
            "get_next_meal": {
                "function": self.get_next_meal_tool,
                "description": "Get user's next meal based on current time and meal plans",
                "parameters": ["user_id", "query_type"]
            },
            "get_meal_preparation": {
                "function": self.get_meal_preparation_tool,
                "description": "Get meal preparation instructions for current meal",
                "parameters": ["user_id", "query_type"]
            },
            "get_specific_meal": {
                "function": self.get_specific_meal_tool,
                "description": "Get specific meal details (breakfast, lunch, dinner, snack)",
                "parameters": ["user_id", "meal_type"]
            },
            "get_workout_schedule": {
                "function": self.get_workout_schedule_tool,
                "description": "Get user's complete workout schedule and timing",
                "parameters": ["user_id"]
            }
        }
    
    def calculate_macros_tool(self, weight, height, age, gender, goal, activity):
        """Tool wrapper for macro calculations"""
        try:
            from macros import calculate_macros
            macros = calculate_macros(weight, height, age, gender, goal, activity)
            return {
                "success": True,
                "data": macros,
                "message": f"Calculated macros: {macros['calories']} calories, {macros['protein']}g protein"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_workout_suggestions_tool(self, user_profile):
        """Tool wrapper for workout suggestions using RAG"""
        try:
            from agent import build_workout_query
            from retriever import retrieve_workouts
            
            workout_query = build_workout_query(user_profile)
            workout_suggestions = retrieve_workouts(workout_query)
            
            return {
                "success": True,
                "data": workout_suggestions[:3],  # Top 3 suggestions
                "message": f"Found {len(workout_suggestions)} workout suggestions"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_nutrition_suggestions_tool(self, user_profile):
        """Tool wrapper for nutrition suggestions using RAG"""
        try:
            from agent import build_nutrition_query
            from retriever import retrieve_nutrition
            
            nutrition_query = build_nutrition_query(user_profile)
            nutrition_suggestions = retrieve_nutrition(nutrition_query)
            
            return {
                "success": True,
                "data": nutrition_suggestions[:3],  # Top 3 suggestions
                "message": f"Found {len(nutrition_suggestions)} nutrition suggestions"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_meal_plan_tool(self, user_profile, calories=None, protein=None):
        """Tool wrapper for meal plan generation"""
        try:
            from nutrition_planner import NutritionPlanner
            from macros import calculate_macros
            
            # Calculate macros if not provided
            if calories is None or protein is None:
                macros = calculate_macros(
                    user_profile.get('weight', 70),
                    user_profile.get('height', 175), 
                    user_profile.get('age', 25),
                    user_profile.get('gender', 'male'),
                    user_profile.get('goal', 'general_fitness'),
                    user_profile.get('activity', 'moderate')
                )
                calories = macros['calories']
                protein = macros['protein']
            
            nutrition_planner = NutritionPlanner()
            cooking_ability = user_profile.get('cooking_ability', 'can_cook')
            living_situation = user_profile.get('living_situation', 'home')
            
            if cooking_ability == 'no_cooking' or living_situation == 'hostel':
                meal_plan = nutrition_planner.generate_no_cook_meal_plan(calories, protein)
            elif cooking_ability == 'limited_cooking':
                meal_plan = nutrition_planner.generate_limited_cooking_plan(calories, protein)
            else:
                meal_plan = nutrition_planner.generate_full_cooking_plan(calories, protein)
            
            return {
                "success": True,
                "data": meal_plan,
                "message": f"Generated {cooking_ability} meal plan for {calories} calories, {protein}g protein"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_full_plan_tool(self, user_profile):
        """Tool wrapper for full plan generation"""
        try:
            from agent import generate_plan
            plan = generate_plan(user_profile)
            
            return {
                "success": True,
                "data": plan,
                "message": "Generated comprehensive fitness and nutrition plan"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_workout_json_tool(self, user_profile):
        """Tool wrapper for workout JSON generation"""
        try:
            workout_plan_json = generate_workout_plan_json(user_profile)
            
            return {
                "success": True,
                "data": workout_plan_json,
                "message": "Generated structured workout plan JSON"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Profile Management Tool Implementations
    def get_user_profile_tool(self, user_id):
        """Tool to retrieve user profile"""
        try:
            profile = get_user_profile(user_id)
            return {
                "success": True,
                "data": profile,
                "message": f"Retrieved profile for user {user_id}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_user_profile_tool(self, user_id, profile_data):
        """Tool to update user profile"""
        try:
            success = update_user_profile(user_id, profile_data)
            if success:
                return {
                    "success": True,
                    "data": profile_data,
                    "message": f"Updated profile for user {user_id}"
                }
            else:
                return {"success": False, "error": "Failed to update profile"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def check_profile_completeness_tool(self, user_profile):
        """Tool to check profile completeness"""
        try:
            missing_fields = check_profile_completeness(user_profile)
            return {
                "success": True,
                "data": {
                    "missing_fields": missing_fields,
                    "is_complete": len(missing_fields) == 0
                },
                "message": f"Profile completeness check: {len(missing_fields)} missing fields"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # RAG Knowledge Tool Implementations
    def get_workout_suggestions_tool(self, query, user_profile=None):
        """Tool to get workout suggestions using RAG"""
        try:
            if user_profile:
                from agent import build_workout_query
                workout_query = build_workout_query(user_profile)
            else:
                workout_query = query
            
            workout_suggestions = retrieve_workouts(workout_query)
            
            return {
                "success": True,
                "data": workout_suggestions[:3],
                "message": f"Found {len(workout_suggestions)} workout suggestions"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_nutrition_suggestions_tool(self, query, user_profile=None):
        """Tool to get nutrition suggestions using RAG"""
        try:
            if user_profile:
                from agent import build_nutrition_query
                nutrition_query = build_nutrition_query(user_profile)
            else:
                nutrition_query = query
            
            nutrition_suggestions = retrieve_nutrition(nutrition_query)
            
            return {
                "success": True,
                "data": nutrition_suggestions[:3],
                "message": f"Found {len(nutrition_suggestions)} nutrition suggestions"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Conversation Tool Implementations
    def generate_greeting_tool(self):
        """Tool to generate greeting"""
        greetings = [
            "Hi there! I'm your AI fitness and nutrition coach. How can I help you today?",
            "Hello! Ready to work on your fitness goals? What can I do for you?",
            "Hey! I'm here to help with your workouts and nutrition. What's on your mind?",
            "Hi! Whether you need a workout plan, nutrition advice, or just have questions, I'm here to help!"
        ]
        import random
        return {
            "success": True,
            "data": random.choice(greetings),
            "message": "Generated greeting"
        }
    
    def generate_conversational_response_tool(self, user_message, context=""):
        """Tool to generate conversational responses"""
        try:
            prompt = f"""
You are a friendly fitness assistant. The user said: "{user_message}"

Context: {context}

Respond naturally and helpfully. If it's fitness-related, provide brief advice. If it's not fitness-related, acknowledge it and gently guide back to fitness topics. Keep it conversational and under 100 words.
"""
            
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=200,
                    temperature=0.8,
                )
            )
            
            return {
                "success": True,
                "data": response.text.strip(),
                "message": "Generated conversational response"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def answer_fitness_question_tool(self, question, user_profile=None):
        """Tool to answer fitness questions using AI and RAG"""
        try:
            # Get RAG context
            workout_info = retrieve_workouts(question)[:2]
            nutrition_info = retrieve_nutrition(question)[:2]
            
            # Build context-aware prompt
            context = f"Research Context: {' '.join(workout_info)} {' '.join(nutrition_info)}"
            if user_profile:
                context += f"\nUser Profile: {user_profile}"
            
            prompt = f"""
You are an expert fitness coach and nutritionist. Answer this question with detailed, research-backed information.

Question: {question}

{context}

Provide a comprehensive, actionable answer. Include specific tips, examples, and practical advice. Keep it informative but concise.
"""
            
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=800,
                    temperature=0.7,
                )
            )
            
            return {
                "success": True,
                "data": response.text.strip(),
                "message": "Answered fitness question"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Stored Workout Plan Tool Implementations
    def get_stored_workout_plans_tool(self, user_id):
        """Tool to retrieve user's stored workout plans from Supabase or fallback storage"""
        try:
            if supabase:
                # Query Supabase for user's workout plans
                result = supabase.table('workout_plans').select('*').eq('user_id', user_id).execute()
                
                if result.data:
                    return {
                        "success": True,
                        "data": result.data,
                        "message": f"Found {len(result.data)} stored workout plans"
                    }
                else:
                    return {
                        "success": True,
                        "data": [],
                        "message": "No stored workout plans found in Supabase"
                    }
            else:
                # Fallback: Check fallback storage for workout plans
                global fallback_profiles
                if user_id in fallback_profiles and 'workout_plans' in fallback_profiles[user_id]:
                    workout_plans = fallback_profiles[user_id]['workout_plans']
                    return {
                        "success": True,
                        "data": workout_plans,
                        "message": f"Found {len(workout_plans)} stored workout plans in fallback storage"
                    }
                else:
                    return {
                        "success": True,
                        "data": [],
                        "message": "No stored workout plans found. Generate a new plan to get started!"
                    }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def answer_workout_plan_question_tool(self, question, user_id, user_profile=None):
        """Tool to answer questions about user's stored workout plans"""
        try:
            # First, get the user's stored workout plans
            stored_plans_result = self.get_stored_workout_plans_tool(user_id)
            
            if not stored_plans_result["success"]:
                return {
                    "success": True,
                    "data": "I don't have access to your stored workout plans right now. You can generate a new plan by asking me to create one!",
                    "message": "No stored plans available"
                }
            
            stored_plans = stored_plans_result["data"]
            
            if not stored_plans:
                return {
                    "success": True,
                    "data": "You don't have any saved workout plans yet. Would you like me to generate a personalized workout plan for you?",
                    "message": "No stored plans found"
                }
            
            # Format the stored plans for AI analysis
            plans_context = ""
            for i, plan in enumerate(stored_plans, 1):
                plans_context += f"\nWorkout Plan {i}:\n"
                plans_context += f"Goal: {plan.get('goal', 'Not specified')}\n"
                plans_context += f"Days per week: {plan.get('days', 'Not specified')}\n"
                plans_context += f"Split: {plan.get('split', [])}\n"
                
                # Format exercises
                exercises = plan.get('exercises', [])
                for day_plan in exercises:
                    day_name = day_plan.get('day_name', day_plan.get('day', 'Unknown'))
                    plans_context += f"\n{day_name}:\n"
                    for exercise in day_plan.get('exercises', []):
                        plans_context += f"- {exercise.get('name', 'Unknown exercise')}: {exercise.get('sets', '?')} sets x {exercise.get('reps', '?')} reps\n"
                
                plans_context += f"Created: {plan.get('created_at', 'Unknown date')}\n"
                plans_context += "-" * 50 + "\n"
            
            # Create AI prompt to answer the question about stored plans
            prompt = f"""
You are a fitness coach helping a user understand their stored workout plans. Answer their question based on their saved workout data.

User Question: "{question}"

User's Stored Workout Plans:
{plans_context}

User Profile: {user_profile if user_profile else 'Not available'}

Instructions:
- Answer the user's question specifically about their stored workout plans
- Be helpful and specific, referencing their actual saved workouts
- If they ask about exercises, sets, reps, or schedule, provide exact details from their plans
- If they ask about progress or modifications, give practical advice
- If the question can't be answered from their stored data, let them know and offer to help in other ways

Provide a clear, helpful response based on their actual stored workout data.
"""
            
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=800,
                    temperature=0.7,
                )
            )
            
            return {
                "success": True,
                "data": response.text.strip(),
                "message": "Answered question about stored workout plans"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Stored Meal Plan Tool Implementations
    def get_stored_meal_plans_tool(self, user_id):
        """Tool to retrieve user's stored meal plans from Supabase"""
        try:
            if supabase:
                # Query Supabase for user's meal plans
                result = supabase.table('meal_plans').select('*').eq('user_id', user_id).execute()
                
                if result.data:
                    return {
                        "success": True,
                        "data": result.data,
                        "message": f"Found {len(result.data)} stored meal plans"
                    }
                else:
                    return {
                        "success": True,
                        "data": [],
                        "message": "No stored meal plans found"
                    }
            else:
                return {
                    "success": False,
                    "error": "Supabase not connected - cannot retrieve stored meal plans"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def answer_meal_plan_question_tool(self, question, user_id, user_profile=None):
        """Tool to answer questions about user's stored meal plans"""
        try:
            # First, get the user's stored meal plans
            stored_plans_result = self.get_stored_meal_plans_tool(user_id)
            
            if not stored_plans_result["success"]:
                return {
                    "success": True,
                    "data": "I don't have access to your stored meal plans right now. You can generate a new meal plan by asking me to create one!",
                    "message": "No stored meal plans available"
                }
            
            stored_plans = stored_plans_result["data"]
            
            if not stored_plans:
                return {
                    "success": True,
                    "data": "You don't have any saved meal plans yet. Would you like me to generate a personalized meal plan for you?",
                    "message": "No stored meal plans found"
                }
            
            # Format the stored meal plans for AI analysis
            plans_context = ""
            for i, plan in enumerate(stored_plans, 1):
                plans_context += f"\nMeal Plan {i}:\n"
                plans_context += f"Goal: {plan.get('goal', 'Not specified')}\n"
                plans_context += f"Target Calories: {plan.get('target_calories', 'Not specified')}\n"
                plans_context += f"Dietary Restrictions: {plan.get('dietary_restrictions', [])}\n"
                
                # Format meals
                meals = plan.get('meals', [])
                if isinstance(meals, list):
                    for meal in meals:
                        if isinstance(meal, dict):
                            meal_name = meal.get('name', meal.get('type', 'Unknown meal'))
                            plans_context += f"\n{meal_name}:\n"
                            plans_context += f"- Calories: {meal.get('calories', '?')} kcal\n"
                            plans_context += f"- Protein: {meal.get('protein', '?')}g\n"
                            plans_context += f"- Carbs: {meal.get('carbs', '?')}g\n"
                            plans_context += f"- Fat: {meal.get('fat', '?')}g\n"
                            
                            # Add ingredients if available
                            ingredients = meal.get('ingredients', [])
                            if ingredients:
                                plans_context += f"- Ingredients: {', '.join(ingredients)}\n"
                            
                            # Add preparation steps if available
                            steps = meal.get('steps', [])
                            if steps:
                                plans_context += f"- Preparation: {'; '.join(steps)}\n"
                
                plans_context += f"Created: {plan.get('created_at', 'Unknown date')}\n"
                plans_context += "-" * 50 + "\n"
            
            # Create AI prompt to answer the question about stored meal plans
            prompt = f"""
You are a nutrition coach helping a user understand their stored meal plans. Answer their question based on their saved meal plan data.

User Question: "{question}"

User's Stored Meal Plans:
{plans_context}

User Profile: {user_profile if user_profile else 'Not available'}

Instructions:
- Answer the user's question specifically about their stored meal plans
- Be helpful and specific, referencing their actual saved meal plans
- If they ask about calories, macros, ingredients, or preparation, provide exact details from their plans
- If they ask about nutrition advice or modifications, give practical suggestions
- If they ask about meal timing or portions, reference their stored data
- If the question can't be answered from their stored data, let them know and offer to help in other ways

Provide a clear, helpful response based on their actual stored meal plan data.
"""
            
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=800,
                    temperature=0.7,
                )
            )
            
            return {
                "success": True,
                "data": response.text.strip(),
                "message": "Answered question about stored meal plans"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Smart Data-Aware Tool Implementations
    def get_next_workout_tool(self, user_id, query_type="today"):
        """Get user's next workout based on their stored plans and current day"""
        try:
            from datetime import datetime, timedelta
            import calendar
            
            # Get user's stored workout plans
            stored_plans_result = self.get_stored_workout_plans_tool(user_id)
            
            if not stored_plans_result["success"] or not stored_plans_result["data"]:
                return {
                    "success": True,
                    "data": "You don't have any saved workout plans yet. Would you like me to create a personalized workout plan for you?",
                    "message": "No workout plans found"
                }
            
            # Get the most recent workout plan
            workout_plans = stored_plans_result["data"]
            latest_plan = max(workout_plans, key=lambda x: x.get('created_at', ''))
            
            # Get current day info
            today = datetime.now()
            if query_type == "tomorrow":
                target_date = today + timedelta(days=1)
            else:
                target_date = today
            
            day_name = calendar.day_name[target_date.weekday()].lower()
            day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            
            # Parse the workout plan exercises
            exercises = latest_plan.get('exercises', [])
            if isinstance(exercises, str):
                import json
                try:
                    exercises = json.loads(exercises)
                except:
                    exercises = []
            
            # Find today's workout
            today_workout = None
            for day_plan in exercises:
                if isinstance(day_plan, dict):
                    day_plan_name = day_plan.get('day_name', '').lower()
                    day_plan_day = day_plan.get('day', '').lower()
                    
                    # Match by day name or day
                    if (day_name in day_plan_name or 
                        day_plan_name in day_name or
                        day_name in day_plan_day or
                        day_plan_day in day_name):
                        today_workout = day_plan
                        break
            
            # If no specific day match, use day index
            if not today_workout and exercises:
                day_index = target_date.weekday()
                if day_index < len(exercises):
                    today_workout = exercises[day_index]
            
            if today_workout:
                workout_exercises = today_workout.get('exercises', [])
                day_display_name = today_workout.get('day_name', f"{target_date.strftime('%A')}")
                
                response_text = f"🏋️ **Your {query_type.title()} Workout - {day_display_name}**\n\n"
                
                if workout_exercises:
                    response_text += f"📋 **{len(workout_exercises)} Exercises Planned:**\n\n"
                    
                    for i, exercise in enumerate(workout_exercises, 1):
                        if isinstance(exercise, dict):
                            name = exercise.get('name', 'Unknown Exercise')
                            sets = exercise.get('sets', '?')
                            reps = exercise.get('reps', '?')
                            rest = exercise.get('rest', '60-90s')
                            
                            response_text += f"**{i}. {name}**\n"
                            response_text += f"   • Sets: {sets} | Reps: {reps}\n"
                            response_text += f"   • Rest: {rest}\n"
                            
                            # Add muscle groups if available
                            muscle_groups = exercise.get('muscle_groups', [])
                            if muscle_groups:
                                response_text += f"   • Targets: {', '.join(muscle_groups).title()}\n"
                            
                            # Add notes if available
                            notes = exercise.get('notes', '')
                            if notes:
                                response_text += f"   • Notes: {notes}\n"
                            
                            response_text += "\n"
                    
                    response_text += "💪 **Ready to crush your workout?** Remember to warm up before starting!"
                else:
                    response_text += "It looks like this is a rest day or the workout details aren't available. Consider doing some light stretching or cardio!"
                
                return {
                    "success": True,
                    "data": response_text,
                    "message": f"Retrieved {query_type} workout plan"
                }
            else:
                return {
                    "success": True,
                    "data": f"No specific workout found for {target_date.strftime('%A')}. You might have a rest day, or your workout plan doesn't specify daily routines. Would you like me to suggest some exercises?",
                    "message": "No workout found for specified day"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_next_meal_tool(self, user_id, query_type="next"):
        """Get user's next meal based on current time and meal plans"""
        try:
            from datetime import datetime
            
            # Get user's stored meal plans
            stored_plans_result = self.get_stored_meal_plans_tool(user_id)
            
            if not stored_plans_result["success"] or not stored_plans_result["data"]:
                return {
                    "success": True,
                    "data": "You don't have any saved meal plans yet. Would you like me to create a personalized meal plan for you?",
                    "message": "No meal plans found"
                }
            
            # Get the most recent meal plan
            meal_plans = stored_plans_result["data"]
            latest_plan = max(meal_plans, key=lambda x: x.get('created_at', ''))
            
            # Get current time to determine next meal
            current_hour = datetime.now().hour
            
            # Determine next meal based on time
            if current_hour < 9:
                next_meal_type = "breakfast"
            elif current_hour < 13:
                next_meal_type = "lunch"
            elif current_hour < 18:
                next_meal_type = "dinner"
            else:
                next_meal_type = "snack"
            
            # Parse meals from the plan
            meals = latest_plan.get('meals', {})
            if isinstance(meals, str):
                import json
                try:
                    meals = json.loads(meals)
                except:
                    meals = {}
            
            # Find the next meal
            next_meal = None
            if isinstance(meals, dict):
                # Try to find exact match first
                next_meal = meals.get(next_meal_type)
                
                # If not found, try variations
                if not next_meal:
                    for meal_key, meal_data in meals.items():
                        if next_meal_type in meal_key.lower():
                            next_meal = meal_data
                            break
            elif isinstance(meals, list):
                # If meals is a list, find by type
                for meal in meals:
                    if isinstance(meal, dict) and meal.get('type', '').lower() == next_meal_type:
                        next_meal = meal
                        break
            
            if next_meal:
                meal_name = next_meal.get('name', f'{next_meal_type.title()} Meal')
                calories = next_meal.get('total_calories', next_meal.get('calories', 'N/A'))
                protein = next_meal.get('total_protein', next_meal.get('protein', 'N/A'))
                
                response_text = f"🍽️ **Your Next Meal - {meal_name}**\n\n"
                response_text += f"📊 **Nutrition**: {calories} calories, {protein}g protein\n\n"
                
                # Add ingredients if available
                ingredients = next_meal.get('ingredients', [])
                if ingredients:
                    response_text += f"🛒 **Ingredients**:\n"
                    for ingredient in ingredients:
                        response_text += f"• {ingredient}\n"
                    response_text += "\n"
                
                # Add preparation steps if available
                steps = next_meal.get('preparation_steps', next_meal.get('steps', []))
                if steps:
                    response_text += f"👨‍🍳 **Preparation**:\n"
                    for i, step in enumerate(steps, 1):
                        response_text += f"{i}. {step}\n"
                    response_text += "\n"
                
                response_text += f"⏰ **Perfect timing for {next_meal_type}!** Enjoy your meal!"
                
                return {
                    "success": True,
                    "data": response_text,
                    "message": f"Retrieved next meal ({next_meal_type})"
                }
            else:
                return {
                    "success": True,
                    "data": f"I couldn't find a specific {next_meal_type} in your meal plan. Would you like me to suggest something healthy for this time of day?",
                    "message": "No specific meal found"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_meal_preparation_tool(self, user_id, query_type="prepare"):
        """Get meal preparation instructions for current meal"""
        try:
            # First get the next meal
            next_meal_result = self.get_next_meal_tool(user_id, "next")
            
            if not next_meal_result["success"]:
                return next_meal_result
            
            # Get user's stored meal plans for detailed preparation
            stored_plans_result = self.get_stored_meal_plans_tool(user_id)
            
            if not stored_plans_result["success"] or not stored_plans_result["data"]:
                return {
                    "success": True,
                    "data": "I don't have your meal plan details for preparation instructions. Would you like me to create a meal plan first?",
                    "message": "No meal plans for preparation"
                }
            
            # Get the most recent meal plan
            meal_plans = stored_plans_result["data"]
            latest_plan = max(meal_plans, key=lambda x: x.get('created_at', ''))
            
            # Determine current meal time
            from datetime import datetime
            current_hour = datetime.now().hour
            
            if current_hour < 9:
                current_meal_type = "breakfast"
            elif current_hour < 13:
                current_meal_type = "lunch"
            elif current_hour < 18:
                current_meal_type = "dinner"
            else:
                current_meal_type = "snack"
            
            # Parse meals and find current meal
            meals = latest_plan.get('meals', {})
            if isinstance(meals, str):
                import json
                try:
                    meals = json.loads(meals)
                except:
                    meals = {}
            
            current_meal = None
            if isinstance(meals, dict):
                current_meal = meals.get(current_meal_type)
                if not current_meal:
                    for meal_key, meal_data in meals.items():
                        if current_meal_type in meal_key.lower():
                            current_meal = meal_data
                            break
            
            if current_meal:
                meal_name = current_meal.get('name', f'{current_meal_type.title()} Meal')
                
                response_text = f"👨‍🍳 **Preparation Guide - {meal_name}**\n\n"
                
                # Ingredients checklist
                ingredients = current_meal.get('ingredients', [])
                if ingredients:
                    response_text += f"🛒 **Ingredients Checklist**:\n"
                    for ingredient in ingredients:
                        response_text += f"☐ {ingredient}\n"
                    response_text += "\n"
                
                # Preparation steps
                steps = current_meal.get('preparation_steps', current_meal.get('steps', []))
                if steps:
                    response_text += f"📝 **Step-by-Step Preparation**:\n"
                    for i, step in enumerate(steps, 1):
                        response_text += f"**Step {i}**: {step}\n"
                    response_text += "\n"
                
                # Cooking tips if available
                cooking_time = current_meal.get('cooking_time', '')
                if cooking_time:
                    response_text += f"⏱️ **Cooking Time**: {cooking_time}\n\n"
                
                # Nutritional reminder
                calories = current_meal.get('total_calories', current_meal.get('calories', 'N/A'))
                protein = current_meal.get('total_protein', current_meal.get('protein', 'N/A'))
                response_text += f"📊 **Nutrition**: {calories} calories, {protein}g protein\n\n"
                
                response_text += "🔥 **Ready to cook?** Take your time and enjoy the process!"
                
                return {
                    "success": True,
                    "data": response_text,
                    "message": f"Retrieved preparation guide for {current_meal_type}"
                }
            else:
                return {
                    "success": True,
                    "data": f"I couldn't find preparation details for your current {current_meal_type}. Would you like me to suggest a quick and healthy recipe?",
                    "message": "No preparation details found"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_specific_meal_tool(self, user_id, meal_type):
        """Get specific meal details (breakfast, lunch, dinner, snack)"""
        try:
            # Get user's stored meal plans
            stored_plans_result = self.get_stored_meal_plans_tool(user_id)
            
            if not stored_plans_result["success"] or not stored_plans_result["data"]:
                return {
                    "success": True,
                    "data": f"You don't have any saved meal plans yet. Would you like me to create a personalized meal plan with {meal_type} options?",
                    "message": "No meal plans found"
                }
            
            # Get the most recent meal plan
            meal_plans = stored_plans_result["data"]
            latest_plan = max(meal_plans, key=lambda x: x.get('created_at', ''))
            
            # Parse meals
            meals = latest_plan.get('meals', {})
            if isinstance(meals, str):
                import json
                try:
                    meals = json.loads(meals)
                except:
                    meals = {}
            
            # Find the specific meal
            specific_meal = None
            if isinstance(meals, dict):
                specific_meal = meals.get(meal_type)
                if not specific_meal:
                    for meal_key, meal_data in meals.items():
                        if meal_type in meal_key.lower():
                            specific_meal = meal_data
                            break
            elif isinstance(meals, list):
                for meal in meals:
                    if isinstance(meal, dict) and meal.get('type', '').lower() == meal_type:
                        specific_meal = meal
                        break
            
            if specific_meal:
                meal_name = specific_meal.get('name', f'{meal_type.title()} Meal')
                calories = specific_meal.get('total_calories', specific_meal.get('calories', 'N/A'))
                protein = specific_meal.get('total_protein', specific_meal.get('protein', 'N/A'))
                carbs = specific_meal.get('total_carbs', specific_meal.get('carbs', 'N/A'))
                fat = specific_meal.get('total_fat', specific_meal.get('fat', 'N/A'))
                
                response_text = f"🍽️ **Today's {meal_type.title()} - {meal_name}**\n\n"
                response_text += f"📊 **Nutrition Breakdown**:\n"
                response_text += f"• Calories: {calories} kcal\n"
                response_text += f"• Protein: {protein}g\n"
                response_text += f"• Carbs: {carbs}g\n"
                response_text += f"• Fat: {fat}g\n\n"
                
                # Ingredients
                ingredients = specific_meal.get('ingredients', [])
                if ingredients:
                    response_text += f"🛒 **Ingredients**:\n"
                    for ingredient in ingredients:
                        response_text += f"• {ingredient}\n"
                    response_text += "\n"
                
                # Preparation
                steps = specific_meal.get('preparation_steps', specific_meal.get('steps', []))
                if steps:
                    response_text += f"👨‍🍳 **How to Prepare**:\n"
                    for i, step in enumerate(steps, 1):
                        response_text += f"{i}. {step}\n"
                    response_text += "\n"
                
                response_text += f"✨ **Perfect choice for {meal_type}!** This meal aligns with your fitness goals."
                
                return {
                    "success": True,
                    "data": response_text,
                    "message": f"Retrieved {meal_type} details"
                }
            else:
                return {
                    "success": True,
                    "data": f"I couldn't find a specific {meal_type} in your current meal plan. Would you like me to suggest a healthy {meal_type} option?",
                    "message": f"No {meal_type} found in meal plan"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_workout_schedule_tool(self, user_id):
        """Get user's complete workout schedule and timing"""
        try:
            # Get user's stored workout plans
            stored_plans_result = self.get_stored_workout_plans_tool(user_id)
            
            if not stored_plans_result["success"] or not stored_plans_result["data"]:
                return {
                    "success": True,
                    "data": "You don't have any saved workout plans yet. Would you like me to create a personalized workout schedule for you?",
                    "message": "No workout plans found"
                }
            
            # Get the most recent workout plan
            workout_plans = stored_plans_result["data"]
            latest_plan = max(workout_plans, key=lambda x: x.get('created_at', ''))
            
            goal = latest_plan.get('goal', 'General Fitness').replace('_', ' ').title()
            days_per_week = latest_plan.get('days', 'N/A')
            
            response_text = f"📅 **Your Workout Schedule**\n\n"
            response_text += f"🎯 **Goal**: {goal}\n"
            response_text += f"📊 **Frequency**: {days_per_week} days per week\n\n"
            
            # Parse exercises
            exercises = latest_plan.get('exercises', [])
            if isinstance(exercises, str):
                import json
                try:
                    exercises = json.loads(exercises)
                except:
                    exercises = []
            
            if exercises:
                response_text += f"🗓️ **Weekly Schedule**:\n\n"
                
                for i, day_plan in enumerate(exercises, 1):
                    if isinstance(day_plan, dict):
                        day_name = day_plan.get('day_name', f'Day {i}')
                        day_exercises = day_plan.get('exercises', [])
                        
                        response_text += f"**{day_name}**\n"
                        response_text += f"• {len(day_exercises)} exercises planned\n"
                        
                        # Show main muscle groups
                        muscle_groups = set()
                        for exercise in day_exercises:
                            if isinstance(exercise, dict):
                                groups = exercise.get('muscle_groups', [])
                                muscle_groups.update(groups)
                        
                        if muscle_groups:
                            response_text += f"• Focus: {', '.join(list(muscle_groups)[:3]).title()}\n"
                        
                        response_text += "\n"
                
                response_text += "💡 **Tips**:\n"
                response_text += "• Rest 48-72 hours between training the same muscle groups\n"
                response_text += "• Stay consistent with your schedule\n"
                response_text += "• Listen to your body and take rest days when needed\n\n"
                
                response_text += "🔥 **Ready to follow your schedule?** Consistency is key to reaching your goals!"
            else:
                response_text += "Your workout plan structure isn't detailed yet. Would you like me to create a more detailed schedule?"
            
            return {
                "success": True,
                "data": response_text,
                "message": "Retrieved workout schedule"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_available_tools(self):
        """Get list of available tools"""
        return list(self.tools.keys())
    
    def execute_tool(self, tool_name, **kwargs):
        """Execute a specific tool with given parameters"""
        if tool_name not in self.tools:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        
        tool_info = self.tools[tool_name]
        try:
            result = tool_info["function"](**kwargs)
            return result
        except Exception as e:
            return {"success": False, "error": f"Tool execution failed: {str(e)}"}

# Initialize chatbot tools
chatbot_tools = ChatbotTools()

def fast_keyword_classifier(user_message):
    """Fast keyword-based classification to avoid AI calls for simple questions"""
    message_lower = user_message.lower().strip()
    
    # Greetings (check first)
    if message_lower in ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]:
        return {"intent": "greeting", "tools_to_use": ["generate_greeting"]}
    
    # Smart data-aware questions (check before plan creation)
    # Next workout questions
    if any(phrase in message_lower for phrase in [
        "next workout", "today's workout", "workout today", "workout for today",
        "what workout today", "my workout today", "today workout", "workout plan for today",
        "what is my next workout", "what's my next workout", "whats my next workout",
        "what do i train today", "which workout today", "what should i train today"
    ]):
        return {"intent": "smart_workout_query", "tools_to_use": ["get_next_workout"], "query_type": "today"}
    
    if any(phrase in message_lower for phrase in [
        "tomorrow workout", "workout tomorrow", "next day workout", "workout for tomorrow",
        "what workout tomorrow", "my workout tomorrow", "tommorow workout", "workout tommorow",
        "tommorows workout", "tomorrows workout"
    ]):
        return {"intent": "smart_workout_query", "tools_to_use": ["get_next_workout"], "query_type": "tomorrow"}
    
    # Next meal questions
    if any(phrase in message_lower for phrase in [
        "next meal", "what to eat next", "what should i eat", "meal now", "current meal",
        "what to eat now", "next food", "what meal now", "meal for now",
        "what is my next meal", "what's my next meal", "whats my next meal",
        "what should i eat now", "what should i eat for next meal"
    ]):
        return {"intent": "smart_meal_query", "tools_to_use": ["get_next_meal"], "query_type": "next"}
    
    if any(phrase in message_lower for phrase in [
        "what to prepare", "what should i prepare", "prepare now", "cooking now",
        "what to cook", "meal prep", "prepare meal", "cook now"
    ]):
        return {"intent": "smart_meal_query", "tools_to_use": ["get_meal_preparation"], "query_type": "prepare"}
    
    if any(phrase in message_lower for phrase in [
        "breakfast today", "lunch today", "dinner today", "snack today",
        "today's breakfast", "today's lunch", "today's dinner"
    ]):
        meal_type = None
        if "breakfast" in message_lower:
            meal_type = "breakfast"
        elif "lunch" in message_lower:
            meal_type = "lunch"
        elif "dinner" in message_lower:
            meal_type = "dinner"
        elif "snack" in message_lower:
            meal_type = "snack"
        
        return {"intent": "smart_meal_query", "tools_to_use": ["get_specific_meal"], "query_type": "specific", "meal_type": meal_type}
    
    # Workout progress and schedule questions
    if any(phrase in message_lower for phrase in [
        "workout schedule", "my schedule", "training schedule", "workout days",
        "when do i workout", "workout timing"
    ]):
        return {"intent": "smart_workout_query", "tools_to_use": ["get_workout_schedule"], "query_type": "schedule"}
    
    # Nutrition/Meal plan requests - extract goal from prompt (check before profile questions)
    # IMPORTANT: avoid generic words like "meal", "diet", "nutrition" to prevent false positives for smart meal queries
    nutrition_keywords = [
        "nutrition plan", "meal plan", "diet plan", "eating plan", "food plan",
        "create nutrition plan", "generate meal plan", "create meal plan", "make meal plan",
        "design meal plan", "generate diet plan", "create diet plan"
    ]
    
    for keyword in nutrition_keywords:
        if keyword in message_lower:
            # Extract goal from the message
            extracted_goal = "general_fitness"  # default
            if any(word in message_lower for word in ["muscle", "bulk", "gain", "build", "strength"]):
                extracted_goal = "muscle_gain"
            elif any(word in message_lower for word in ["lose", "weight loss", "fat", "cut", "slim"]):
                extracted_goal = "weight_loss"
            elif any(word in message_lower for word in ["endurance", "cardio", "running", "stamina"]):
                extracted_goal = "endurance"
            elif any(word in message_lower for word in ["tone", "toning", "definition"]):
                extracted_goal = "toning"
            
            return {
                "intent": "nutrition_request", 
                "tools_to_use": ["generate_meal_plan"],
                "extracted_goal": extracted_goal
            }
    
    # Workout plan requests - extract goal from prompt (but exclude smart queries)
    workout_keywords = ["workout plan", "create workout", "generate workout", "give me workout", "training plan", "exercise plan", "fitness plan"]
    
    for keyword in workout_keywords:
        if keyword in message_lower:
            # Skip if this is clearly asking about existing workouts (smart queries)
            if any(phrase in message_lower for phrase in [
                "my workout", "next workout", "today", "tomorrow", "schedule", 
                "what workout", "which workout", "workout for"
            ]):
                continue
                
            # Extract goal from the message
            extracted_goal = "general_fitness"  # default
            if any(word in message_lower for word in ["muscle", "bulk", "gain", "build", "strength"]):
                extracted_goal = "muscle_gain"
            elif any(word in message_lower for word in ["lose", "weight loss", "fat", "cut", "slim"]):
                extracted_goal = "weight_loss"
            elif any(word in message_lower for word in ["endurance", "cardio", "running", "stamina"]):
                extracted_goal = "endurance"
            elif any(word in message_lower for word in ["tone", "toning", "definition"]):
                extracted_goal = "toning"
            
            return {
                "intent": "plan_request", 
                "tools_to_use": ["generate_workout_json"],
                "extracted_goal": extracted_goal
            }
    
    # Additional check for generic "workout" requests (only if not asking about existing workouts)
    if "workout" in message_lower and not any(phrase in message_lower for phrase in [
        "my workout", "next workout", "today", "tomorrow", "schedule", 
        "what workout", "which workout", "workout for", "workout today", "workout tomorrow"
    ]):
        # This is likely a request for a new workout plan
        extracted_goal = "general_fitness"
        if any(word in message_lower for word in ["muscle", "bulk", "gain", "build", "strength"]):
            extracted_goal = "muscle_gain"
        elif any(word in message_lower for word in ["lose", "weight loss", "fat", "cut", "slim"]):
            extracted_goal = "weight_loss"
        elif any(word in message_lower for word in ["endurance", "cardio", "running", "stamina"]):
            extracted_goal = "endurance"
        elif any(word in message_lower for word in ["tone", "toning", "definition"]):
            extracted_goal = "toning"
        
        return {
            "intent": "plan_request", 
            "tools_to_use": ["generate_workout_json"],
            "extracted_goal": extracted_goal
        }
    
    # Update/Add choices
    if message_lower in ["update", "update plan", "update my plan"]:
        return {"intent": "workout_plan_choice", "action": "update"}
    
    if any(phrase in message_lower for phrase in ["add new", "add another", "new plan"]):
        return {"intent": "workout_plan_choice", "action": "add"}
    
    # Plan questions
    if any(phrase in message_lower for phrase in ["my workout plans", "workout plans", "show workout"]):
        return {"intent": "profile_question", "tools_to_use": ["get_stored_workout_plans"]}
    
    if any(phrase in message_lower for phrase in ["my meal plans", "meal plans", "show meal"]):
        return {"intent": "profile_question", "tools_to_use": ["get_stored_meal_plans"]}
    
    # Profile questions - detect multiple fields in one question (check AFTER plan requests)
    profile_fields_mentioned = []
    
    # Check for each field mentioned in the message
    if any(phrase in message_lower for phrase in ["age", "old", "years"]):
        profile_fields_mentioned.append("age")
    
    if any(phrase in message_lower for phrase in ["weight", "weigh", "kg", "pounds", "lbs"]):
        profile_fields_mentioned.append("weight")
    
    if any(phrase in message_lower for phrase in ["height", "tall", "cm", "feet", "inches"]):
        profile_fields_mentioned.append("height")
    
    if any(phrase in message_lower for phrase in ["goal", "fitness goal", "objective"]):
        profile_fields_mentioned.append("goal")
    
    if any(phrase in message_lower for phrase in ["calories", "calorie", "daily calories"]):
        profile_fields_mentioned.append("calories")
    
    if any(phrase in message_lower for phrase in ["protein", "daily protein", "protein target"]):
        profile_fields_mentioned.append("protein")
    
    # If multiple profile fields are mentioned, or general profile questions
    if len(profile_fields_mentioned) > 1 or any(phrase in message_lower for phrase in ["my profile", "about my profile", "profile summary", "tell me about"]):
        return {"intent": "profile_question", "tools_to_use": ["get_user_profile"], "fields": profile_fields_mentioned, "field": "multiple"}
    
    # Single field questions
    elif len(profile_fields_mentioned) == 1:
        field = profile_fields_mentioned[0]
        return {"intent": "profile_question", "tools_to_use": ["get_user_profile"], "field": field}
    
    # If no fast match, use AI orchestrator
    return None

def ai_tool_orchestrator(user_message, user_id):
    """AI-driven tool orchestration with fast keyword pre-filtering"""
    try:
        # Try fast keyword classification first
        fast_result = fast_keyword_classifier(user_message)
        if fast_result:
            return fast_result
        
        # Get user profile first (only for complex queries)
        user_profile = get_user_profile(user_id)
        
        # AI decides what to do based on the message and profile
        orchestration_prompt = f"""
You are an AI tool orchestrator for a fitness chatbot. Analyze the user's message and decide what tools to use.

User Message: "{user_message}"
User Profile: {user_profile}

Available Tools:
1. get_user_profile - Get stored user profile
2. update_user_profile - Update user profile with new info
3. check_profile_completeness - Check if profile is complete
4. calculate_macros - Calculate calories and macros
5. get_workout_suggestions - Get workout advice using RAG
6. get_nutrition_suggestions - Get nutrition advice using RAG
7. generate_meal_plan - Create detailed meal plan
8. generate_full_plan - Create comprehensive fitness plan
9. generate_workout_json - Create structured workout JSON
10. generate_greeting - Generate friendly greeting
11. generate_conversational_response - General conversation
12. answer_fitness_question - Answer fitness questions with RAG
13. get_stored_workout_plans - Retrieve user's saved workout plans from database
14. answer_workout_plan_question - Answer questions about user's stored workout plans
15. get_stored_meal_plans - Retrieve user's saved meal plans from database
16. answer_meal_plan_question - Answer questions about user's stored meal plans
17. get_next_workout - Get user's next workout based on current day and stored plans
18. get_next_meal - Get user's next meal based on current time and meal plans
19. get_meal_preparation - Get meal preparation instructions for current meal
20. get_specific_meal - Get specific meal details (breakfast, lunch, dinner, snack)
21. get_workout_schedule - Get user's complete workout schedule and timing

Analyze the message and return a JSON response with your decision:

{{
    "intent": "greeting|profile_sharing|profile_question|plan_request|fitness_question|general_conversation",
    "tools_to_use": ["tool1", "tool2"],
    "extracted_profile_data": {{"age": null, "weight": null, "height": null, "goal": null}},
    "reasoning": "Why you chose these tools"
}}

Examples:
- "Hi" → {{"intent": "greeting", "tools_to_use": ["generate_greeting"], "extracted_profile_data": {{}}, "reasoning": "Simple greeting"}}
- "I am 25 years old" → {{"intent": "profile_sharing", "tools_to_use": ["update_user_profile"], "extracted_profile_data": {{"age": 25}}, "reasoning": "User sharing age"}}
- "My goal is muscle gain" → {{"intent": "profile_sharing", "tools_to_use": ["update_user_profile"], "extracted_profile_data": {{"goal": "muscle_gain"}}, "reasoning": "User sharing fitness goal"}}
- "I want to build muscle" → {{"intent": "profile_sharing", "tools_to_use": ["update_user_profile"], "extracted_profile_data": {{"goal": "muscle_gain"}}, "reasoning": "User sharing fitness goal"}}
- "What is my age?" → {{"intent": "profile_question", "tools_to_use": ["get_user_profile"], "extracted_profile_data": {{}}, "reasoning": "User asking about stored info"}}
- "Give me a workout plan" → {{"intent": "plan_request", "tools_to_use": ["check_profile_completeness", "generate_full_plan", "generate_workout_json"], "extracted_profile_data": {{}}, "reasoning": "User wants comprehensive plan"}}
- "Create me a nutrition plan" → {{"intent": "plan_request", "tools_to_use": ["check_profile_completeness", "calculate_macros", "generate_meal_plan"], "extracted_profile_data": {{}}, "reasoning": "User wants nutrition/meal plan specifically"}}
- "Give me a meal plan" → {{"intent": "plan_request", "tools_to_use": ["check_profile_completeness", "calculate_macros", "generate_meal_plan"], "extracted_profile_data": {{}}, "reasoning": "User wants meal plan specifically"}}
- "What is protein?" → {{"intent": "fitness_question", "tools_to_use": ["answer_fitness_question"], "extracted_profile_data": {{}}, "reasoning": "General fitness question"}}
- "What are my workout plans?" → {{"intent": "profile_question", "tools_to_use": ["get_stored_workout_plans"], "extracted_profile_data": {{}}, "reasoning": "User asking about stored workout plans"}}
- "Show me my meal plans" → {{"intent": "profile_question", "tools_to_use": ["get_stored_meal_plans"], "extracted_profile_data": {{}}, "reasoning": "User asking about stored meal plans"}}
- "What is my weight?" → {{"intent": "profile_question", "tools_to_use": ["get_user_profile"], "extracted_profile_data": {{}}, "reasoning": "User asking about stored profile info"}}
- "What is my height?" → {{"intent": "profile_question", "tools_to_use": ["get_user_profile"], "extracted_profile_data": {{}}, "reasoning": "User asking about stored profile info"}}
- "What is my goal?" → {{"intent": "profile_question", "tools_to_use": ["get_user_profile"], "extracted_profile_data": {{}}, "reasoning": "User asking about stored profile info"}}
- "What are my calories?" → {{"intent": "profile_question", "tools_to_use": ["get_user_profile"], "extracted_profile_data": {{}}, "reasoning": "User asking about stored profile info"}}
- "Tell me about my profile" → {{"intent": "profile_question", "tools_to_use": ["get_user_profile"], "extracted_profile_data": {{}}, "reasoning": "User asking for complete profile summary"}}
- "update" or "update my plan" → {{"intent": "workout_plan_choice", "tools_to_use": ["generate_workout_json"], "extracted_profile_data": {{}}, "reasoning": "User chose to update existing workout plan"}}
- "add new" or "add another plan" → {{"intent": "workout_plan_choice", "tools_to_use": ["generate_workout_json"], "extracted_profile_data": {{}}, "reasoning": "User chose to add new workout plan"}}

IMPORTANT: Always prioritize profile_sharing over plan_request when the user is sharing personal information like goals, age, weight, height, etc.

Return ONLY valid JSON.
"""

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            orchestration_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=400,
                temperature=0.2,
            )
        )
        
        # Parse AI decision
        import json
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        ai_decision = json.loads(response_text)
        
        return ai_decision
        
    except Exception as e:
        error_message = str(e)
        
        # Check for quota exceeded error
        if "429" in error_message and "quota" in error_message.lower():
            # Try to provide basic functionality without AI
            message_lower = user_message.lower()
            
            # Basic keyword detection for common requests
            if any(word in message_lower for word in ['nutrition', 'meal', 'diet', 'food']):
                return {
                    "intent": "quota_exceeded_nutrition",
                    "tools_to_use": ["quota_exceeded_nutrition_response"],
                    "extracted_profile_data": {},
                    "reasoning": "API quota exceeded - nutrition request"
                }
            elif any(word in message_lower for word in ['workout', 'exercise', 'training', 'gym']):
                return {
                    "intent": "quota_exceeded_workout",
                    "tools_to_use": ["quota_exceeded_workout_response"],
                    "extracted_profile_data": {},
                    "reasoning": "API quota exceeded - workout request"
                }
            else:
                return {
                    "intent": "quota_exceeded",
                    "tools_to_use": ["quota_exceeded_response"],
                    "extracted_profile_data": {},
                    "reasoning": "API quota exceeded"
                }
        
        # Minimal fallback for other errors
        return {
            "intent": "general_conversation",
            "tools_to_use": ["generate_conversational_response"],
            "extracted_profile_data": {},
            "reasoning": "Fallback due to error"
        }

def execute_ai_decision(ai_decision, user_message, user_id):
    """Execute the AI's tool selection decision with fast path optimization"""
    tools_to_use = ai_decision.get("tools_to_use", [])
    extracted_profile_data = ai_decision.get("extracted_profile_data", {})
    intent = ai_decision.get("intent", "general_conversation")
    
    tool_results = {}
    response_data = {"response": ""}
    
    # Fast path for profile questions with specific field(s)
    if intent == "profile_question" and "field" in ai_decision:
        field = ai_decision["field"]
        fields = ai_decision.get("fields", [])
        profile = get_user_profile(user_id)
        
        if profile:
            if field == "multiple" and fields:
                # Handle multiple fields in one response
                response_parts = []
                
                if "age" in fields:
                    age = profile.get('age', 'not set')
                    response_parts.append(f"🧑 **Age**: {age} years old")
                
                if "weight" in fields:
                    weight = profile.get('weight', 'not set')
                    response_parts.append(f"⚖️ **Weight**: {weight}kg")
                
                if "height" in fields:
                    height = profile.get('height', 'not set')
                    response_parts.append(f"📏 **Height**: {height}cm")
                
                if "goal" in fields:
                    goal = profile.get('fitness_goal', 'not set')
                    response_parts.append(f"🎯 **Goal**: {goal}")
                
                if "calories" in fields:
                    calories = profile.get('target_calories', 'not calculated')
                    response_parts.append(f"🔥 **Daily Calories**: {calories} calories")
                
                if "protein" in fields:
                    protein = profile.get('target_protein', 'not calculated')
                    response_parts.append(f"💪 **Daily Protein**: {protein}g")
                
                if response_parts:
                    response_data["response"] = "Here's your information:\n\n" + "\n".join(response_parts)
                else:
                    response_data["response"] = "I couldn't find the specific information you requested."
                    
            elif field == "age":
                age = profile.get('age', 'not set')
                response_data["response"] = f"You are {age} years old."
            elif field == "weight":
                weight = profile.get('weight', 'not set')
                response_data["response"] = f"Your weight is {weight}kg."
            elif field == "height":
                height = profile.get('height', 'not set')
                response_data["response"] = f"Your height is {height}cm."
            elif field == "goal":
                goal = profile.get('fitness_goal', 'not set')
                response_data["response"] = f"Your fitness goal is: {goal}."
            elif field == "calories":
                calories = profile.get('target_calories', 'not calculated')
                response_data["response"] = f"Your daily calorie target is {calories} calories."
            elif field == "protein":
                protein = profile.get('target_protein', 'not calculated')
                response_data["response"] = f"Your daily protein target is {protein}g."
            elif field == "summary":
                age = profile.get('age', 'N/A')
                weight = profile.get('weight', 'N/A')
                height = profile.get('height', 'N/A')
                goal = profile.get('fitness_goal', 'N/A')
                calories = profile.get('target_calories', 'N/A')
                
                response_data["response"] = f"""Here's your profile summary:

🧑 **Age**: {age} years old
⚖️ **Weight**: {weight}kg
📏 **Height**: {height}cm
🎯 **Goal**: {goal}
🔥 **Daily Calories**: {calories} calories

Is there anything specific you'd like to know about your profile?"""
        else:
            response_data["response"] = "I don't have your profile information yet. Please share some details about yourself (age, weight, height, fitness goal) so I can help you better!"
        
        return response_data, tool_results
    
    # Special handling for nutrition plan requests
    if intent == "nutrition_request":
        # Get user profile for basic info (age, weight, height)
        profile = get_user_profile(user_id)
        
        # Use extracted goal from prompt instead of profile goal
        extracted_goal = ai_decision.get("extracted_goal", "general_fitness")
        
        # Create a modified profile with the extracted goal
        nutrition_profile = profile.copy() if profile else {}
        nutrition_profile['goal'] = extracted_goal
        nutrition_profile['fitness_goal'] = extracted_goal
        
        # Set defaults for missing profile data
        nutrition_profile.setdefault('age', 25)
        nutrition_profile.setdefault('weight', 70)
        nutrition_profile.setdefault('height', 175)
        nutrition_profile.setdefault('gender', 'male')
        nutrition_profile.setdefault('activity', 'moderate')
        
        # Generate nutrition plan with extracted goal
        result = chatbot_tools.execute_tool("generate_meal_plan", user_profile=nutrition_profile)
        if result["success"]:
            age_display = nutrition_profile.get('age', 25)
            goal_display = extracted_goal.replace('_', ' ').title()
            
            # Format the meal plan
            meal_plan = result["data"]
            
            # Create nutrition plan display
            response_text = f"Perfect! I've created a personalized nutrition plan for **{goal_display}**.\n\n"
            response_text += f"📊 **Your Profile**: Age {age_display}, {nutrition_profile['weight']}kg, {nutrition_profile['height']}cm\n\n"
            
            if 'daily_totals' in meal_plan:
                response_text += f"🎯 **Daily Targets**: {meal_plan['daily_totals']['calories']} calories, {meal_plan['daily_totals']['protein']}g protein\n\n"
            
            # Show meal plan overview
            if 'meals' in meal_plan:
                response_text += "🍽️ **Your Nutrition Plan Includes**:\n"
                for meal_name, meal_data in meal_plan['meals'].items():
                    calories = meal_data.get('total_calories', 'N/A')
                    protein = meal_data.get('total_protein', 'N/A')
                    response_text += f"• **{meal_name.title()}**: {meal_data.get('name', 'Meal')} ({calories} cal, {protein}g protein)\n"
                
                response_text += f"\n💡 **Total Daily**: {meal_plan['daily_totals']['calories']} calories, {meal_plan['daily_totals']['protein']}g protein\n\n"
            
            response_text += "🔥 Ready to start your nutrition journey? This plan is tailored for your goals!"
            
            response_data["response"] = response_text
            response_data["nutrition_plan"] = result["data"]
            
            return response_data, tool_results
    
    # Smart Data-Aware Query Handlers
    if intent == "smart_workout_query":
        query_type = ai_decision.get("query_type", "today")
        
        if "get_next_workout" in tools_to_use:
            result = chatbot_tools.execute_tool("get_next_workout", user_id=user_id, query_type=query_type)
        elif "get_workout_schedule" in tools_to_use:
            result = chatbot_tools.execute_tool("get_workout_schedule", user_id=user_id)
        else:
            result = {"success": False, "error": "Unknown workout query tool"}
        
        if result["success"]:
            response_data["response"] = result["data"]
            return response_data, tool_results
    
    if intent == "smart_meal_query":
        query_type = ai_decision.get("query_type", "next")
        meal_type = ai_decision.get("meal_type", None)
        
        if "get_next_meal" in tools_to_use:
            result = chatbot_tools.execute_tool("get_next_meal", user_id=user_id, query_type=query_type)
        elif "get_meal_preparation" in tools_to_use:
            result = chatbot_tools.execute_tool("get_meal_preparation", user_id=user_id, query_type=query_type)
        elif "get_specific_meal" in tools_to_use and meal_type:
            result = chatbot_tools.execute_tool("get_specific_meal", user_id=user_id, meal_type=meal_type)
        else:
            result = {"success": False, "error": "Unknown meal query tool"}
        
        if result["success"]:
            response_data["response"] = result["data"]
            return response_data, tool_results
    
    # Special handling for workout plan choices
    if intent == "workout_plan_choice":
        action = ai_decision.get("action", "add")
        if not action:
            user_choice = user_message.lower().strip()
            if "update" in user_choice:
                action = "update"
            elif "add" in user_choice or "new" in user_choice:
                action = "add"
            else:
                action = "add"
        
        # Generate workout plan with the chosen action
        profile = get_user_profile(user_id)
        missing_fields = check_profile_completeness(profile)
        
        if missing_fields:
            missing_message = get_missing_fields_message(missing_fields)
            response_data["response"] = f"I'd love to create a personalized workout plan for you! {missing_message}"
            return response_data, tool_results
        
        result = chatbot_tools.execute_tool("generate_workout_json", user_profile=profile)
        if result["success"]:
            age_display = profile.get('age', 25)
            goal_display = profile['goal'].replace('_', ' ').title()
            
            # Create a user-friendly response for workout plan
            workout_plan = result["data"]
            action_text = "updated" if action == "update" else "new"
            response_text = f"Perfect! I've created your {action_text} personalized workout plan for your {goal_display} goal.\n\n"
            response_text += f"💪 **Your Profile**: Age {age_display}, {profile['weight']}kg, {profile['height']}cm\n\n"
            
            if 'days' in workout_plan:
                response_text += f"🗓️ **Training Schedule**: {workout_plan['days']} days per week\n\n"
            
            # Show workout overview
            if 'exercises' in workout_plan and workout_plan['exercises']:
                response_text += "🏋️ **Your Workout Plan Includes**:\n"
                for day_plan in workout_plan['exercises']:
                    day_name = day_plan.get('day_name', day_plan.get('day', 'Training Day'))
                    exercise_count = len(day_plan.get('exercises', []))
                    response_text += f"• **{day_name}**: {exercise_count} exercises\n"
                
                response_text += f"\n💡 **Total Exercises**: {sum(len(day.get('exercises', [])) for day in workout_plan['exercises'])} exercises across {len(workout_plan['exercises'])} training days\n\n"
            
            response_text += f"🔥 Ready to {action} your workout plan? Click the **'Save Workout Plan'** button below!"
            
            response_data["response"] = response_text
            response_data["workout_plan"] = result["data"]
            response_data["workout_plan_action"] = action
            
            return response_data, tool_results
    
    for tool_name in tools_to_use:
        try:
            if tool_name == "get_user_profile":
                result = chatbot_tools.execute_tool("get_user_profile", user_id=user_id)
                if result["success"] and result["data"]:
                    profile = result["data"]
                    # Generate a user-friendly response based on what they asked
                    user_message_lower = user_message.lower()
                    
                    if "age" in user_message_lower:
                        age = profile.get('age', 'not set')
                        response_data["response"] = f"You are {age} years old."
                    elif "weight" in user_message_lower:
                        weight = profile.get('weight', 'not set')
                        response_data["response"] = f"Your weight is {weight}kg."
                    elif "height" in user_message_lower:
                        height = profile.get('height', 'not set')
                        response_data["response"] = f"Your height is {height}cm."
                    elif "goal" in user_message_lower:
                        goal = profile.get('fitness_goal', 'not set')
                        response_data["response"] = f"Your fitness goal is: {goal}."
                    elif "calories" in user_message_lower:
                        calories = profile.get('target_calories', 'not calculated')
                        response_data["response"] = f"Your daily calorie target is {calories} calories."
                    elif "protein" in user_message_lower:
                        protein = profile.get('target_protein', 'not calculated')
                        response_data["response"] = f"Your daily protein target is {protein}g."
                    else:
                        # General profile summary
                        age = profile.get('age', 'N/A')
                        weight = profile.get('weight', 'N/A')
                        height = profile.get('height', 'N/A')
                        goal = profile.get('fitness_goal', 'N/A')
                        calories = profile.get('target_calories', 'N/A')
                        
                        response_data["response"] = f"""Here's your profile summary:
                        
🧑 **Age**: {age} years old
⚖️ **Weight**: {weight}kg
📏 **Height**: {height}cm
🎯 **Goal**: {goal}
🔥 **Daily Calories**: {calories} calories

Is there anything specific you'd like to know about your profile?"""
                else:
                    response_data["response"] = "I don't have your profile information yet. Please share some details about yourself (age, weight, height, fitness goal) so I can help you better!"
                
            elif tool_name == "update_user_profile":
                # Clean extracted data
                clean_data = {k: v for k, v in extracted_profile_data.items() if v is not None}
                if clean_data:
                    result = chatbot_tools.execute_tool("update_user_profile", user_id=user_id, profile_data=clean_data)
                    if result["success"]:
                        updates = [f"{k}: {v}" for k, v in clean_data.items()]
                        response_data["response"] = f"Got it! Updated your {', '.join(updates)}. Thanks for sharing!"
                else:
                    result = {"success": False, "error": "No profile data to update"}
                    
            elif tool_name == "check_profile_completeness":
                profile = get_user_profile(user_id)
                result = chatbot_tools.execute_tool("check_profile_completeness", user_profile=profile)
                
            elif tool_name == "generate_greeting":
                result = chatbot_tools.execute_tool("generate_greeting")
                if result["success"]:
                    response_data["response"] = result["data"]
                    
            elif tool_name == "generate_conversational_response":
                result = chatbot_tools.execute_tool("generate_conversational_response", user_message=user_message, context="")
                if result["success"]:
                    response_data["response"] = result["data"]
                    
            elif tool_name == "answer_fitness_question":
                profile = get_user_profile(user_id)
                result = chatbot_tools.execute_tool("answer_fitness_question", question=user_message, user_profile=profile)
                if result["success"]:
                    response_data["response"] = result["data"]
                    
            elif tool_name == "get_stored_workout_plans":
                result = chatbot_tools.execute_tool("get_stored_workout_plans", user_id=user_id)
                if result["success"]:
                    plans = result["data"]
                    if plans:
                        response_text = f"Here are your {len(plans)} saved workout plans:\n\n"
                        for i, plan in enumerate(plans, 1):
                            goal = plan.get('goal', 'General Fitness')
                            days = plan.get('days', 'N/A')
                            created = plan.get('created_at', 'Unknown date')
                            if isinstance(created, str) and 'T' in created:
                                created = created.split('T')[0]
                            response_text += f"**Plan {i}**: {goal}\n"
                            response_text += f"📅 {days} days per week\n"
                            response_text += f"📆 Created: {created}\n\n"
                        response_text += "Would you like me to create a new workout plan or modify an existing one?"
                        response_data["response"] = response_text
                    else:
                        response_data["response"] = "You don't have any saved workout plans yet. Would you like me to create a personalized workout plan for you?"
                        
            elif tool_name == "get_stored_meal_plans":
                result = chatbot_tools.execute_tool("get_stored_meal_plans", user_id=user_id)
                if result["success"]:
                    plans = result["data"]
                    if plans:
                        response_text = f"Here are your {len(plans)} saved meal plans:\n\n"
                        for i, plan in enumerate(plans, 1):
                            goal = plan.get('goal', 'General Nutrition')
                            created = plan.get('created_at', 'Unknown date')
                            if isinstance(created, str) and 'T' in created:
                                created = created.split('T')[0]
                            response_text += f"**Plan {i}**: {goal}\n"
                            response_text += f"📆 Created: {created}\n\n"
                        response_text += "Would you like me to create a new meal plan or view details of an existing one?"
                        response_data["response"] = response_text
                    else:
                        response_data["response"] = "You don't have any saved meal plans yet. Would you like me to create a personalized meal plan for you?"
                    
            elif tool_name == "generate_full_plan":
                profile = get_user_profile(user_id)
                missing_fields = check_profile_completeness(profile)
                
                if missing_fields:
                    missing_message = get_missing_fields_message(missing_fields)
                    response_data["response"] = f"I'd love to create a personalized plan for you! {missing_message}"
                    result = {"success": False, "error": "Incomplete profile"}
                else:
                    result = chatbot_tools.execute_tool("generate_full_plan", user_profile=profile)
                    if result["success"]:
                        age_display = profile.get('age', 25)
                        profile_summary = f"Based on your profile (Age: {age_display}, Weight: {profile['weight']}kg, Height: {profile['height']}cm, Goal: {profile['goal'].replace('_', ' ').title()}), here's your personalized plan:\n\n"
                        response_data["response"] = profile_summary + result["data"]
                        
            elif tool_name == "generate_workout_json":
                # Get user profile for basic info (age, weight, height)
                profile = get_user_profile(user_id)
                
                # Use extracted goal from prompt instead of profile goal
                extracted_goal = ai_decision.get("extracted_goal", "general_fitness")
                
                # Create a modified profile with the extracted goal
                workout_profile = profile.copy() if profile else {}
                workout_profile['goal'] = extracted_goal
                workout_profile['fitness_goal'] = extracted_goal
                
                # Set defaults for missing profile data
                workout_profile.setdefault('age', 25)
                workout_profile.setdefault('weight', 70)
                workout_profile.setdefault('height', 175)
                workout_profile.setdefault('gender', 'male')
                workout_profile.setdefault('activity', 'moderate')
                

                
                # Generate workout plan with extracted goal
                result = chatbot_tools.execute_tool("generate_workout_json", user_profile=workout_profile)
                if result["success"]:
                    age_display = workout_profile.get('age', 25)
                    goal_display = extracted_goal.replace('_', ' ').title()
                    
                    # Create a user-friendly response for workout plan
                    workout_plan = result["data"]
                    response_text = f"Perfect! I've created a personalized workout plan for **{goal_display}**.\n\n"
                    response_text += f"💪 **Your Profile**: Age {age_display}, {workout_profile['weight']}kg, {workout_profile['height']}cm\n\n"
                    
                    if 'days' in workout_plan:
                        response_text += f"🗓️ **Training Schedule**: {workout_plan['days']} days per week\n\n"
                    
                    # Show workout overview
                    if 'exercises' in workout_plan and workout_plan['exercises']:
                        response_text += "🏋️ **Your Workout Plan Includes**:\n"
                        for day_plan in workout_plan['exercises']:
                            day_name = day_plan.get('day_name', day_plan.get('day', 'Training Day'))
                            exercise_count = len(day_plan.get('exercises', []))
                            response_text += f"• **{day_name}**: {exercise_count} exercises\n"
                        
                        response_text += f"\n💡 **Total Exercises**: {sum(len(day.get('exercises', [])) for day in workout_plan['exercises'])} exercises across {len(workout_plan['exercises'])} training days\n\n"
                    
                    # Check for existing plans to determine button options
                    existing_plans = check_existing_workout_plans(user_id)
                    
                    if existing_plans:
                        response_text += f"🔥 I see you have {len(existing_plans)} existing workout plan(s). You can either **update** your current plan or **add** this as a new plan!"
                        response_data["show_both_buttons"] = True
                    else:
                        response_text += "🔥 Ready to start your fitness journey? Save this plan to your profile!"
                        response_data["show_both_buttons"] = False
                    
                    response_data["response"] = response_text
                    response_data["workout_plan"] = result["data"]
                    
            elif tool_name == "calculate_macros":
                profile = get_user_profile(user_id)
                result = chatbot_tools.execute_tool(
                    "calculate_macros",
                    weight=profile.get('weight'),
                    height=profile.get('height'),
                    age=profile.get('age', 25),
                    gender=profile.get('gender', 'male'),
                    goal=profile.get('goal', 'general_fitness'),
                    activity=profile.get('activity', 'moderate')
                )
                if result["success"]:
                    response_data["macros"] = result["data"]
                    
            elif tool_name == "generate_meal_plan":
                # Get user profile for basic info (age, weight, height)
                profile = get_user_profile(user_id)
                
                # Use extracted goal from prompt instead of profile goal
                extracted_goal = ai_decision.get("extracted_goal", "general_fitness")
                
                # Create a modified profile with the extracted goal
                nutrition_profile = profile.copy() if profile else {}
                nutrition_profile['goal'] = extracted_goal
                nutrition_profile['fitness_goal'] = extracted_goal
                
                # Set defaults for missing profile data
                nutrition_profile.setdefault('age', 25)
                nutrition_profile.setdefault('weight', 70)
                nutrition_profile.setdefault('height', 175)
                nutrition_profile.setdefault('gender', 'male')
                nutrition_profile.setdefault('activity', 'moderate')
                
                # Generate nutrition plan with extracted goal
                result = chatbot_tools.execute_tool("generate_meal_plan", user_profile=nutrition_profile)
                if result["success"]:
                    age_display = nutrition_profile.get('age', 25)
                    goal_display = extracted_goal.replace('_', ' ').title()
                    
                    # Format the meal plan
                    meal_plan = result["data"]
                    
                    # Create nutrition plan display
                    response_text = f"Perfect! I've created a personalized nutrition plan for **{goal_display}**.\n\n"
                    response_text += f"📊 **Your Profile**: Age {age_display}, {nutrition_profile['weight']}kg, {nutrition_profile['height']}cm\n\n"
                    
                    if 'daily_totals' in meal_plan:
                        response_text += f"🎯 **Daily Targets**: {meal_plan['daily_totals']['calories']} calories, {meal_plan['daily_totals']['protein']}g protein\n\n"
                    
                    # Show meal plan overview
                    if 'meals' in meal_plan:
                        response_text += "🍽️ **Your Nutrition Plan Includes**:\n"
                        for meal_name, meal_data in meal_plan['meals'].items():
                            calories = meal_data.get('total_calories', 'N/A')
                            protein = meal_data.get('total_protein', 'N/A')
                            response_text += f"• **{meal_name.title()}**: {meal_data.get('name', 'Meal')} ({calories} cal, {protein}g protein)\n"
                        
                        response_text += f"\n💡 **Total Daily**: {meal_plan['daily_totals']['calories']} calories, {meal_plan['daily_totals']['protein']}g protein\n\n"
                    
                    response_text += "🔥 Ready to start your nutrition journey? This plan is tailored for your goals!"
                    
                    response_data["response"] = response_text
                    response_data["nutrition_plan"] = result["data"]
                        
            elif tool_name == "get_stored_meal_plans":
                result = chatbot_tools.execute_tool("get_stored_meal_plans", user_id=user_id)
                
            elif tool_name == "answer_meal_plan_question":
                profile = get_user_profile(user_id)
                result = chatbot_tools.execute_tool("answer_meal_plan_question", question=user_message, user_id=user_id, user_profile=profile)
                if result["success"]:
                    response_data["response"] = result["data"]
                    
            elif tool_name == "get_stored_workout_plans":
                result = chatbot_tools.execute_tool("get_stored_workout_plans", user_id=user_id)
                
            elif tool_name == "answer_workout_plan_question":
                profile = get_user_profile(user_id)
                result = chatbot_tools.execute_tool("answer_workout_plan_question", question=user_message, user_id=user_id, user_profile=profile)
                if result["success"]:
                    response_data["response"] = result["data"]
                    
            elif tool_name == "quota_exceeded_response":
                response_data["response"] = "🚫 **API Quota Exceeded**\n\nI've reached my daily AI request limit (50 requests per day on the free tier). Please try again in 24 hours when my quota resets.\n\n⏰ **When to try again**: Tomorrow at the same time\n\n💡 **In the meantime**: You can still browse your saved workout and meal plans, or check out the basic fitness information I have stored.\n\nThank you for your patience! 🙏"
                result = {"success": True, "message": "Quota exceeded message displayed"}
                
            elif tool_name == "quota_exceeded_nutrition_response":
                response_data["response"] = "🚫 **API Quota Exceeded - Nutrition Request**\n\nI've reached my daily AI request limit, but I can still help with basic nutrition guidance!\n\n🍽️ **Basic Nutrition Tips**:\n• **Protein**: Aim for 1.6-2.2g per kg of body weight\n• **Carbs**: 45-65% of total calories for energy\n• **Fats**: 20-35% of total calories for hormones\n• **Water**: 8-10 glasses per day\n\n💡 **For detailed meal plans**: Please try again tomorrow when my AI quota resets.\n\nThank you for your patience! 🙏"
                result = {"success": True, "message": "Quota exceeded nutrition message displayed"}
                
            elif tool_name == "quota_exceeded_workout_response":
                response_data["response"] = "🚫 **API Quota Exceeded - Workout Request**\n\nI've reached my daily AI request limit, but here are some basic workout guidelines!\n\n💪 **Basic Workout Tips**:\n• **Frequency**: 3-4 times per week for beginners\n• **Compound exercises**: Squats, deadlifts, push-ups, pull-ups\n• **Progressive overload**: Gradually increase weight/reps\n• **Rest**: 48-72 hours between training same muscle groups\n• **Warm-up**: 5-10 minutes before each session\n\n💡 **For personalized workout plans**: Please try again tomorrow when my AI quota resets.\n\nThank you for your patience! 🙏"
                result = {"success": True, "message": "Quota exceeded workout message displayed"}
                    
            else:
                result = {"success": False, "error": f"Unknown tool: {tool_name}"}
            
            tool_results[tool_name] = result
            
        except Exception as e:
            tool_results[tool_name] = {"success": False, "error": str(e)}
    
    # Fallback response if nothing was generated
    if not response_data["response"]:
        response_data["response"] = "I'm here to help with your fitness and nutrition goals! How can I assist you today?"
    
    return response_data, tool_results

# execute_selected_tools function removed - was unused

def generate_workout_plan_json(user_data):
    """Generate structured workout plan JSON using RAG and context-aware approach"""
    try:
        # Map Supabase field names to expected field names
        mapped_data = user_data.copy()
        
        # Map fitness_goal to goal if needed
        if 'fitness_goal' in user_data and 'goal' not in user_data:
            mapped_data['goal'] = user_data['fitness_goal']
        
        # Ensure required fields have defaults
        mapped_data.setdefault('age', 25)
        mapped_data.setdefault('gender', 'male')
        mapped_data.setdefault('activity', 'moderate')
        mapped_data.setdefault('days', 3)
        
        # Get RAG-based workout suggestions
        from agent import build_workout_query
        from retriever import retrieve_workouts
        
        workout_query = build_workout_query(mapped_data)
        workout_evidence = retrieve_workouts(workout_query)[:3]  # Get top 3 RAG suggestions
        
        # Determine user context for specialized plans
        living_situation = user_data.get('living_situation', 'home')
        gym_access = user_data.get('gym_access', 'full_gym')
        cooking_ability = user_data.get('cooking_ability', 'can_cook')
        
        # Build context-specific constraints
        constraints = []
        if living_situation == 'hostel' or gym_access == 'no_gym':
            constraints.append("HOSTEL/NO GYM: Use only bodyweight exercises, no equipment needed")
        elif gym_access == 'home_gym':
            constraints.append("HOME GYM: Limited equipment - focus on dumbbells, resistance bands, bodyweight")
        elif gym_access == 'bodyweight_only':
            constraints.append("BODYWEIGHT ONLY: No equipment, calisthenics focus")
        
        workout_prompt = f"""
You are a professional fitness trainer with access to research-backed workout data. Create a detailed workout plan JSON for this user profile:

User Profile:
- Age: {user_data['age']}
- Weight: {user_data['weight']}kg
- Height: {user_data['height']}cm
- Gender: {user_data['gender']}
- Goal: {user_data['goal']}
- Activity Level: {user_data['activity']}
- Living Situation: {living_situation}
- Gym Access: {gym_access}
- Days per week: {user_data.get('days', 3)}

CONSTRAINTS: {' | '.join(constraints) if constraints else 'Full gym access available'}

Research-Based Evidence:
{' '.join(workout_evidence)}

Create a workout plan and return ONLY valid JSON in this exact format:
{{
    "goal": "{user_data['goal']}",
    "split": ["day_1", "day_2", "day_3"],
    "days": {user_data.get('days', 3)},
    "exercises": [
        {{
            "day": "day_1",
            "day_name": "Upper Body",
            "exercises": [
                {{
                    "name": "Bench Press",
                    "sets": 4,
                    "reps": "6-8",
                    "rest": "90-120s",
                    "muscle_groups": ["chest", "triceps", "shoulders"],
                    "equipment": "barbell",
                    "notes": "Focus on controlled movement"
                }},
                {{
                    "name": "Pull-ups",
                    "sets": 3,
                    "reps": "8-12",
                    "rest": "60-90s",
                    "muscle_groups": ["back", "biceps"],
                    "equipment": "pull-up bar",
                    "notes": "Use assistance if needed"
                }}
            ]
        }},
        {{
            "day": "day_2",
            "day_name": "Lower Body",
            "exercises": [
                {{
                    "name": "Squats",
                    "sets": 4,
                    "reps": "8-10",
                    "rest": "90-120s",
                    "muscle_groups": ["quadriceps", "glutes", "hamstrings"],
                    "equipment": "barbell",
                    "notes": "Keep chest up and knees tracking over toes"
                }}
            ]
        }}
    ]
}}

Requirements:
- Create {user_data.get('days', 3)} workout days
- Choose appropriate split based on goal and days per week
- Include 4-6 exercises per day
- Specify sets, reps, rest periods for each exercise
- Include muscle groups targeted
- Add helpful form notes
- Consider gym access and equipment availability

Return ONLY the JSON, no additional text.
"""

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            workout_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=2000,
                temperature=0.6,  # Slightly higher for more variation while keeping structure
            )
        )
        
        # Clean and parse the JSON response
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        import json
        workout_plan = json.loads(response_text)
        return workout_plan
        
    except Exception as e:
        pass
        return None

def store_workout_plan_in_fallback(user_id, workout_plan_json):
    """Store workout plan in fallback storage when Supabase is unavailable"""
    try:
        # Load current fallback profiles
        global fallback_profiles
        
        if user_id not in fallback_profiles:
            fallback_profiles[user_id] = {}
        
        # Store workout plans in user's profile
        if 'workout_plans' not in fallback_profiles[user_id]:
            fallback_profiles[user_id]['workout_plans'] = []
        
        # Add timestamp to the workout plan
        import datetime
        workout_plan_with_timestamp = workout_plan_json.copy()
        workout_plan_with_timestamp['created_at'] = datetime.datetime.now().isoformat()
        workout_plan_with_timestamp['user_id'] = user_id
        
        # Add to the list (keep only the latest 5 plans)
        fallback_profiles[user_id]['workout_plans'].append(workout_plan_with_timestamp)
        if len(fallback_profiles[user_id]['workout_plans']) > 5:
            fallback_profiles[user_id]['workout_plans'] = fallback_profiles[user_id]['workout_plans'][-5:]
        
        # Save to file
        save_fallback_profiles()
        
        return True
        
    except Exception as e:
        return False

def check_existing_workout_plans(user_id):
    """Check if user has existing workout plans with retry logic for network issues"""
    if not supabase:
        return []
    
    # Retry logic for intermittent network issues
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = supabase.table('workout_plans').select('*').eq('user_id', user_id).execute()
            
            if result.data and len(result.data) > 0:
                return result.data
            else:
                return []
                
        except Exception as e:
            if attempt == max_retries - 1:
                return []
            else:
                import time
                time.sleep(1)  # Wait 1 second before retry
    
    return []

def store_workout_plan_in_supabase(user_id, workout_plan_json, action="add"):
    """Store workout plan JSON in Supabase workout_plans table - PRIORITIZE SUPABASE
    
    Args:
        user_id: User identifier
        workout_plan_json: Workout plan data
        action: "add" to add new plan, "update" to replace existing plans
    """
    if not supabase:
        return False
    
    try:
        # If action is "update", delete existing plans first
        if action == "update":
            delete_result = supabase.table('workout_plans').delete().eq('user_id', user_id).execute()
        
        # Prepare data for Supabase
        workout_data = {
            'user_id': user_id,
            'goal': workout_plan_json.get('goal', 'General Fitness'),
            'split': workout_plan_json.get('split', []),
            'days': workout_plan_json.get('days', 7),
            'exercises': workout_plan_json.get('exercises', [])  # JSONB field
        }
        
        # Insert into workout_plans table
        result = supabase.table('workout_plans').insert(workout_data).execute()
        
        if result.data:
            return True
        else:
            return False
            
    except Exception as e:
        return False

def store_workout_plan_in_fallback(user_id, workout_plan_json, action="add"):
    """Store workout plan in fallback storage with update/add options"""
    global fallback_profiles
    
    # Initialize user profile if not exists
    if user_id not in fallback_profiles:
        fallback_profiles[user_id] = {}
    
    # Initialize workout_plans if not exists
    if 'workout_plans' not in fallback_profiles[user_id]:
        fallback_profiles[user_id]['workout_plans'] = []
    
    # If action is "update", clear existing plans
    if action == "update":
        fallback_profiles[user_id]['workout_plans'] = []
    
    # Add timestamp to the workout plan
    from datetime import datetime
    workout_plan_with_timestamp = {
        **workout_plan_json,
        "created_at": datetime.now().isoformat(),
        "action": action
    }
    
    # Add to the list
    fallback_profiles[user_id]['workout_plans'].append(workout_plan_with_timestamp)
    
    # Keep only the latest 10 plans to prevent unlimited growth
    if len(fallback_profiles[user_id]['workout_plans']) > 10:
        fallback_profiles[user_id]['workout_plans'] = fallback_profiles[user_id]['workout_plans'][-10:]
    
    # Save to file
    save_fallback_profiles()
    return True

# AI-powered intent classification using Gemini
# classify_user_intent function removed - was unused, replaced by AI orchestrator

def check_profile_completeness(profile):
    """Check if profile has minimum required information for plan generation"""
    missing_fields = []
    
    # Check weight
    if not profile.get('weight'):
        missing_fields.append('weight')
    
    # Check height  
    if not profile.get('height'):
        missing_fields.append('height')
    
    # Check goal (fitness_goal in Supabase, goal in some contexts)
    if not profile.get('fitness_goal') and not profile.get('goal'):
        missing_fields.append('goal')
    
    # Age is preferred but not strictly required - we can use a default
    if not profile.get('age'):
        pass  # Will use default age of 25 for calculations
    
    return missing_fields

def get_missing_fields_message(missing_fields):
    """Generate a friendly message asking for missing profile information"""
    field_prompts = {
        'age': 'your age (e.g., "I am 25 years old")',
        'weight': 'your weight (e.g., "I weigh 70kg")',
        'height': 'your height (e.g., "I am 175cm tall")',
        'goal': 'your fitness goal (e.g., "I want to build muscle" or "I want to lose weight")',
        'gender': 'your gender (male/female)'
    }
    
    if len(missing_fields) == 1:
        return f"To create a personalized plan, I need to know {field_prompts[missing_fields[0]]}."
    elif len(missing_fields) == 2:
        return f"To create a personalized plan, I need to know {field_prompts[missing_fields[0]]} and {field_prompts[missing_fields[1]]}."
    else:
        field_list = ", ".join([field_prompts[field] for field in missing_fields[:-1]])
        return f"To create a personalized plan, I need to know {field_list}, and {field_prompts[missing_fields[-1]]}."

# Supabase database functions with fallback
def get_user_profile(user_id):
    """Get user profile from Supabase with retry logic for network issues"""
    if not supabase:
        return {}
    
    # Retry logic for intermittent network issues
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
            
            if result.data and len(result.data) > 0:
                profile = result.data[0]
                return profile
            else:
                return {}
                
        except Exception as e:
            if attempt == max_retries - 1:
                return {}
            else:
                import time
                time.sleep(1)  # Wait 1 second before retry
    
    return {}

def update_user_profile(user_id, profile_data):
    """Update user profile in Supabase - PRIORITIZE SUPABASE DATA"""
    if supabase:
        try:
            # Check if profile exists
            existing = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
            
            if existing.data:
                # Update existing profile
                result = supabase.table('user_profiles').update(profile_data).eq('user_id', user_id).execute()
            else:
                # Create new profile
                profile_data['user_id'] = user_id
                result = supabase.table('user_profiles').insert(profile_data).execute()
            
            return True
        except Exception as e:
            return False
    else:
        return False

def get_profile_answer(question, user_id='default'):
    """Get answer for profile-related questions"""
    profile = get_user_profile(user_id)
    
    if 'age' in question.lower():
        return f"Your age is {profile.get('age', 'not set')}."
    elif 'weight' in question.lower():
        return f"Your weight is {profile.get('weight', 'not set')} kg."
    elif 'height' in question.lower():
        return f"Your height is {profile.get('height', 'not set')} cm."
    elif 'goal' in question.lower():
        goal = profile.get('goal', 'not set')
        goal_text = goal.replace('_', ' ').title() if goal != 'not set' else 'not set'
        return f"Your goal is {goal_text}."
    elif 'diet' in question.lower():
        return f"Your diet preference is {profile.get('diet', 'not set')}."
    elif 'profile' in question.lower() or 'stats' in question.lower():
        if not profile:
            return "You haven't shared any profile information yet. Tell me your age, weight, height, and goals!"
        
        profile_text = "Here's your profile:\n"
        if 'age' in profile:
            profile_text += f"• Age: {profile['age']}\n"
        if 'weight' in profile:
            profile_text += f"• Weight: {profile['weight']} kg\n"
        if 'height' in profile:
            profile_text += f"• Height: {profile['height']} cm\n"
        if 'goal' in profile:
            goal_text = profile['goal'].replace('_', ' ').title()
            profile_text += f"• Goal: {goal_text}\n"
        if 'diet' in profile:
            profile_text += f"• Diet: {profile['diet']}\n"
        
        return profile_text.strip()
    
    return "I'm not sure what you're asking about. Try asking about your age, weight, height, goal, or diet."

class ChatMessageWithAuth(BaseModel):
    message: str
    user_id: str = 'default'  # Optional user ID for authentication

def get_user_id_from_request(request_data):
    """Extract user ID from request or use default"""
    if hasattr(request_data, 'user_id') and request_data.user_id:
        return request_data.user_id
    return 'default'  # Fallback for anonymous users

@app.post("/chat")
def chat_with_agent(chat_message: ChatMessageWithAuth):
    """Pure AI-driven tool-based chatbot - no keywords, no fallbacks, just intelligent tool orchestration"""
    
    user_message = chat_message.message.strip()
    user_id = get_user_id_from_request(chat_message)
    
    try:
        # Step 1: AI decides what tools to use based on the message
        ai_decision = ai_tool_orchestrator(user_message, user_id)
        
        # Step 2: Execute the AI's decision
        response_data, tool_results = execute_ai_decision(ai_decision, user_message, user_id)
        
        # Step 3: Handle API quota errors gracefully
        if not response_data["response"]:
            response_data["response"] = "I'm here to help with your fitness and nutrition goals! How can I assist you today?"
        
        return response_data
        
    except Exception as e:
        error_message = str(e)
        
        # Handle specific API quota exceeded error
        if "429" in error_message and "quota" in error_message.lower():
            return {"response": "Sorry, I've reached my daily AI credit limit! 😅 Please try again tomorrow when my credits refresh. Thank you for your patience!"}
        
        # Handle other API errors
        elif "api" in error_message.lower() or "gemini" in error_message.lower():
            return {"response": "I'm having trouble connecting to my AI service right now. Please try again in a few minutes!"}
        
        # Generic error fallback
        else:
            return {"response": "Sorry, I encountered an issue. Please try again!"}
        # Old intent-based handling code removed - now using AI orchestrator
    
    except Exception as e:
        return {"response": "Sorry, I encountered an issue. Please try again!"}



@app.post("/meal-plan")
def generate_meal_plan(request: MealPlanRequest):
    """Generate a meal plan using AI based on goal and ingredients"""
    try:
        # Get RAG nutrition data for context
        nutrition_context = []
        try:
            nutrition_context = retrieve_nutrition(f"{request.goal} nutrition meal planning")[:2]
        except Exception as e:
            pass
        
        # Create prompt for meal plan generation
        dietary_restrictions_text = ""
        if request.dietary_restrictions:
            dietary_restrictions_text = f"Dietary Restrictions: {', '.join(request.dietary_restrictions)}"
        
        target_calories_text = ""
        if request.target_calories:
            target_calories_text = f"Target Daily Calories: {request.target_calories}"
        
        prompt = f"""
You are a professional nutritionist and chef. Create a detailed daily meal plan based on:

Goal: {request.goal}
Available Ingredients: {', '.join(request.ingredients)}
{dietary_restrictions_text}
{target_calories_text}

Nutrition Context: {' '.join(nutrition_context)}

Provide a JSON response with this exact structure:
{{
  "goal": "{request.goal}",
  "ingredients": {request.ingredients},
  "meals": [
    {{
      "name": "Meal name",
      "type": "breakfast",
      "calories": 400,
      "protein": 25,
      "carbs": 45,
      "fat": 15,
      "steps": ["Step 1", "Step 2", "Step 3"]
    }}
  ]
}}

Requirements:
- Create 3-4 meals (breakfast, lunch, dinner, optional snack)
- Use primarily the provided ingredients
- Align meals with the fitness goal
- Respect dietary restrictions
- Provide realistic macro calculations
- Include detailed cooking steps
- Make total calories appropriate for the goal

Respond ONLY with valid JSON, no additional text.
"""
        
        # Generate meal plan using Gemini
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=1500,
                temperature=0.7,
            )
        )
        
        # Clean and parse the response
        generated_text = response.text.strip()
        if generated_text.startswith('```json'):
            generated_text = generated_text.replace('```json\n', '').replace('\n```', '')
        if generated_text.startswith('```'):
            generated_text = generated_text.replace('```\n', '').replace('\n```', '')
        
        import json
        meal_plan = json.loads(generated_text)
        
        return {"mealPlan": meal_plan}
        
    except Exception as e:
        # Return a simple fallback meal plan
        fallback_plan = {
            "goal": request.goal,
            "ingredients": request.ingredients,
            "meals": [
                {
                    "name": "Simple Breakfast",
                    "type": "breakfast",
                    "calories": 350,
                    "protein": 20,
                    "carbs": 40,
                    "fat": 12,
                    "steps": [
                        f"Use available ingredients: {', '.join(request.ingredients[:3])}",
                        "Combine ingredients in a balanced way",
                        "Cook or prepare as needed"
                    ]
                },
                {
                    "name": "Balanced Lunch",
                    "type": "lunch",
                    "calories": 450,
                    "protein": 30,
                    "carbs": 45,
                    "fat": 15,
                    "steps": [
                        f"Prepare main ingredients: {', '.join(request.ingredients[:2])}",
                        "Add vegetables if available",
                        "Season and cook thoroughly"
                    ]
                },
                {
                    "name": "Nutritious Dinner",
                    "type": "dinner",
                    "calories": 500,
                    "protein": 35,
                    "carbs": 50,
                    "fat": 18,
                    "steps": [
                        f"Use protein source from: {', '.join(request.ingredients)}",
                        "Add complex carbohydrates",
                        "Include healthy fats"
                    ]
                }
            ]
        }
        return {"mealPlan": fallback_plan}

@app.get("/api/debug-profile/{user_id}")
def debug_profile(user_id: str = "default"):
    """Debug endpoint to check what's stored in user profile"""
    profile = get_user_profile(user_id)
    missing_fields = check_profile_completeness(profile)
    
    return {
        "user_id": user_id,
        "profile_data": profile,
        "missing_fields": missing_fields,
        "profile_complete": len(missing_fields) == 0,
        "supabase_connected": supabase is not None
    }

@app.get("/api/debug-supabase/{user_id}")
def debug_supabase_connection(user_id: str = "default"):
    """Debug endpoint to test Supabase connection and workout plan retrieval"""
    debug_info = {
        "supabase_connected": supabase is not None,
        "user_id": user_id,
        "workout_plans": [],
        "meal_plans": [],
        "error": None
    }
    
    if supabase:
        try:
            # Test workout plans query
            workout_result = supabase.table('workout_plans').select('*').eq('user_id', user_id).execute()
            debug_info["workout_plans"] = workout_result.data
            debug_info["workout_plans_count"] = len(workout_result.data) if workout_result.data else 0
            
            # Test meal plans query
            meal_result = supabase.table('meal_plans').select('*').eq('user_id', user_id).execute()
            debug_info["meal_plans"] = meal_result.data
            debug_info["meal_plans_count"] = len(meal_result.data) if meal_result.data else 0
            
        except Exception as e:
            debug_info["error"] = str(e)
    else:
        debug_info["error"] = "Supabase not connected - check credentials"
    
    return debug_info

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