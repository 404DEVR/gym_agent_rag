import re
from typing import Dict, List

class FallbackResponseSystem:
    def __init__(self):
        self.keyword_responses = {
            # Weight loss related
            'weight_loss': [
                "For weight loss, focus on creating a caloric deficit through a combination of diet and exercise. Aim for 1-2 pounds per week for sustainable results.",
                "Weight loss basics: eat in a caloric deficit, include protein in every meal, stay hydrated, and combine cardio with strength training.",
                "To lose weight effectively: track your calories, eat whole foods, exercise regularly, and be patient with the process."
            ],
            
            # Muscle building
            'muscle_building': [
                "For muscle building, focus on progressive overload, eat adequate protein (0.8-1g per lb bodyweight), and get enough rest for recovery.",
                "Building muscle requires: consistent strength training, proper nutrition with enough protein, adequate sleep, and patience.",
                "Muscle building tips: lift weights 3-4x per week, eat protein with every meal, get 7-9 hours of sleep, and stay consistent."
            ],
            
            # Nutrition
            'nutrition': [
                "Good nutrition includes: balanced macronutrients, plenty of vegetables, adequate protein, healthy fats, and staying hydrated.",
                "Focus on whole foods: lean proteins, complex carbs, healthy fats, fruits, and vegetables. Limit processed foods.",
                "Nutrition basics: eat regular meals, include protein in each meal, choose complex carbs, and don't forget your vegetables."
            ],
            
            # Workout plans
            'workout': [
                "A good workout plan includes: strength training 3-4x per week, cardio 2-3x per week, and rest days for recovery.",
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
            r'\b(lose|losing|weight loss|fat loss)\b': 'weight_loss',
            r'\b(muscle|build|gain|bulk|strength)\b': 'muscle_building',
            r'\b(eat|food|nutrition|diet|meal)\b': 'nutrition',
            r'\b(workout|exercise|training|gym)\b': 'workout',
            r'\b(fitness|health|fit)\b': 'fitness'
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
        greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
        return any(greeting in message.lower() for greeting in greetings)
    
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