import os
from dotenv import load_dotenv
import google.generativeai as genai
from retriever import retrieve_workouts, retrieve_nutrition
from food_api import get_food_suggestions
from macros import calculate_macros
from nutrition_planner import NutritionPlanner

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
You are an expert evidence-based fitness coach and nutritionist who creates highly personalized meal plans based on individual circumstances.

USER DETAILS:
Age: {user['age']} | Weight: {user['weight']}kg | Height: {user['height']}cm | Gender: {user['gender']}
Goal: {user['goal']} | Activity: {user['activity']} | Days/Week: {user['days']}
Living: {living_situation} | Cooking: {cooking_ability} | Gym: {gym_access}

IMPORTANT CONSTRAINTS TO FOLLOW:
{constraint_text}

CALCULATED MACROS:
Daily Calories: {macros['calories']} kcal | Protein: {macros['protein']}g | Carbs: {macros['carbs']}g | Fats: {macros['fats']}g

RESEARCH CONTEXT:
Workout Information: {workout_evidence}
Nutrition Information: {nutrition_evidence}
Food Suggestions: {foods}

CREATE A COMPREHENSIVE PERSONALIZED PLAN:

1. **DETAILED NUTRITION PLAN** (MOST IMPORTANT):
   
   Based on cooking ability, provide:
   
   IF NO COOKING ABILITY (Hostel/Student):
   - Complete daily meal plan with NO-COOK foods only
   - Exact portions and calorie breakdown for each meal
   - Ready-to-eat combinations (Greek yogurt + nuts + fruits, etc.)
   - Hostel-friendly storage and preparation tips
   - Weekly shopping list with estimated costs
   
   IF LIMITED COOKING (10-15 min meals):
   - Simple meal recipes with minimal equipment
   - Batch cooking strategies for the week
   - Quick preparation methods (overnight oats, boiled eggs, etc.)
   - Meal prep containers and storage advice
   
   IF FULL COOKING ACCESS:
   - Complete recipes with cooking instructions
   - Advanced meal prep strategies
   - Nutritionally optimized home-cooked meals
   - Kitchen equipment recommendations

   For ALL cooking levels, include:
   - **EXACT DAILY MEAL SCHEDULE**: Breakfast, lunch, dinner, 2 snacks
   - **SPECIFIC FOOD ITEMS WITH QUANTITIES**: "200g Greek yogurt", "30g almonds", etc.
   - **CALORIE BREAKDOWN**: Show calories for each meal and total daily intake
   - **MACRO TRACKING**: Protein/carbs/fats for each meal
   - **MEAL TIMING**: When to eat around workouts
   - **EMERGENCY BACKUP MEALS**: Quick options when short on time
   - **WEEKLY SHOPPING LIST**: Organized by food category with quantities

2. **WORKOUT PLAN**:
   - Specific exercises adapted to gym access
   - Sets, reps, and weekly schedule
   - Progression strategy over 4-8 weeks

3. **LIFESTYLE INTEGRATION**:
   - How to fit meals into their daily schedule
   - Budget optimization strategies
   - Time-saving meal prep techniques
   - Social eating situations management

4. **PROGRESS TRACKING**:
   - How to track calories and macros
   - Weekly weight/measurement schedule
   - When to adjust the plan

CRITICAL REQUIREMENTS:
- ALL meal suggestions MUST match their cooking ability
- Provide EXACT quantities and calorie counts
- Include realistic preparation times
- Consider their budget level in food choices
- Make it actionable and easy to follow

