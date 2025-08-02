"""
Meal API Endpoint for the RAG Agent
Provides REST API endpoints for meal planning functionality
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from typing import Dict, Any, List
import json

# Import the meal RAG agent
from meal_rag_agent import MealRAGAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
meal_app = Flask(__name__)
CORS(meal_app)

# Initialize the meal RAG agent
meal_agent = MealRAGAgent()

@meal_app.route('/meal-plan', methods=['POST'])
def generate_meal_plan():
    """
    Generate a comprehensive meal plan using RAG + APIs + AI
    
    Expected JSON payload:
    {
        "goal": "build muscle",
        "ingredients": ["chicken", "rice", "broccoli"],
        "dietary_restrictions": ["gluten-free"],
        "target_calories": 2500
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract parameters
        goal = data.get('goal', '')
        ingredients = data.get('ingredients', [])
        dietary_restrictions = data.get('dietary_restrictions', [])
        target_calories = data.get('target_calories')
        
        # Validate required parameters
        if not goal or not ingredients:
            return jsonify({"error": "Goal and ingredients are required"}), 400
        
        # Generate meal plan
        meal_plan = meal_agent.generate_meal_plan(
            goal=goal,
            ingredients=ingredients,
            dietary_restrictions=dietary_restrictions,
            target_calories=target_calories
        )
        
        # Convert to dictionary for JSON response
        response_data = {
            "goal": meal_plan.goal,
            "ingredients": meal_plan.ingredients,
            "meals": meal_plan.meals,
            "total_nutrition": {
                "calories": meal_plan.total_calories,
                "protein": meal_plan.total_protein,
                "carbs": meal_plan.total_carbs,
                "fat": meal_plan.total_fat
            },
            "created_at": meal_plan.created_at
        }
        
        return jsonify({"meal_plan": response_data}), 200
        
    except Exception as e:
        logger.error(f"Error generating meal plan: {e}")
        return jsonify({"error": "Failed to generate meal plan"}), 500

@meal_app.route('/recipe-suggestions', methods=['POST'])
def get_recipe_suggestions():
    """
    Get recipe suggestions based on ingredients
    
    Expected JSON payload:
    {
        "ingredients": ["chicken", "rice"],
        "meal_type": "dinner"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        ingredients = data.get('ingredients', [])
        meal_type = data.get('meal_type')
        
        if not ingredients:
            return jsonify({"error": "Ingredients are required"}), 400
        
        # Get recipe suggestions
        recipes = meal_agent.get_recipe_suggestions(ingredients, meal_type)
        
        # Convert recipes to dictionaries
        recipe_data = []
        for recipe in recipes:
            recipe_dict = {
                "id": recipe.id,
                "name": recipe.name,
                "ingredients": recipe.ingredients,
                "instructions": recipe.instructions,
                "nutrition": {
                    "calories": recipe.nutrition.calories,
                    "protein": recipe.nutrition.protein,
                    "carbs": recipe.nutrition.carbs,
                    "fat": recipe.nutrition.fat,
                    "fiber": recipe.nutrition.fiber
                },
                "prep_time": recipe.prep_time,
                "cook_time": recipe.cook_time,
                "servings": recipe.servings,
                "image_url": recipe.image_url,
                "meal_type": recipe.meal_type
            }
            recipe_data.append(recipe_dict)
        
        return jsonify({"recipes": recipe_data}), 200
        
    except Exception as e:
        logger.error(f"Error getting recipe suggestions: {e}")
        return jsonify({"error": "Failed to get recipe suggestions"}), 500

@meal_app.route('/nutrition-analysis', methods=['POST'])
def analyze_nutrition():
    """
    Analyze nutrition content of ingredients
    
    Expected JSON payload:
    {
        "ingredients": ["chicken breast", "brown rice"],
        "quantities": ["150g", "1 cup cooked"]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        ingredients = data.get('ingredients', [])
        quantities = data.get('quantities', [])
        
        if not ingredients:
            return jsonify({"error": "Ingredients are required"}), 400
        
        # Analyze nutrition using the meal API client
        nutrition = meal_agent.meal_api.analyze_nutrition_spoonacular(ingredients)
        
        return jsonify({"nutrition": nutrition}), 200
        
    except Exception as e:
        logger.error(f"Error analyzing nutrition: {e}")
        return jsonify({"error": "Failed to analyze nutrition"}), 500

@meal_app.route('/ingredient-substitutes', methods=['POST'])
def get_ingredient_substitutes():
    """
    Get ingredient substitutes
    
    Expected JSON payload:
    {
        "ingredient": "chicken breast"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        ingredient = data.get('ingredient', '')
        
        if not ingredient:
            return jsonify({"error": "Ingredient is required"}), 400
        
        # Get substitutes
        substitutes = meal_agent.meal_api.get_ingredient_substitutes(ingredient)
        
        return jsonify({"substitutes": substitutes}), 200
        
    except Exception as e:
        logger.error(f"Error getting ingredient substitutes: {e}")
        return jsonify({"error": "Failed to get ingredient substitutes"}), 500

@meal_app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "meal-rag-agent"}), 200

@meal_app.route('/meal-plan/simple', methods=['POST'])
def generate_simple_meal_plan():
    """
    Generate a simple meal plan (fallback for when APIs are not available)
    
    Expected JSON payload:
    {
        "goal": "build muscle",
        "ingredients": ["chicken", "rice", "broccoli"]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        goal = data.get('goal', '')
        ingredients = data.get('ingredients', [])
        
        if not goal or not ingredients:
            return jsonify({"error": "Goal and ingredients are required"}), 400
        
        # Generate fallback meal plan
        meal_plan = meal_agent._generate_fallback_meal_plan(goal, ingredients)
        
        # Convert to dictionary for JSON response
        response_data = {
            "goal": meal_plan.goal,
            "ingredients": meal_plan.ingredients,
            "meals": meal_plan.meals,
            "total_nutrition": {
                "calories": meal_plan.total_calories,
                "protein": meal_plan.total_protein,
                "carbs": meal_plan.total_carbs,
                "fat": meal_plan.total_fat
            },
            "created_at": meal_plan.created_at
        }
        
        return jsonify({"meal_plan": response_data}), 200
        
    except Exception as e:
        logger.error(f"Error generating simple meal plan: {e}")
        return jsonify({"error": "Failed to generate simple meal plan"}), 500

if __name__ == '__main__':
    # Run the meal API server
    meal_app.run(host='0.0.0.0', port=8001, debug=True)