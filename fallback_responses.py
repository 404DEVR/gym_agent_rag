import re
from typing import Dict, List

class FallbackResponseSystem:
    def __init__(self):
        self.keyword_responses = {
            # Weight loss related
            'weight_loss': [
                """**Weight Loss Plan Basics:**

**Workout (3-4x/week):**
• 20-30 min cardio (walking, jogging, cycling)
• 2-3 strength training sessions
• Focus: compound movements (squats, push-ups, planks)

**Nutrition:**
• Create 300-500 calorie deficit
• Eat protein with every meal
• Fill half your plate with vegetables
• Stay hydrated (8-10 glasses water)

**Sample Day:**
• Breakfast: Oatmeal + berries + protein powder
• Lunch: Grilled chicken + quinoa + vegetables  
• Dinner: Fish + sweet potato + salad
• Snacks: Greek yogurt, nuts, fruits

*For a personalized plan, share your age, weight, height, and current activity level!*""",
                
                "Weight loss basics: eat in a caloric deficit, include protein in every meal, stay hydrated, and combine cardio with strength training.",
                "To lose weight effectively: track your calories, eat whole foods, exercise regularly, and be patient with the process."
            ],
            
            # Muscle building
            'muscle_building': [
                """**Muscle Building Plan Basics:**

**Workout (4-5x/week):**
• Day 1: Chest, Shoulders, Triceps
• Day 2: Back, Biceps
• Day 3: Legs, Glutes
• Day 4: Rest or light cardio
• Day 5: Full body or repeat

**Key Exercises:**
• Push-ups/Bench press
• Pull-ups/Rows
• Squats/Lunges
• Deadlifts/Hip hinges

**Nutrition:**
• Eat in slight calorie surplus (200-300 calories)
• 1g protein per lb bodyweight
• Complex carbs around workouts
• Healthy fats for hormone production

*Share your details for a personalized muscle-building plan!*""",
                
                "Building muscle requires: consistent strength training, proper nutrition with enough protein, adequate sleep, and patience.",
                "Muscle building tips: lift weights 3-4x per week, eat protein with every meal, get 7-9 hours of sleep, and stay consistent."
            ],
            
            # Nutrition
            'nutrition': [
                """**Daily Nutrition Template:**

**Breakfast:**
• Protein source (eggs, Greek yogurt, protein powder)
• Complex carbs (oats, whole grain toast)
• Healthy fats (nuts, avocado)

**Lunch:**
• Lean protein (chicken, fish, tofu)
• Vegetables (aim for variety and color)
• Complex carbs (quinoa, brown rice)

**Dinner:**
• Similar to lunch but lighter portions
• Focus on vegetables and protein

**Snacks:**
• Greek yogurt with berries
• Nuts and seeds
• Protein smoothies
• Fresh fruits

*Tell me your goals and I'll create a specific meal plan for you!*""",
                
                "Focus on whole foods: lean proteins, complex carbs, healthy fats, fruits, and vegetables. Limit processed foods.",
                "Nutrition basics: eat regular meals, include protein in each meal, choose complex carbs, and don't forget your vegetables."
            ],
            
            # Workout plans
            'workout': [
                """**Beginner Workout Plan (3x/week):**

**Day 1 - Full Body:**
• Squats: 3 sets x 10-12 reps
• Push-ups: 3 sets x 8-10 reps
• Plank: 3 sets x 30-60 seconds
• Walking: 20-30 minutes

**Day 2 - Rest or Light Activity**

**Day 3 - Full Body:**
• Lunges: 3 sets x 10 each leg
• Modified pull-ups or rows: 3 sets x 8-10
• Glute bridges: 3 sets x 12-15
• Stretching: 10-15 minutes

**Day 4 - Rest**

**Day 5 - Full Body:**
• Wall sits: 3 sets x 30-45 seconds
• Mountain climbers: 3 sets x 20
• Dead bugs: 3 sets x 10 each side
• Light cardio: 20-30 minutes

*Want a personalized plan? Share your fitness level and goals!*""",
                
                "For beginners: start with bodyweight exercises, gradually add weights, focus on form over intensity, and be consistent.",
                "Effective workouts include: compound movements, progressive overload, proper warm-up, and adequate rest between sessions."
            ],
            
            # General fitness
            'fitness': [
                "Fitness is a journey, not a destination. Focus on consistency, proper form, adequate nutrition, and listening to your body.",
                "Key fitness principles: progressive overload, consistency, proper nutrition, adequate rest, and patience with results.",
                "Remember: small consistent actions lead to big results. Focus on building sustainable habits."
            ]
        }
        
        self.question_patterns = {
            r'\b(lose|losing|weight loss|fat loss|shed|drop)\b': 'weight_loss',
            r'\b(muscle|build|gain|bulk|strength|mass|size)\b': 'muscle_building',
            r'\b(eat|food|nutrition|diet|meal|recipe|cook)\b': 'nutrition',
            r'\b(workout|exercise|training|gym|routine|plan|program)\b': 'workout',
            r'\b(fitness|health|fit|active|shape)\b': 'fitness'
        }
    
    def get_fallback_response(self, message: str) -> str:
        """Get an appropriate fallback response based on message content"""
        message_lower = message.lower()
        
        # Check for question patterns
        for pattern, category in self.question_patterns.items():
            if re.search(pattern, message_lower):
                responses = self.keyword_responses[category]
                # Simple hash-based selection for consistency
                response_index = hash(message) % len(responses)
                return responses[response_index]
        
        # Default response if no pattern matches
        return """
I'd love to help you with your fitness journey! I can assist with:

• **Weight Loss** - Creating sustainable caloric deficits
• **Muscle Building** - Strength training and nutrition
• **Workout Plans** - Customized exercise routines  
• **Nutrition Advice** - Meal planning and healthy eating
• **General Fitness** - Tips for staying active and healthy

What specific area would you like to focus on today?
        """.strip()
    
    def is_greeting(self, message: str) -> bool:
        """Check if message is a greeting"""
        message_lower = message.lower().strip()
        
        # Only consider it a greeting if it's a short message that starts with or is exactly a greeting
        greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
        
        # Check if message is exactly a greeting or starts with a greeting
        for greeting in greetings:
            if message_lower == greeting or message_lower.startswith(greeting + ' '):
                return True
        
        # Also check for very short messages that are clearly greetings
        if len(message.split()) <= 3:
            return any(greeting in message_lower for greeting in greetings)
        
        return False
    
    def get_greeting_response(self) -> str:
        """Get a friendly greeting response"""
        return """
Hello! 👋 I'm your AI Fitness Assistant, and I'm excited to help you on your fitness journey!

I can help you with:
• Creating personalized workout plans
• Nutrition and meal planning advice
• Weight loss strategies
• Muscle building tips
• General fitness guidance

What would you like to work on today?
        """.strip()