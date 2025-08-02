import os
import json
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
from datetime import datetime

# Import existing components
from retriever import FitnessRetriever
from cache_manager import CacheManager
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MealPlan:
    """Data class for meal plan structure"""
    goal: str
    ingredients: List[str]
    meals: List[Dict[str, Any]]
    total_calories: int
    total_protein: float
    total_carbs: float
    total_fat: float
    created_at: str

@dataclass
class Recipe:
    """Data class for recipe structure"""
    id: str
    name: str
    ingredients: List[str]
    instructions: List[str]
    nutrition: Dict[str, float]
    prep_time: int
    cook_time: int
    servings: int
    image_url: Optional[str] = None

class MealAPIClient:
    """Client for interacting with meal/recipe APIs"""
    
    def __init__(self):
        self.spoonacular_key = os.getenv('SPOONACULAR_API_KEY')
        self.edamam_app_id = os.getenv('EDAMAM_APP_ID')
        self.edamam_app_key = os.getenv('EDAMAM_APP_KEY')
        
    def search_recipes_spoonacular(self, ingredients: List[str], diet: str = None, 
                                 max_results: int = 10) -> List[Recipe]:
        """Search for recipes using Spoonacular API"""
        if not self.spoonacular_key:
            logger.warning("Spoonacular API key not found")
            return []
            
        url = "https://api.spoonacular.com/recipes/findByIngredients"
        params = {
            'apiKey': self.spoonacular_key,
            'ingredients': ','.join(ingredients),
            'number': max_results,
            'ranking': 2,  # Maximize used ingredients
            'ignorePantry': True
        }
        
        if diet:
            params['diet'] = diet
            
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            recipes = []
            for recipe_data in response.json():
                # Get detailed recipe information
                detailed_recipe = self._get_recipe_details_spoonacular(recipe_data['id'])
                if detailed_recipe:
                    recipes.append(detailed_recipe)
                    
            return recipes
            
        except requests.RequestException as e:
            logger.error(f"Error searching Spoonacular recipes: {e}")
            return []
    
    def _get_recipe_details_spoonacular(self, recipe_id: str) -> Optional[Recipe]:
        """Get detailed recipe information from Spoonacular"""
        url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
        params = {
            'apiKey': self.spoonacular_key,
            'includeNutrition': True
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract nutrition information
            nutrition = {}
            if 'nutrition' in data and 'nutrients' in data['nutrition']:
                for nutrient in data['nutrition']['nutrients']:
                    name = nutrient['name'].lower()
                    if name in ['calories', 'protein', 'carbohydrates', 'fat']:
                        nutrition[name] = nutrient['amount']
            
            # Extract instructions
            instructions = []
            if 'analyzedInstructions' in data and data['analyzedInstructions']:
                for instruction_group in data['analyzedInstructions']:
                    if 'steps' in instruction_group:
                        for step in instruction_group['steps']:
                            instructions.append(step['step'])
            
            # Extract ingredients
            ingredients = []
            if 'extendedIngredients' in data:
                ingredients = [ing['original'] for ing in data['extendedIngredients']]
            
            return Recipe(
                id=str(data['id']),
                name=data['title'],
                ingredients=ingredients,
                instructions=instructions,
                nutrition=nutrition,
                prep_time=data.get('preparationMinutes', 0),
                cook_time=data.get('cookingMinutes', 0),
                servings=data.get('servings', 1),
                image_url=data.get('image')
            )
            
        except requests.RequestException as e:
            logger.error(f"Error getting recipe details: {e}")
            return None
    
    def analyze_nutrition_spoonacular(self, ingredients: List[str]) -> Dict[str, float]:
        """Analyze nutrition using Spoonacular API"""
        if not self.spoonacular_key:
            logger.warning("Spoonacular API key not found")
            return {}
            
        # Use Spoonacular's ingredient search and nutrition analysis
        nutrition_totals = {
            'calories': 0,
            'protein': 0,
            'carbohydrates': 0,
            'fat': 0,
            'fiber': 0,
            'sugar': 0,
            'sodium': 0
        }
        
        try:
            for ingredient in ingredients:
                # Search for ingredient to get nutrition info
                url = f"https://api.spoonacular.com/food/ingredients/search"
                params = {
                    'apiKey': self.spoonacular_key,
                    'query': ingredient,
                    'number': 1,
                    'metaInformation': True
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data.get('results'):
                    ingredient_id = data['results'][0]['id']
                    
                    # Get detailed nutrition information
                    nutrition_url = f"https://api.spoonacular.com/food/ingredients/{ingredient_id}/information"
                    nutrition_params = {
                        'apiKey': self.spoonacular_key,
                        'amount': 1,
                        'unit': 'serving'
                    }
                    
                    nutrition_response = requests.get(nutrition_url, params=nutrition_params, timeout=10)
                    nutrition_response.raise_for_status()
                    nutrition_data = nutrition_response.json()
                    
                    # Extract nutrition values
                    if 'nutrition' in nutrition_data and 'nutrients' in nutrition_data['nutrition']:
                        for nutrient in nutrition_data['nutrition']['nutrients']:
                            name = nutrient['name'].lower()
                            amount = nutrient.get('amount', 0)
                            
                            if 'calorie' in name or name == 'energy':
                                nutrition_totals['calories'] += amount
                            elif 'protein' in name:
                                nutrition_totals['protein'] += amount
                            elif 'carbohydrate' in name or 'carbs' in name:
                                nutrition_totals['carbohydrates'] += amount
                            elif name == 'fat' or 'total fat' in name:
                                nutrition_totals['fat'] += amount
                            elif 'fiber' in name:
                                nutrition_totals['fiber'] += amount
                            elif 'sugar' in name:
                                nutrition_totals['sugar'] += amount
                            elif 'sodium' in name:
                                nutrition_totals['sodium'] += amount
                
            return nutrition_totals
            
        except requests.RequestException as e:
            logger.error(f"Error analyzing nutrition with Spoonacular: {e}")
            return {}

class MealRAGAgent:
    """RAG Agent for intelligent meal planning combining APIs and AI"""
    
    def __init__(self):
        # Initialize components
        self.retriever = FitnessRetriever()
        self.cache_manager = CacheManager()
        self.meal_api = MealAPIClient()
        
        # Initialize Gemini
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Load nutrition knowledge base
        self._load_nutrition_knowledge()
    
    def _load_nutrition_knowledge(self):
        """Load nutrition-related documents into the retriever"""
        try:
            # Add nutrition documents to the retriever if not already loaded
            nutrition_docs = [
                "pdfs/nutrition/nutrition_basics.txt",
                "pdfs/nutrition/hostel_nutrition.txt"
            ]
            
            for doc_path in nutrition_docs:
                if os.path.exists(doc_path):
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self.retriever.add_document(content, doc_path)
                        
        except Exception as e:
            logger.error(f"Error loading nutrition knowledge: {e}")
    
    def generate_meal_plan(self, goal: str, ingredients: List[str], 
                          dietary_restrictions: List[str] = None,
                          target_calories: int = None) -> MealPlan:
        """Generate a comprehensive meal plan using RAG + APIs + AI"""
        
        # Create cache key
        cache_key = f"meal_plan_{hash(goal + str(ingredients) + str(dietary_restrictions))}"
        
        # Check cache first
        cached_plan = self.cache_manager.get(cache_key)
        if cached_plan:
            logger.info("Returning cached meal plan")
            return MealPlan(**cached_plan)
        
        try:
            # Step 1: Retrieve relevant nutrition knowledge
            nutrition_context = self._get_nutrition_context(goal, ingredients)
            
            # Step 2: Search for recipes using meal APIs
            api_recipes = self._search_api_recipes(ingredients, dietary_restrictions)
            
            # Step 3: Generate meal plan using Gemini with context
            meal_plan = self._generate_ai_meal_plan(
                goal, ingredients, nutrition_context, api_recipes, 
                dietary_restrictions, target_calories
            )
            
            # Step 4: Enhance with API nutrition data
            enhanced_plan = self._enhance_with_api_nutrition(meal_plan)
            
            # Cache the result
            self.cache_manager.set(cache_key, enhanced_plan.__dict__, expire_hours=24)
            
            return enhanced_plan
            
        except Exception as e:
            logger.error(f"Error generating meal plan: {e}")
            # Fallback to basic AI generation
            return self._generate_fallback_meal_plan(goal, ingredients)
    
    def _get_nutrition_context(self, goal: str, ingredients: List[str]) -> str:
        """Retrieve relevant nutrition context using RAG"""
        # Create query combining goal and ingredients
        query = f"nutrition advice for {goal} using ingredients: {', '.join(ingredients)}"
        
        # Retrieve relevant documents
        relevant_docs = self.retriever.retrieve(query, top_k=3)
        
        # Combine retrieved context
        context = "\n\n".join([doc['content'] for doc in relevant_docs])
        
        return context
    
    def _search_api_recipes(self, ingredients: List[str], 
                           dietary_restrictions: List[str] = None) -> List[Recipe]:
        """Search for recipes using meal APIs"""
        recipes = []
        
        # Determine diet parameter for API
        diet = None
        if dietary_restrictions:
            diet_mapping = {
                'vegetarian': 'vegetarian',
                'vegan': 'vegan',
                'gluten-free': 'gluten free',
                'keto': 'ketogenic',
                'paleo': 'paleo'
            }
            for restriction in dietary_restrictions:
                if restriction.lower() in diet_mapping:
                    diet = diet_mapping[restriction.lower()]
                    break
        
        # Search using Spoonacular
        spoonacular_recipes = self.meal_api.search_recipes_spoonacular(
            ingredients, diet=diet, max_results=5
        )
        recipes.extend(spoonacular_recipes)
        
        return recipes
    
    def _generate_ai_meal_plan(self, goal: str, ingredients: List[str], 
                              nutrition_context: str, api_recipes: List[Recipe],
                              dietary_restrictions: List[str] = None,
                              target_calories: int = None) -> MealPlan:
        """Generate meal plan using Gemini AI with context"""
        
        # Prepare API recipes context
        recipes_context = ""
        if api_recipes:
            recipes_context = "Available recipes from database:\n"
            for recipe in api_recipes[:3]:  # Limit to top 3
                recipes_context += f"- {recipe.name}: {', '.join(recipe.ingredients[:5])}\n"
        
        # Prepare dietary restrictions
        restrictions_text = ""
        if dietary_restrictions:
            restrictions_text = f"Dietary restrictions: {', '.join(dietary_restrictions)}"
        
        # Prepare target calories
        calories_text = ""
        if target_calories:
            calories_text = f"Target daily calories: {target_calories}"
        
        prompt = f"""
You are a professional nutritionist and meal planning expert. Create a detailed daily meal plan based on the following information:

GOAL: {goal}
AVAILABLE INGREDIENTS: {', '.join(ingredients)}
{restrictions_text}
{calories_text}

NUTRITION KNOWLEDGE CONTEXT:
{nutrition_context}

{recipes_context}

Please create a comprehensive meal plan with the following JSON structure:
{{
  "goal": "{goal}",
  "ingredients": {json.dumps(ingredients)},
  "meals": [
    {{
      "name": "Meal name",
      "type": "breakfast|lunch|dinner|snack",
      "calories": number,
      "protein": number (in grams),
      "carbs": number (in grams),
      "fat": number (in grams),
      "fiber": number (in grams),
      "ingredients_used": ["ingredient1", "ingredient2"],
      "steps": ["Step 1", "Step 2", "Step 3"],
      "prep_time": number (in minutes),
      "cook_time": number (in minutes),
      "tips": "Optional cooking tips or modifications"
    }}
  ]
}}

REQUIREMENTS:
- Create 3-4 meals (breakfast, lunch, dinner, and optionally a snack)
- Use primarily the provided ingredients
- Ensure meals align with the fitness goal
- Provide realistic macro calculations based on nutrition knowledge
- Include detailed cooking steps for each meal
- Consider the available recipes from the database when possible
- Make sure total daily calories are appropriate for the goal
- Include prep and cook times
- Add helpful cooking tips where relevant

Respond ONLY with valid JSON, no additional text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up JSON response
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json\n', '').replace('\n```', '')
            elif response_text.startswith('```'):
                response_text = response_text.replace('```\n', '').replace('\n```', '')
            
            meal_data = json.loads(response_text)
            
            # Calculate totals
            total_calories = sum(meal.get('calories', 0) for meal in meal_data['meals'])
            total_protein = sum(meal.get('protein', 0) for meal in meal_data['meals'])
            total_carbs = sum(meal.get('carbs', 0) for meal in meal_data['meals'])
            total_fat = sum(meal.get('fat', 0) for meal in meal_data['meals'])
            
            return MealPlan(
                goal=meal_data['goal'],
                ingredients=meal_data['ingredients'],
                meals=meal_data['meals'],
                total_calories=total_calories,
                total_protein=total_protein,
                total_carbs=total_carbs,
                total_fat=total_fat,
                created_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error generating AI meal plan: {e}")
            raise
    
    def _enhance_with_api_nutrition(self, meal_plan: MealPlan) -> MealPlan:
        """Enhance meal plan with accurate nutrition data from APIs"""
        try:
            for meal in meal_plan.meals:
                if 'ingredients_used' in meal:
                    # Get accurate nutrition from Spoonacular
                    api_nutrition = self.meal_api.analyze_nutrition_spoonacular(
                        meal['ingredients_used']
                    )
                    
                    # Update nutrition values if API data is available
                    if api_nutrition:
                        meal['calories'] = api_nutrition.get('calories', meal['calories'])
                        meal['protein'] = api_nutrition.get('protein', meal['protein'])
                        meal['carbs'] = api_nutrition.get('carbohydrates', meal['carbs'])
                        meal['fat'] = api_nutrition.get('fat', meal['fat'])
                        if 'fiber' in api_nutrition:
                            meal['fiber'] = api_nutrition['fiber']
            
            # Recalculate totals
            meal_plan.total_calories = sum(meal.get('calories', 0) for meal in meal_plan.meals)
            meal_plan.total_protein = sum(meal.get('protein', 0) for meal in meal_plan.meals)
            meal_plan.total_carbs = sum(meal.get('carbs', 0) for meal in meal_plan.meals)
            meal_plan.total_fat = sum(meal.get('fat', 0) for meal in meal_plan.meals)
            
        except Exception as e:
            logger.error(f"Error enhancing with API nutrition: {e}")
        
        return meal_plan
    
    def _generate_fallback_meal_plan(self, goal: str, ingredients: List[str]) -> MealPlan:
        """Generate a basic meal plan as fallback"""
        try:
            prompt = f"""
Create a simple meal plan for goal: {goal} using ingredients: {', '.join(ingredients)}

Provide JSON with structure:
{{
  "goal": "{goal}",
  "ingredients": {json.dumps(ingredients)},
  "meals": [
    {{
      "name": "Meal name",
      "type": "breakfast|lunch|dinner",
      "calories": 400,
      "protein": 25,
      "carbs": 45,
      "fat": 15,
      "steps": ["Step 1", "Step 2"]
    }}
  ]
}}
            """
            
            response = self.model.generate_content(prompt)
            meal_data = json.loads(response.text.strip())
            
            total_calories = sum(meal.get('calories', 0) for meal in meal_data['meals'])
            total_protein = sum(meal.get('protein', 0) for meal in meal_data['meals'])
            total_carbs = sum(meal.get('carbs', 0) for meal in meal_data['meals'])
            total_fat = sum(meal.get('fat', 0) for meal in meal_data['meals'])
            
            return MealPlan(
                goal=meal_data['goal'],
                ingredients=meal_data['ingredients'],
                meals=meal_data['meals'],
                total_calories=total_calories,
                total_protein=total_protein,
                total_carbs=total_carbs,
                total_fat=total_fat,
                created_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error in fallback meal plan generation: {e}")
            # Return minimal plan
            return MealPlan(
                goal=goal,
                ingredients=ingredients,
                meals=[],
                total_calories=0,
                total_protein=0,
                total_carbs=0,
                total_fat=0,
                created_at=datetime.now().isoformat()
            )
    
    def get_recipe_suggestions(self, ingredients: List[str], meal_type: str = None) -> List[Recipe]:
        """Get recipe suggestions based on ingredients"""
        cache_key = f"recipe_suggestions_{hash(str(ingredients) + str(meal_type))}"
        
        cached_recipes = self.cache_manager.get(cache_key)
        if cached_recipes:
            return [Recipe(**recipe) for recipe in cached_recipes]
        
        recipes = self.meal_api.search_recipes_spoonacular(ingredients, max_results=10)
        
        # Filter by meal type if specified
        if meal_type and recipes:
            # Use AI to filter recipes by meal type
            filtered_recipes = self._filter_recipes_by_meal_type(recipes, meal_type)
            recipes = filtered_recipes
        
        # Cache results
        recipe_dicts = [recipe.__dict__ for recipe in recipes]
        self.cache_manager.set(cache_key, recipe_dicts, expire_hours=12)
        
        return recipes
    
    def _filter_recipes_by_meal_type(self, recipes: List[Recipe], meal_type: str) -> List[Recipe]:
        """Filter recipes by meal type using AI"""
        try:
            recipe_names = [recipe.name for recipe in recipes]
            
            prompt = f"""
Given these recipe names: {', '.join(recipe_names)}
Filter and return only the recipe names that are suitable for {meal_type}.
Return as a JSON array of recipe names: ["recipe1", "recipe2"]
            """
            
            response = self.model.generate_content(prompt)
            suitable_names = json.loads(response.text.strip())
            
            # Filter original recipes
            filtered_recipes = [
                recipe for recipe in recipes 
                if recipe.name in suitable_names
            ]
            
            return filtered_recipes
            
        except Exception as e:
            logger.error(f"Error filtering recipes by meal type: {e}")
            return recipes  # Return all if filtering fails

# Example usage and testing
if __name__ == "__main__":
    # Initialize the meal RAG agent
    meal_agent = MealRAGAgent()
    
    # Test meal plan generation
    test_goal = "build muscle"
    test_ingredients = ["chicken breast", "rice", "broccoli", "eggs", "oats"]
    test_restrictions = ["gluten-free"]
    
    print("Generating meal plan...")
    meal_plan = meal_agent.generate_meal_plan(
        goal=test_goal,
        ingredients=test_ingredients,
        dietary_restrictions=test_restrictions,
        target_calories=2500
    )
    
    print(f"Generated meal plan for: {meal_plan.goal}")
    print(f"Total calories: {meal_plan.total_calories}")
    print(f"Total protein: {meal_plan.total_protein}g")
    print(f"Number of meals: {len(meal_plan.meals)}")
    
    for i, meal in enumerate(meal_plan.meals, 1):
        print(f"\nMeal {i}: {meal['name']} ({meal['type']})")
        print(f"Calories: {meal['calories']}, Protein: {meal['protein']}g")