"""
Advanced Nutrition Planning Module
Provides detailed meal plans based on user's cooking ability and lifestyle
"""

class NutritionPlanner:
    def __init__(self):
        self.no_cook_foods = {
            # Protein sources with calories per 100g
            "greek_yogurt": {"protein": 10, "carbs": 4, "fats": 0, "calories": 59},
            "cottage_cheese": {"protein": 11, "carbs": 3, "fats": 4, "calories": 98},
            "boiled_eggs": {"protein": 13, "carbs": 1, "fats": 11, "calories": 155},
            "milk": {"protein": 3.4, "carbs": 5, "fats": 3.3, "calories": 61},
            "almonds": {"protein": 21, "carbs": 22, "fats": 49, "calories": 579},
            "peanut_butter": {"protein": 25, "carbs": 20, "fats": 50, "calories": 588},
            "protein_powder": {"protein": 80, "carbs": 5, "fats": 2, "calories": 354},
            "canned_tuna": {"protein": 25, "carbs": 0, "fats": 1, "calories": 116},
            "chickpeas_canned": {"protein": 8, "carbs": 27, "fats": 3, "calories": 164},
        }
        
        self.simple_cook_recipes = {
            "overnight_oats": {
                "ingredients": [
                    {"item": "oats", "quantity": "80g", "calories": 304},
                    {"item": "milk", "quantity": "300ml", "calories": 183},
                    {"item": "banana", "quantity": "1 medium", "calories": 89},
                    {"item": "almonds", "quantity": "20g", "calories": 116}
                ],
                "instructions": [
                    "Mix oats with milk in a jar",
                    "Add sliced banana and almonds",
                    "Refrigerate overnight",
                    "Ready to eat in the morning"
                ],
                "prep_time": "5 minutes",
                "total_calories": 692,
                "macros": {"protein": 25, "carbs": 85, "fats": 20}
            },
            "scrambled_eggs_toast": {
                "ingredients": [
                    {"item": "eggs", "quantity": "3 large", "calories": 210},
                    {"item": "whole_grain_bread", "quantity": "2 slices", "calories": 160},
                    {"item": "butter", "quantity": "1 tsp", "calories": 34},
                    {"item": "tomato", "quantity": "1 medium", "calories": 22}
                ],
                "instructions": [
                    "Beat eggs in a bowl",
                    "Heat pan with butter",
                    "Scramble eggs on medium heat",
                    "Toast bread and serve with tomato"
                ],
                "prep_time": "10 minutes",
                "total_calories": 426,
                "macros": {"protein": 22, "carbs": 35, "fats": 18}
            }
        }
        
        self.full_cook_recipes = {
            "protein_pancakes": {
                "ingredients": [
                    {"item": "oats", "quantity": "60g", "calories": 228},
                    {"item": "eggs", "quantity": "2 large", "calories": 140},
                    {"item": "banana", "quantity": "1 medium", "calories": 89},
                    {"item": "protein_powder", "quantity": "1 scoop", "calories": 120},
                    {"item": "milk", "quantity": "100ml", "calories": 61}
                ],
                "instructions": [
                    "Blend all ingredients until smooth",
                    "Heat non-stick pan on medium heat",
                    "Pour batter to make 3-4 pancakes",
                    "Cook 2-3 minutes each side until golden",
                    "Serve with berries or honey"
                ],
                "prep_time": "15 minutes",
                "total_calories": 638,
                "macros": {"protein": 45, "carbs": 65, "fats": 12}
            },
            "chicken_rice_bowl": {
                "ingredients": [
                    {"item": "chicken_breast", "quantity": "150g", "calories": 248},
                    {"item": "brown_rice", "quantity": "80g_dry", "calories": 288},
                    {"item": "broccoli", "quantity": "150g", "calories": 51},
                    {"item": "olive_oil", "quantity": "1 tbsp", "calories": 119},
                    {"item": "bell_pepper", "quantity": "100g", "calories": 31}
                ],
                "instructions": [
                    "Cook rice according to package instructions",
                    "Season and grill chicken breast",
                    "Steam broccoli and bell peppers",
                    "Slice chicken and arrange over rice",
                    "Drizzle with olive oil and seasonings"
                ],
                "prep_time": "25 minutes",
                "total_calories": 737,
                "macros": {"protein": 45, "carbs": 65, "fats": 18}
            }
        }

    def generate_no_cook_meal_plan(self, target_calories, target_protein):
        """Generate a complete no-cook meal plan"""
        meals = {
            "breakfast": {
                "name": "Greek Yogurt Power Bowl",
                "foods": [
                    {"item": "Greek yogurt", "quantity": "200g", "calories": 118, "protein": 20},
                    {"item": "Banana", "quantity": "1 medium", "calories": 89, "protein": 1},
                    {"item": "Almonds", "quantity": "30g", "calories": 174, "protein": 6},
                    {"item": "Honey", "quantity": "1 tbsp", "calories": 64, "protein": 0}
                ],
                "total_calories": 445,
                "total_protein": 27,
                "prep_instructions": "Mix yogurt with sliced banana, top with almonds and drizzle honey"
            },
            "mid_morning": {
                "name": "Protein Snack",
                "foods": [
                    {"item": "Boiled eggs", "quantity": "2 large", "calories": 140, "protein": 12},
                    {"item": "Apple", "quantity": "1 medium", "calories": 95, "protein": 0}
                ],
                "total_calories": 235,
                "total_protein": 12,
                "prep_instructions": "Pre-boiled eggs with fresh apple slices"
            },
            "lunch": {
                "name": "Cottage Cheese Sandwich",
                "foods": [
                    {"item": "Cottage cheese", "quantity": "150g", "calories": 147, "protein": 17},
                    {"item": "Whole grain bread", "quantity": "2 slices", "calories": 160, "protein": 6},
                    {"item": "Peanut butter", "quantity": "2 tbsp", "calories": 188, "protein": 8},
                    {"item": "Cucumber", "quantity": "100g", "calories": 16, "protein": 1}
                ],
                "total_calories": 511,
                "total_protein": 32,
                "prep_instructions": "Spread peanut butter on bread, add cottage cheese and cucumber slices"
            },
            "pre_workout": {
                "name": "Energy Boost",
                "foods": [
                    {"item": "Banana", "quantity": "1 large", "calories": 121, "protein": 1},
                    {"item": "Dates", "quantity": "3 pieces", "calories": 60, "protein": 0}
                ],
                "total_calories": 181,
                "total_protein": 1,
                "prep_instructions": "Eat 30-45 minutes before workout"
            },
            "post_workout": {
                "name": "Recovery Shake",
                "foods": [
                    {"item": "Protein powder", "quantity": "1 scoop", "calories": 120, "protein": 25},
                    {"item": "Milk", "quantity": "300ml", "calories": 183, "protein": 10},
                    {"item": "Banana", "quantity": "1 medium", "calories": 89, "protein": 1}
                ],
                "total_calories": 392,
                "total_protein": 36,
                "prep_instructions": "Blend all ingredients, consume within 30 minutes post-workout"
            },
            "dinner": {
                "name": "High-Protein Evening Meal",
                "foods": [
                    {"item": "Curd/Yogurt", "quantity": "300g", "calories": 177, "protein": 15},
                    {"item": "Mixed nuts", "quantity": "30g", "calories": 180, "protein": 6},
                    {"item": "Whole grain bread", "quantity": "1 slice", "calories": 80, "protein": 3}
                ],
                "total_calories": 437,
                "total_protein": 24,
                "prep_instructions": "Serve curd with nuts and bread on the side"
            },
            "before_bed": {
                "name": "Casein-Rich Snack",
                "foods": [
                    {"item": "Cottage cheese", "quantity": "100g", "calories": 98, "protein": 11},
                    {"item": "Walnuts", "quantity": "15g", "calories": 98, "protein": 2}
                ],
                "total_calories": 196,
                "total_protein": 13,
                "prep_instructions": "Light snack 1 hour before bed for overnight muscle recovery"
            }
        }
        
        # Calculate totals
        total_daily_calories = sum(meal["total_calories"] for meal in meals.values())
        total_daily_protein = sum(meal["total_protein"] for meal in meals.values())
        
        return {
            "meals": meals,
            "daily_totals": {
                "calories": total_daily_calories,
                "protein": total_daily_protein
            },
            "hostel_tips": [
                "Store dairy products in mini-fridge",
                "Pre-boil 10 eggs every Sunday for the week",
                "Buy nuts in bulk to save money",
                "Keep protein powder in airtight container",
                "Prepare overnight oats in mason jars"
            ],
            "shopping_list": self._generate_shopping_list(meals)
        }

    def generate_limited_cooking_plan(self, target_calories, target_protein):
        """Generate meal plan for limited cooking ability (10-15 min meals)"""
        meals = {
            "breakfast": {
                "recipe": self.simple_cook_recipes["overnight_oats"],
                "note": "Prepare 3 jars on Sunday for Mon-Wed"
            },
            "lunch": {
                "recipe": self.simple_cook_recipes["scrambled_eggs_toast"],
                "note": "Quick 10-minute meal"
            },
            "dinner": {
                "name": "Instant Noodles + Protein",
                "ingredients": [
                    {"item": "Whole grain instant noodles", "quantity": "1 pack", "calories": 380},
                    {"item": "Boiled eggs", "quantity": "2", "calories": 140},
                    {"item": "Frozen vegetables", "quantity": "100g", "calories": 35}
                ],
                "instructions": [
                    "Cook noodles as per package instructions",
                    "Add frozen vegetables in last 2 minutes",
                    "Top with sliced boiled eggs",
                    "Season with herbs and spices"
                ],
                "total_calories": 555,
                "prep_time": "8 minutes"
            }
        }
        
        return {
            "meals": meals,
            "batch_cooking_tips": [
                "Boil 10 eggs every Sunday",
                "Prepare overnight oats for 3 days",
                "Pre-cut vegetables and store in fridge",
                "Cook rice in bulk and refrigerate"
            ]
        }

    def generate_full_cooking_plan(self, target_calories, target_protein):
        """Generate comprehensive meal plan with full recipes"""
        meals = {
            "breakfast": {
                "name": "Protein Pancakes",
                "ingredients": self.full_cook_recipes["protein_pancakes"]["ingredients"],
                "instructions": self.full_cook_recipes["protein_pancakes"]["instructions"],
                "prep_time": self.full_cook_recipes["protein_pancakes"]["prep_time"],
                "total_calories": self.full_cook_recipes["protein_pancakes"]["total_calories"],
                "total_protein": self.full_cook_recipes["protein_pancakes"]["macros"]["protein"]
            },
            "lunch": {
                "name": "Chicken Rice Bowl",
                "ingredients": self.full_cook_recipes["chicken_rice_bowl"]["ingredients"],
                "instructions": self.full_cook_recipes["chicken_rice_bowl"]["instructions"],
                "prep_time": self.full_cook_recipes["chicken_rice_bowl"]["prep_time"],
                "total_calories": self.full_cook_recipes["chicken_rice_bowl"]["total_calories"],
                "total_protein": self.full_cook_recipes["chicken_rice_bowl"]["macros"]["protein"]
            },
            "dinner": {
                "name": "Grilled Salmon with Quinoa",
                "ingredients": [
                    {"item": "salmon_fillet", "quantity": "150g", "calories": 280},
                    {"item": "quinoa", "quantity": "60g_dry", "calories": 220},
                    {"item": "asparagus", "quantity": "150g", "calories": 30},
                    {"item": "olive_oil", "quantity": "1 tbsp", "calories": 119}
                ],
                "instructions": [
                    "Cook quinoa according to package instructions",
                    "Season salmon with herbs and spices",
                    "Grill salmon for 4-5 minutes each side",
                    "Steam asparagus until tender",
                    "Serve salmon over quinoa with asparagus"
                ],
                "prep_time": "20 minutes",
                "total_calories": 649,
                "total_protein": 42
            }
        }
        
        # Calculate totals
        total_daily_calories = sum(meal["total_calories"] for meal in meals.values())
        total_daily_protein = sum(meal["total_protein"] for meal in meals.values())
        
        return {
            "meals": meals,
            "daily_totals": {
                "calories": total_daily_calories,
                "protein": total_daily_protein
            },
            "cooking_tips": [
                "Sunday: Prep proteins for the week",
                "Cook grains in bulk",
                "Wash and chop all vegetables",
                "Prepare 3-4 different sauces/seasonings",
                "Invest in good non-stick pans",
                "Use a food scale for accurate portions"
            ],
            "shopping_list": self._generate_shopping_list(meals)
        }

    def _generate_shopping_list(self, meals):
        """Generate organized shopping list from meal plan"""
        shopping_list = {
            "dairy": ["Greek yogurt (1kg)", "Cottage cheese (500g)", "Milk (2L)", "Curd (500g)"],
            "proteins": ["Eggs (30 pieces)", "Protein powder (1kg)", "Canned tuna (4 cans)"],
            "nuts_seeds": ["Almonds (500g)", "Mixed nuts (300g)", "Peanut butter (500g jar)"],
            "fruits": ["Bananas (2kg)", "Apples (1kg)", "Dates (250g)"],
            "grains": ["Whole grain bread (2 loaves)", "Oats (1kg)"],
            "vegetables": ["Cucumber (500g)", "Tomatoes (500g)"],
            "pantry": ["Honey (250g)", "Olive oil (500ml)"]
        }
        
        return shopping_list

    def calculate_meal_macros(self, meal_foods):
        """Calculate total macros for a meal"""
        total_calories = sum(food["calories"] for food in meal_foods)
        total_protein = sum(food.get("protein", 0) for food in meal_foods)
        
        return {
            "calories": total_calories,
            "protein": total_protein,
            "carbs": total_calories * 0.4 // 4,  # Rough estimate
            "fats": total_calories * 0.3 // 9    # Rough estimate
        }

if __name__ == "__main__":
    planner = NutritionPlanner()
    
    # Test no-cook meal plan
    no_cook_plan = planner.generate_no_cook_meal_plan(2400, 150)
    # Test no-cook meal plan
    no_cook_plan = planner.generate_no_cook_meal_plan(2400, 150)