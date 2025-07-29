import os
from dotenv import load_dotenv
import google.generativeai as genai
from retriever import retrieve_workouts, retrieve_nutrition
from food_api import get_food_suggestions
from macros import calculate_macros

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY") or "YOUR_GEMINI_KEY_HERE")

def build_workout_query(user):
    """Build context-aware workout query based on user constraints"""
    base_query = f"best workout for {user['goal']}"
    
    # Add gym access context
    gym_access = user.get('gym_access', 'full_gym')
    if gym_access == 'no_gym' or gym_access == 'bodyweight_only':
        base_query += " calisthenics bodyweight home workout"
    elif gym_access == 'home_gym':
        base_query += " home gym limited equipment"
    
    # Add equipment context
    equipment = user.get('equipment_available', [])
    if equipment:
        base_query += f" using {' '.join(equipment)}"
    
    return base_query

def build_nutrition_query(user):
    """Build context-aware nutrition query based on user constraints"""
    base_query = f"nutrition for {user['goal']} {user.get('diet', '')}"
    
    # Add cooking ability context
    cooking_ability = user.get('cooking_ability', 'can_cook')
    living_situation = user.get('living_situation', 'home')
    
    if cooking_ability == 'no_cooking' or living_situation == 'hostel':
        base_query += " no cook meals hostel nutrition"
    elif cooking_ability == 'limited_cooking':
        base_query += " minimal cooking simple meals"
    
    return base_query

def build_food_query(user):
    """Build context-aware food query for API"""
    base_query = f"{user['goal']} {user.get('diet', '')} high protein"
    
    # Add context based on constraints
    cooking_ability = user.get('cooking_ability', 'can_cook')
    living_situation = user.get('living_situation', 'home')
    
    if cooking_ability == 'no_cooking' or living_situation == 'hostel':
        base_query += " no cook ready to eat"
    
    return base_query

def build_context_aware_prompt(user, macros, workout_evidence, nutrition_evidence, foods):
    """Build a context-aware prompt based on user constraints"""
    
    # Determine user constraints
    gym_access = user.get('gym_access', 'full_gym')
    cooking_ability = user.get('cooking_ability', 'can_cook')
    living_situation = user.get('living_situation', 'home')
    equipment = user.get('equipment_available', [])
    dietary_restrictions = user.get('dietary_restrictions', [])
    budget_level = user.get('budget_level', 'moderate')
    
    # Build constraint context
    constraints = []
    if gym_access == 'no_gym' or gym_access == 'bodyweight_only':
        constraints.append("NO GYM ACCESS - Must use bodyweight/calisthenics exercises only")
    elif gym_access == 'home_gym':
        constraints.append(f"HOME GYM - Limited equipment: {', '.join(equipment) if equipment else 'basic equipment'}")
    
    if cooking_ability == 'no_cooking' or living_situation == 'hostel':
        constraints.append("NO COOKING ABILITY - Must suggest no-cook, ready-to-eat meals only")
    elif cooking_ability == 'limited_cooking':
        constraints.append("LIMITED COOKING - Prefer simple, minimal cooking meals")
    
    if dietary_restrictions:
        constraints.append(f"DIETARY RESTRICTIONS: {', '.join(dietary_restrictions)}")
    
    if budget_level == 'low':
        constraints.append("LOW BUDGET - Focus on affordable, cost-effective options")
    
    constraint_text = "\n".join([f"- {c}" for c in constraints]) if constraints else "No specific constraints"
    
    prompt = f"""
You are an expert evidence-based fitness coach who adapts recommendations to user constraints.

USER DETAILS:
Age: {user['age']} | Weight: {user['weight']}kg | Height: {user['height']}cm
Goal: {user['goal']} | Activity: {user['activity']} | Days/Week: {user['days']}
Living: {living_situation} | Cooking: {cooking_ability} | Gym: {gym_access}

IMPORTANT CONSTRAINTS TO FOLLOW:
{constraint_text}

MACROS:
Calories {macros['calories']} kcal | Protein {macros['protein']}g | Carbs {macros['carbs']}g | Fats {macros['fats']}g

WORKOUT RESEARCH:
{workout_evidence}

NUTRITION RESEARCH:
{nutrition_evidence}

FOOD OPTIONS:
{foods}

TASK - ADAPT ALL RECOMMENDATIONS TO USER CONSTRAINTS:
1. **WORKOUT PLAN**: 
   - If NO GYM: Provide bodyweight/calisthenics exercises with progressions
   - If HOME GYM: Use available equipment or suggest alternatives
   - If FULL GYM: Provide complete gym-based routine
   - Include specific exercises, sets, reps, and progression methods

2. **NUTRITION PLAN**:
   - If NO COOKING: Focus on ready-to-eat foods (yogurt, eggs, nuts, fruits, protein powder, etc.)
   - If LIMITED COOKING: Simple preparations (boiled eggs, overnight oats, etc.)
   - If CAN COOK: Full cooking options
   - Provide specific meal examples with portions

3. **PRACTICAL ADAPTATIONS**:
   - Suggest equipment alternatives if needed
   - Provide food swaps based on availability/budget
   - Include shopping lists for the user's situation

4. **TIMELINE**: Realistic timeline considering constraints

CRITICAL: Your recommendations MUST work within the user's constraints. Don't suggest gym exercises if they have no gym access, or cooking meals if they can't cook.

Respond in a clear, structured format with practical, actionable advice.
"""
    
    return prompt

def generate_plan(user):
    # ✅ Macros
    macros = calculate_macros(
        user["weight"], user["height"], user["age"],
        user["gender"], user["goal"], user["activity"]
    )

    # ✅ Context-aware research retrieval
    workout_query = build_workout_query(user)
    nutrition_query = build_nutrition_query(user)
    
    workout_evidence = retrieve_workouts(workout_query)
    nutrition_evidence = retrieve_nutrition(nutrition_query)

    # ✅ Context-aware food suggestions
    food_query = build_food_query(user)
    foods = get_food_suggestions(food_query)

    # ✅ Context-aware prompt
    prompt = build_context_aware_prompt(user, macros, workout_evidence, nutrition_evidence, foods)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

if __name__ == "__main__":
    user = {
        "age": 25,
        "weight": 80,
        "height": 175,
        "gender": "male",
        "goal": "muscle_gain",
        "activity": "moderate",
        "diet": "vegetarian",
        "days": 4
    }
    print(generate_plan(user))