Format your response with clear sections and bullet points for easy reading.
"""
    
    return prompt

def generate_plan(user):
    # ✅ Macros
    macros = calculate_macros(
        user["weight"], user["height"], user["age"],
        user["gender"], user["goal"], user["activity"]
    )

    # ✅ Initialize nutrition planner for detailed meal plans
    nutrition_planner = NutritionPlanner()
    
    # ✅ Generate specific meal plan based on cooking ability
    cooking_ability = user.get('cooking_ability', 'can_cook')
    living_situation = user.get('living_situation', 'home')
    
    detailed_meal_plan = None
    if cooking_ability == 'no_cooking' or living_situation == 'hostel':
        detailed_meal_plan = nutrition_planner.generate_no_cook_meal_plan(
            macros['calories'], macros['protein']
        )
    elif cooking_ability == 'limited_cooking':
        detailed_meal_plan = nutrition_planner.generate_limited_cooking_plan(
            macros['calories'], macros['protein']
        )
    else:
        detailed_meal_plan = nutrition_planner.generate_full_cooking_plan(
            macros['calories'], macros['protein']
        )

    # ✅ Context-aware research retrieval
    workout_query = build_workout_query(user)
    nutrition_query = build_nutrition_query(user)
    
    workout_evidence = retrieve_workouts(workout_query)
    nutrition_evidence = retrieve_nutrition(nutrition_query)

    # ✅ Context-aware food suggestions
    food_query = build_food_query(user)
    foods = get_food_suggestions(food_query)

    # ✅ Enhanced context-aware prompt with detailed meal plan
    prompt = build_enhanced_prompt(user, macros, workout_evidence, nutrition_evidence, foods, detailed_meal_plan)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

def build_enhanced_prompt(user, macros, workout_evidence, nutrition_evidence, foods, detailed_meal_plan):
    """Build enhanced prompt with detailed meal plan integration"""
    
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
    
    # Format detailed meal plan for prompt
    meal_plan_text = ""
    if detailed_meal_plan and 'meals' in detailed_meal_plan:
        meal_plan_text = "\nDETAILED MEAL PLAN TEMPLATE:\n"
        for meal_name, meal_data in detailed_meal_plan['meals'].items():
            meal_plan_text += f"\n{meal_name.upper()}: {meal_data['name']}\n"
            meal_plan_text += f"Calories: {meal_data['total_calories']} | Protein: {meal_data['total_protein']}g\n"
            for food in meal_data['foods']:
                meal_plan_text += f"- {food['item']} ({food['quantity']}): {food['calories']} cal, {food['protein']}g protein\n"
            meal_plan_text += f"Prep: {meal_data['prep_instructions']}\n"
        
        if 'daily_totals' in detailed_meal_plan:
            meal_plan_text += f"\nDAILY TOTALS: {detailed_meal_plan['daily_totals']['calories']} calories, {detailed_meal_plan['daily_totals']['protein']}g protein\n"
        
        if 'hostel_tips' in detailed_meal_plan:
            meal_plan_text += "\nHOSTEL/NO-COOK TIPS:\n"
            for tip in detailed_meal_plan['hostel_tips']:
                meal_plan_text += f"- {tip}\n"
        
        if 'shopping_list' in detailed_meal_plan:
            meal_plan_text += "\nWEEKLY SHOPPING LIST:\n"
            for category, items in detailed_meal_plan['shopping_list'].items():
                meal_plan_text += f"{category.upper()}: {', '.join(items)}\n"
    
    prompt = f"""
You are an expert evidence-based fitness coach and nutritionist who creates highly personalized meal plans based on individual circumstances.

USER DETAILS:
Age: {user['age']} | Weight: {user['weight']}kg | Height: {user['height']}cm | Gender: {user['gender']}
Goal: {user['goal']} | Activity: {user['activity']} | Days/Week: {user['days']}
Living: {living_situation} | Cooking: {cooking_ability} | Gym: {gym_access}

IMPORTANT CONSTRAINTS TO FOLLOW:
{constraint_text}

CALCULATED MACROS:
Daily Calories: {macros['calories']} kcal | Protein: {macros['protein']}g | Carbs: {macros['carbs']}g | Fats: {macros['fats']}g

RESEARCH CONTEXT:
Workout Information: {workout_evidence}
Nutrition Information: {nutrition_evidence}
Food Suggestions: {foods}

{meal_plan_text}

CREATE A COMPREHENSIVE PERSONALIZED PLAN:

1. **PERSONALIZED NUTRITION PLAN** (MOST IMPORTANT):
   
   Use the detailed meal plan template above as your foundation and adapt it to the user's specific needs:
   
   - **DAILY MEAL SCHEDULE**: Present the complete meal plan with exact timings
   - **CALORIE & MACRO BREAKDOWN**: Show how each meal contributes to daily targets
   - **PREPARATION INSTRUCTIONS**: Specific to their cooking ability level
   - **PORTION ADJUSTMENTS**: Scale portions to match their exact calorie needs ({macros['calories']} calories)
   - **MEAL TIMING**: Optimize around their workout schedule
   - **SHOPPING LIST**: Organized and budget-conscious for their situation
   - **STORAGE & PREP TIPS**: Especially important for hostel/no-cook situations

2. **WORKOUT PLAN**:
   - Specific exercises adapted to gym access ({gym_access})
   - Sets, reps, and weekly schedule for {user['days']} days
   - Progression strategy over 4-8 weeks
   - Exercise alternatives based on available equipment

3. **LIFESTYLE INTEGRATION**:
   - How to fit meals and workouts into their daily routine
   - Budget optimization strategies (especially if {budget_level} budget)
   - Time-saving techniques for their situation
   - Social eating and dining out strategies

4. **PROGRESS TRACKING & ADJUSTMENTS**:
   - How to track calories and macros effectively
   - Weekly measurement and progress assessment
   - When and how to adjust portions and exercises
   - Signs that the plan is working

CRITICAL REQUIREMENTS:
- Use the provided meal plan template as your foundation
- ALL suggestions MUST match their cooking ability ({cooking_ability})
- Provide EXACT quantities and calorie counts for each meal
- Include realistic preparation times and methods
- Consider their budget level ({budget_level}) in all recommendations
- Make everything actionable and immediately implementable

Format your response with clear sections, bullet points, and easy-to-follow instructions.
"""
    
    return prompt

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
