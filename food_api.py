"""
Enhanced Food API Integration Module
Handles interactions with various food and nutrition APIs for the RAG system
"""

import requests
import json
import os
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NutritionInfo:
    """Data class for nutrition information"""
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: float = 0
    sugar: float = 0
    sodium: float = 0

@dataclass
class RecipeInfo:
    """Data class for recipe information"""
    id: str
    name: str
    ingredients: List[str]
    instructions: List[str]
    nutrition: NutritionInfo
    prep_time: int
    cook_time: int
    servings: int
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    cuisine: Optional[str] = None
    meal_type: Optional[str] = None

class EnhancedFoodAPIClient:
    """Enhanced client for interacting with food and nutrition APIs"""
    
    def __init__(self):
        # API Keys from environment variables
        self.spoonacular_key = os.getenv('SPOONACULAR_API_KEY')
        
        # Base URLs
        self.spoonacular_base = "https://api.spoonacular.com"
        
        # Rate limiting
        self.last_request_time = {}
        self.min_request_interval = 1.0  # seconds between requests
    
    def _rate_limit(self, api_name: str):
        """Implement rate limiting for API calls"""
        current_time = datetime.now()
        if api_name in self.last_request_time:
            time_diff = (current_time - self.last_request_time[api_name]).total_seconds()
            if time_diff < self.min_request_interval:
                import time
                time.sleep(self.min_request_interval - time_diff)
        
        self.last_request_time[api_name] = current_time
    
    def search_recipes_by_ingredients(self, ingredients: List[str], 
                                    dietary_restrictions: List[str] = None,
                                    cuisine: str = None,
                                    meal_type: str = None,
                                    max_results: int = 10) -> List[RecipeInfo]:
        """
        Enhanced recipe search with multiple filters
        
        Args:
            ingredients: List of ingredients to search with
            dietary_restrictions: List of dietary restrictions
            cuisine: Cuisine type (italian, mexican, etc.)
            meal_type: Type of meal (breakfast, lunch, dinner)
            max_results: Maximum number of results to return
            
        Returns:
            List of RecipeInfo objects
        """
        if not self.spoonacular_key:
            logger.warning("Spoonacular API key not found")
            return []
        
        self._rate_limit('spoonacular')
        
        url = f"{self.spoonacular_base}/recipes/complexSearch"
        params = {
            'apiKey': self.spoonacular_key,
            'includeIngredients': ','.join(ingredients),
            'number': max_results,
            'addRecipeInformation': True,
            'addRecipeNutrition': True,
            'fillIngredients': True,
            'sort': 'max-used-ingredients'
        }
        
        # Add dietary restrictions
        if dietary_restrictions:
            diet_mapping = {
                'vegetarian': 'vegetarian',
                'vegan': 'vegan',
                'gluten-free': 'gluten free',
                'dairy-free': 'dairy free',
                'keto': 'ketogenic',
                'paleo': 'paleo',
                'low-carb': 'ketogenic'
            }
            
            for restriction in dietary_restrictions:
                if restriction.lower() in diet_mapping:
                    params['diet'] = diet_mapping[restriction.lower()]
                    break
        
        if cuisine:
            params['cuisine'] = cuisine
        
        if meal_type:
            params['type'] = meal_type
        
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            recipes = []
            for recipe_data in data.get('results', []):
                recipe_info = self._parse_spoonacular_recipe(recipe_data)
                if recipe_info:
                    recipes.append(recipe_info)
            
            return recipes
            
        except requests.RequestException as e:
            logger.error(f"Error searching recipes: {e}")
            return []
    
    def _parse_spoonacular_recipe(self, recipe_data: Dict[str, Any]) -> Optional[RecipeInfo]:
        """Parse Spoonacular recipe data into RecipeInfo object"""
        try:
            # Extract nutrition information
            nutrition = NutritionInfo(
                calories=0, protein=0, carbs=0, fat=0, fiber=0, sugar=0, sodium=0
            )
            
            if 'nutrition' in recipe_data and 'nutrients' in recipe_data['nutrition']:
                for nutrient in recipe_data['nutrition']['nutrients']:
                    name = nutrient['name'].lower()
                    amount = nutrient.get('amount', 0)
                    
                    if 'calorie' in name:
                        nutrition.calories = amount
                    elif 'protein' in name:
                        nutrition.protein = amount
                    elif 'carbohydrate' in name:
                        nutrition.carbs = amount
                    elif name == 'fat':
                        nutrition.fat = amount
                    elif 'fiber' in name:
                        nutrition.fiber = amount
                    elif 'sugar' in name:
                        nutrition.sugar = amount
                    elif 'sodium' in name:
                        nutrition.sodium = amount
            
            # Extract ingredients
            ingredients = []
            if 'extendedIngredients' in recipe_data:
                ingredients = [ing.get('original', '') for ing in recipe_data['extendedIngredients']]
            
            # Extract instructions
            instructions = []
            if 'analyzedInstructions' in recipe_data and recipe_data['analyzedInstructions']:
                for instruction_group in recipe_data['analyzedInstructions']:
                    if 'steps' in instruction_group:
                        for step in instruction_group['steps']:
                            instructions.append(step.get('step', ''))
            
            # Determine meal type from dish types
            meal_type = None
            if 'dishTypes' in recipe_data and recipe_data['dishTypes']:
                dish_types = recipe_data['dishTypes']
                if any(t in ['breakfast', 'brunch'] for t in dish_types):
                    meal_type = 'breakfast'
                elif any(t in ['lunch', 'main course', 'main dish'] for t in dish_types):
                    meal_type = 'lunch'
                elif any(t in ['dinner'] for t in dish_types):
                    meal_type = 'dinner'
                elif any(t in ['snack', 'appetizer'] for t in dish_types):
                    meal_type = 'snack'
            
            return RecipeInfo(
                id=str(recipe_data.get('id', '')),
                name=recipe_data.get('title', ''),
                ingredients=ingredients,
                instructions=instructions,
                nutrition=nutrition,
                prep_time=recipe_data.get('preparationMinutes', 0),
                cook_time=recipe_data.get('cookingMinutes', 0),
                servings=recipe_data.get('servings', 1),
                image_url=recipe_data.get('image'),
                source_url=recipe_data.get('sourceUrl'),
                cuisine=recipe_data.get('cuisines', [None])[0] if recipe_data.get('cuisines') else None,
                meal_type=meal_type
            )
            
        except Exception as e:
            logger.error(f"Error parsing recipe data: {e}")
            return None
    
    def analyze_nutrition_detailed(self, ingredients: List[str], 
                                 quantities: List[str] = None) -> NutritionInfo:
        """
        Detailed nutrition analysis using Spoonacular API
        
        Args:
            ingredients: List of ingredients
            quantities: List of quantities (optional)
            
        Returns:
            NutritionInfo object
        """
        if not self.spoonacular_key:
            logger.warning("Spoonacular API key not found")
            return NutritionInfo(calories=0, protein=0, carbs=0, fat=0)
        
        self._rate_limit('spoonacular')
        
        # Initialize nutrition totals
        nutrition = NutritionInfo(calories=0, protein=0, carbs=0, fat=0, fiber=0, sugar=0, sodium=0)
        
        try:
            for i, ingredient in enumerate(ingredients):
                # Use quantity if provided, otherwise default to 1 serving
                quantity = quantities[i] if quantities and i < len(quantities) else "1 serving"
                
                # Search for ingredient to get nutrition info
                search_url = f"{self.spoonacular_base}/food/ingredients/search"
                search_params = {
                    'apiKey': self.spoonacular_key,
                    'query': ingredient,
                    'number': 1,
                    'metaInformation': True
                }
                
                search_response = requests.get(search_url, params=search_params, timeout=10)
                search_response.raise_for_status()
                search_data = search_response.json()
                
                if search_data.get('results'):
                    ingredient_id = search_data['results'][0]['id']
                    
                    # Parse quantity and unit
                    amount = 1
                    unit = 'serving'
                    if quantity and quantity != "1 serving":
                        # Simple parsing - extract number and unit
                        import re
                        match = re.match(r'(\d+(?:\.\d+)?)\s*(\w+)', quantity)
                        if match:
                            amount = float(match.group(1))
                            unit = match.group(2)
                    
                    # Get detailed nutrition information
                    nutrition_url = f"{self.spoonacular_base}/food/ingredients/{ingredient_id}/information"
                    nutrition_params = {
                        'apiKey': self.spoonacular_key,
                        'amount': amount,
                        'unit': unit
                    }
                    
                    nutrition_response = requests.get(nutrition_url, params=nutrition_params, timeout=10)
                    nutrition_response.raise_for_status()
                    nutrition_data = nutrition_response.json()
                    
                    # Extract nutrition values
                    if 'nutrition' in nutrition_data and 'nutrients' in nutrition_data['nutrition']:
                        for nutrient in nutrition_data['nutrition']['nutrients']:
                            name = nutrient['name'].lower()
                            amount_val = nutrient.get('amount', 0)
                            
                            if 'calorie' in name or name == 'energy':
                                nutrition.calories += amount_val
                            elif 'protein' in name:
                                nutrition.protein += amount_val
                            elif 'carbohydrate' in name or 'carbs' in name:
                                nutrition.carbs += amount_val
                            elif name == 'fat' or 'total fat' in name:
                                nutrition.fat += amount_val
                            elif 'fiber' in name:
                                nutrition.fiber += amount_val
                            elif 'sugar' in name:
                                nutrition.sugar += amount_val
                            elif 'sodium' in name:
                                nutrition.sodium += amount_val
            
            return nutrition
            
        except requests.RequestException as e:
            logger.error(f"Error analyzing nutrition with Spoonacular: {e}")
            return NutritionInfo(calories=0, protein=0, carbs=0, fat=0)
    
    def get_ingredient_substitutes(self, ingredient: str) -> List[str]:
        """
        Get ingredient substitutes using Spoonacular
        
        Args:
            ingredient: Ingredient to find substitutes for
            
        Returns:
            List of substitute ingredients
        """
        if not self.spoonacular_key:
            return []
        
        self._rate_limit('spoonacular')
        
        url = f"{self.spoonacular_base}/food/ingredients/substitutes"
        params = {
            'apiKey': self.spoonacular_key,
            'ingredientName': ingredient
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            substitutes = []
            if 'substitutes' in data:
                substitutes = data['substitutes']
            
            return substitutes
            
        except requests.RequestException as e:
            logger.error(f"Error getting ingredient substitutes: {e}")
            return []

# Legacy function for backward compatibility
def get_food_suggestions(query, api_key=None):
    """
    Get real-time food suggestions using Spoonacular API
    (Legacy function for backward compatibility)
    """
    if not api_key:
        api_key = os.getenv("SPOONACULAR_API_KEY")
    
    if not api_key:
        # Return fallback suggestions if no API key
        return [
            "Greek yogurt with berries",
            "Grilled chicken breast",
            "Quinoa salad",
            "Almonds and walnuts",
            "Salmon with vegetables"
        ]
    
    try:
        url = "https://api.spoonacular.com/food/ingredients/search"
        params = {
            "query": query,
            "number": 5,
            "apiKey": api_key
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return [item["name"] for item in data.get("results", [])]
        else:
            # Return fallback if API fails
            return [
                "Greek yogurt with berries",
                "Grilled chicken breast", 
                "Quinoa salad",
                "Almonds and walnuts",
                "Salmon with vegetables"
            ]
    except Exception as e:
        # Return fallback if any error occurs
        return [
            "Greek yogurt with berries",
            "Grilled chicken breast",
            "Quinoa salad", 
            "Almonds and walnuts",
            "Salmon with vegetables"
        ]

# Example usage and testing
if __name__ == "__main__":
    client = EnhancedFoodAPIClient()
    
    # Test enhanced recipe search
    print("Testing enhanced recipe search...")
    recipes = client.search_recipes_by_ingredients(
        ingredients=['chicken', 'rice', 'broccoli'],
        dietary_restrictions=['gluten-free'],
        meal_type='dinner',
        max_results=3
    )
    
    print(f"Found {len(recipes)} recipes")
    for recipe in recipes:
        print(f"- {recipe.name}: {recipe.nutrition.calories} cal, {recipe.nutrition.protein}g protein")
    
    # Test detailed nutrition analysis
    print("\nTesting nutrition analysis...")
    nutrition = client.analyze_nutrition_detailed(
        ingredients=['chicken breast', 'brown rice', 'broccoli'],
        quantities=['150g', '1 cup cooked', '1 cup']
    )
    print(f"Nutrition: {nutrition.calories} cal, {nutrition.protein}g protein, {nutrition.carbs}g carbs")
    
    # Test legacy function
    print("\nTesting legacy function...")
    suggestions = get_food_suggestions("high protein vegetarian")
    print(f"Food suggestions: {suggestions}")