from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import generate_plan
import google.generativeai as genai
import os
import re
from dotenv import load_dotenv
from retriever import retrieve_workouts, retrieve_nutrition

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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

@app.get("/api/performance")
def performance_test():
    """Test response times for different components"""
    import time
    from cache_manager import ResponseCache
    from fallback_responses import FallbackResponseSystem
    from macros import MacroCalculator
    
    results = {}
    
    # Test cache
    start = time.time()
    cache = ResponseCache()
    cache.get_cached_response("test message")
    results["cache_check"] = f"{(time.time() - start) * 1000:.2f}ms"
    
    # Test fallback
    start = time.time()
    fallback = FallbackResponseSystem()
    fallback.get_fallback_response("what is protein")
    results["fallback_response"] = f"{(time.time() - start) * 1000:.2f}ms"
    
    # Test calculator
    start = time.time()
    calculator = MacroCalculator()
    calculator.generate_response("I'm 25, 70kg, 175cm, calculate my calories")
    results["calculator_response"] = f"{(time.time() - start) * 1000:.2f}ms"
    
    # Test RAG retrieval
    start = time.time()
    try:
        retrieve_workouts("weight loss workout")[:1]
        results["rag_retrieval"] = f"{(time.time() - start) * 1000:.2f}ms"
    except Exception as e:
        results["rag_retrieval"] = f"Error: {str(e)}"
    
    return {
        "performance_metrics": results,
        "recommendations": {
            "cache_check": "Should be < 5ms",
            "fallback_response": "Should be < 50ms", 
            "calculator_response": "Should be < 100ms",
            "rag_retrieval": "Should be < 500ms"
        }
    }

@app.post("/chat")
def chat_with_agent(chat_message: ChatMessage):
    """Chat endpoint for conversational interactions with the fitness agent"""
    from fallback_responses import FallbackResponseSystem
    import time
    
    # Initialize fallback system (only for greetings)
    fallback = FallbackResponseSystem()
    start_time = time.time()
    
    try:
        user_message = chat_message.message.strip()
        
        # Only handle greetings locally - everything else goes to API
        if fallback.is_greeting(user_message):
            response = fallback.get_greeting_response()
            print(f"Greeting response - Response time: {time.time() - start_time:.2f}s")
            return {"response": response}
        
        # All other messages go directly to API for better personalized responses
        print(f"Using API for: {user_message[:50]}...")
        
        # Check if this is a personal request with details
        has_personal_details = any(re.search(pattern, user_message.lower()) for pattern in [
            r'\bi am \d+', r'\b\d+\s*(?:years?\s*old|yo|age)\b', r'\b\d+\s*(?:kg|kgs|pounds?|lbs?)\b',
            r'\b\d+\s*(?:cm|ft|feet)\b', r'\b\d+\s*%\s*(?:fat|body fat)\b'
        ])
        
        is_plan_request = any(keyword in user_message.lower() for keyword in [
            'plan', 'routine', 'workout', 'meal', 'diet', 'exercise', 'training',
            'build muscle', 'lose fat', 'lose weight', 'gain muscle', 'body recomposition'
        ])
        
        # Get RAG data for better context
        workout_info = []
        nutrition_info = []
        
        try:
            workout_info = retrieve_workouts(user_message)[:2]
            nutrition_info = retrieve_nutrition(user_message)[:2]
            print(f"Retrieved RAG data - Workout: {len(workout_info)} items, Nutrition: {len(nutrition_info)} items")
        except Exception as e:
            print(f"RAG retrieval error: {e}")
        
        # Extract user context for personalized nutrition planning
        user_context = _extract_user_context(user_message)
        
        # Create appropriate prompt based on request type
        if has_personal_details and is_plan_request:
            # Comprehensive prompt for personal requests with details
            prompt = f"""
You are an expert fitness coach and nutritionist specializing in personalized meal planning based on individual circumstances and cooking abilities.

User Request: {user_message}

User Context Analysis:
- Living Situation: {user_context['living_situation']}
- Cooking Ability: {user_context['cooking_ability']}
- Time Availability: {user_context['time_availability']}
- Budget Level: {user_context['budget_level']}

Research Context:
Workout Information: {' '.join(workout_info)}
Nutrition Information: {' '.join(nutrition_info)}

Create a detailed, personalized plan that includes:

1. **CALORIE & MACRO CALCULATION**:
   - Calculate BMR and TDEE based on provided stats
   - Recommend specific calorie target for their goal
   - Provide exact macro breakdown (protein, carbs, fats in grams)

2. **PERSONALIZED NUTRITION PLAN** (MOST IMPORTANT):
   
   Based on cooking ability ({user_context['cooking_ability']}), provide:
   
   IF NO COOKING ABILITY (Hostel/Student/Busy):
   - **COMPLETE NO-COOK DAILY MEAL PLAN**:
     • Breakfast: Greek yogurt (200g, 120 cal) + banana (100g, 89 cal) + almonds (30g, 174 cal) = 383 cal
     • Mid-morning: Boiled eggs (2, 140 cal) + apple (150g, 78 cal) = 218 cal
     • Lunch: Cottage cheese (150g, 165 cal) + whole grain bread (2 slices, 160 cal) + peanut butter (2 tbsp, 190 cal) = 515 cal
     • Pre-workout: Protein shake (1 scoop + milk, 250 cal)
     • Post-workout: Chocolate milk (300ml, 180 cal) + banana (89 cal) = 269 cal
     • Dinner: Curd (300g, 180 cal) + mixed nuts (30g, 180 cal) + dates (3, 60 cal) = 420 cal
     • Before bed: Milk (250ml, 150 cal) + almonds (20g, 116 cal) = 266 cal
     • **TOTAL: ~2300 calories** (adjust portions based on their target)
   
   - **HOSTEL-SPECIFIC TIPS**:
     • Storage: Small fridge for dairy, airtight containers for nuts
     • Preparation: Pre-boil eggs weekly, overnight oats setup
     • Budget hacks: Buy nuts in bulk, seasonal fruits, local dairy
   
   IF LIMITED COOKING (10-15 min meals):
   - **SIMPLE COOKING MEAL PLAN**:
     • Breakfast: Overnight oats (80g oats + 300ml milk + fruits) = 450 cal
     • Lunch: Scrambled eggs (3) + toast (2 slices) + avocado = 520 cal
     • Dinner: Instant noodles + boiled eggs (2) + vegetables = 480 cal
   - **BATCH COOKING**: Boil 10 eggs Sunday, prepare overnight oats for 3 days
   
   IF FULL COOKING ACCESS:
   - **COMPLETE RECIPES WITH INSTRUCTIONS**:
     • Breakfast: Protein pancakes (recipe with exact measurements)
     • Lunch: Chicken rice bowl (cooking steps included)
     • Dinner: Salmon with quinoa (full recipe)
   - **MEAL PREP STRATEGIES**: Sunday prep for entire week
   
   For ALL levels, include:
   - **EXACT QUANTITIES**: "200g Greek yogurt", "30g almonds", "2 slices bread"
   - **CALORIE BREAKDOWN**: Show calories for each meal and daily total
   - **MACRO TRACKING**: Protein/carbs/fats for each meal
   - **WEEKLY SHOPPING LIST**: Organized by category with exact quantities needed
   - **MEAL TIMING**: When to eat around workouts
   - **BACKUP OPTIONS**: Quick alternatives when short on time

3. **WORKOUT PLAN**:
   - Specific exercises for their goal and available equipment
   - Sets, reps, and weekly schedule
   - Progression strategy over 4-8 weeks

4. **LIFESTYLE INTEGRATION**:
   - How to fit meals into their daily schedule
   - Budget optimization (cost per meal breakdown)
   - Time-saving strategies
   - Social eating management

5. **PROGRESS TRACKING**:
   - How to track calories and macros (app recommendations)
   - Weekly measurement schedule
   - When and how to adjust the plan

CRITICAL: Make it extremely practical and actionable. Provide exact foods, quantities, preparation methods, and costs they can implement immediately in their specific situation.
"""
        elif is_plan_request:
            # Plan request without personal details
            prompt = f"""
You are a fitness coach. The user wants a plan but hasn't provided personal details.

User Request: {user_message}

Research Context: {' '.join(workout_info[:1])} {' '.join(nutrition_info[:1])}

Provide a general plan structure and ask for their personal details (age, weight, height, gender, activity level) to create a personalized plan. Include:

1. Basic plan outline for their goal
2. Why personal details are important for customization
3. What specific information you need from them

Keep it helpful but emphasize the need for personalization.
"""
        else:
            # General fitness question - still use API for better answers
            prompt = f"""
You are an expert fitness coach and nutritionist. Answer the user's question with detailed, research-backed information.

Question: {user_message}

Research Context: {' '.join(workout_info[:1])} {' '.join(nutrition_info[:1])}

Provide a comprehensive, actionable answer. Include specific tips, examples, and practical advice. If they need a personalized approach, suggest they share their details (age, weight, height, goals).
"""
        
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            # Adjust token limit based on request type
            if has_personal_details and is_plan_request:
                max_tokens = 800  # More tokens for detailed personal plans
            elif is_plan_request:
                max_tokens = 500  # Medium tokens for general plans
            else:
                max_tokens = 300  # More tokens for detailed answers to simple questions
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7,
                )
            )
            
            api_response = response.text
            print(f"API response - Response time: {time.time() - start_time:.2f}s")
            return {"response": api_response}
            
        except Exception as api_error:
            print(f"API error: {api_error}")
            error_message = str(api_error)
            
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
            
            # For other API errors, return a simple error message
            return {"response": "I'm having a temporary issue connecting to my AI brain 🤖. Please try again in a moment!"}
        
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