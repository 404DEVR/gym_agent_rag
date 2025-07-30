import re
from typing import Dict, Optional, Tuple

class MacroCalculator:
    """Simple macro and calorie calculator to reduce API usage"""
    
    def __init__(self):
        # BMR calculation constants
        self.bmr_constants = {
            'male': {'base': 88.362, 'weight': 13.397, 'height': 4.799, 'age': 5.677},
            'female': {'base': 447.593, 'weight': 9.247, 'height': 3.098, 'age': 4.330}
        }
        
        # Activity multipliers
        self.activity_multipliers = {
            'sedentary': 1.2,
            'lightly_active': 1.375,
            'moderately_active': 1.55,
            'very_active': 1.725,
            'extremely_active': 1.9
        }
    
    def extract_user_data(self, message: str) -> Optional[Dict]:
        """Extract user data from message using regex"""
        data = {}
        
        # Extract age
        age_match = re.search(r'\b(\d{1,2})\s*(?:years?\s*old|yo|age)\b', message.lower())
        if age_match:
            data['age'] = int(age_match.group(1))
        
        # Extract weight (kg or lbs)
        weight_match = re.search(r'\b(\d{1,3}(?:\.\d)?)\s*(?:kg|kgs|pounds?|lbs?)\b', message.lower())
        if weight_match:
            weight = float(weight_match.group(1))
            # Convert lbs to kg if needed
            if 'lb' in message.lower() or 'pound' in message.lower():
                weight = weight * 0.453592
            data['weight'] = weight
        
        # Extract height (cm or feet/inches)
        height_cm_match = re.search(r'\b(\d{2,3})\s*cm\b', message.lower())
        height_ft_match = re.search(r'\b(\d)\s*(?:ft|feet|\')\s*(\d{1,2})\s*(?:in|inches?|")\b', message.lower())
        
        if height_cm_match:
            data['height'] = float(height_cm_match.group(1))
        elif height_ft_match:
            feet = int(height_ft_match.group(1))
            inches = int(height_ft_match.group(2))
            data['height'] = (feet * 12 + inches) * 2.54  # Convert to cm
        
        # Extract gender
        if re.search(r'\b(?:male|man|guy)\b', message.lower()) and not re.search(r'\bfemale\b', message.lower()):
            data['gender'] = 'male'
        elif re.search(r'\b(?:female|woman|girl)\b', message.lower()):
            data['gender'] = 'female'
        
        return data if len(data) >= 3 else None  # Need at least 3 pieces of info
    
    def calculate_bmr(self, weight: float, height: float, age: int, gender: str) -> float:
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor equation"""
        constants = self.bmr_constants.get(gender.lower(), self.bmr_constants['male'])
        
        bmr = (constants['base'] + 
               constants['weight'] * weight + 
               constants['height'] * height - 
               constants['age'] * age)
        
        return round(bmr)
    
    def calculate_tdee(self, bmr: float, activity_level: str = 'moderately_active') -> float:
        """Calculate Total Daily Energy Expenditure"""
        multiplier = self.activity_multipliers.get(activity_level, 1.55)
        return round(bmr * multiplier)
    
    def calculate_macros(self, calories: float, goal: str = 'maintain') -> Dict[str, int]:
        """Calculate macro distribution based on goal"""
        if 'lose' in goal.lower() or 'cut' in goal.lower():
            # Higher protein for weight loss
            protein_ratio, carb_ratio, fat_ratio = 0.35, 0.35, 0.30
        elif 'gain' in goal.lower() or 'bulk' in goal.lower():
            # Higher carbs for muscle gain
            protein_ratio, carb_ratio, fat_ratio = 0.25, 0.45, 0.30
        else:
            # Balanced for maintenance
            protein_ratio, carb_ratio, fat_ratio = 0.30, 0.40, 0.30
        
        return {
            'protein': round((calories * protein_ratio) / 4),  # 4 cal/g
            'carbs': round((calories * carb_ratio) / 4),       # 4 cal/g
            'fat': round((calories * fat_ratio) / 9)           # 9 cal/g
        }
    
    def can_handle_message(self, message: str) -> bool:
        """Check if this message can be handled by the calculator"""
        calc_keywords = [
            'calculate', 'calories', 'bmr', 'tdee', 'macros', 'protein',
            'how many calories', 'daily calories', 'calorie needs'
        ]
        return any(keyword in message.lower() for keyword in calc_keywords)
    
    def generate_response(self, message: str) -> Optional[str]:
        """Generate a response if the message can be handled"""
        if not self.can_handle_message(message):
            return None
        
        user_data = self.extract_user_data(message)
        
        if not user_data or len(user_data) < 3:
            return """
To calculate your daily calorie needs, I need some information:

• **Age** (e.g., "I'm 25 years old")
• **Weight** (e.g., "I weigh 70kg" or "150 lbs")  
• **Height** (e.g., "I'm 175cm" or "5'9\"")
• **Gender** (male/female)

Please provide these details and I'll calculate your calories and macros!
            """.strip()
        
        # Calculate BMR and TDEE
        bmr = self.calculate_bmr(
            user_data['weight'], 
            user_data['height'], 
            user_data['age'], 
            user_data.get('gender', 'male')
        )
        
        tdee = self.calculate_tdee(bmr)
        
        # Determine goal from message
        goal = 'maintain'
        if any(word in message.lower() for word in ['lose', 'cut', 'deficit']):
            goal = 'lose'
            target_calories = tdee - 500  # 500 cal deficit
        elif any(word in message.lower() for word in ['gain', 'bulk', 'surplus']):
            goal = 'gain'
            target_calories = tdee + 300  # 300 cal surplus
        else:
            target_calories = tdee
        
        macros = self.calculate_macros(target_calories, goal)
        
        # Generate response
        goal_text = {
            'lose': 'weight loss (500 cal deficit)',
            'gain': 'muscle gain (300 cal surplus)',
            'maintain': 'maintenance'
        }
        
        response = f"""
## 📊 Your Personalized Nutrition Plan

**Your Stats:**
• Age: {user_data['age']} years
• Weight: {user_data['weight']:.1f}kg
• Height: {user_data['height']:.0f}cm
• Gender: {user_data.get('gender', 'male').title()}

**Calorie Calculations:**
• **BMR** (Base Metabolic Rate): {bmr} calories
• **TDEE** (Total Daily Energy): {tdee} calories
• **Target Calories** for {goal_text[goal]}: **{target_calories:.0f} calories**

**Daily Macro Targets:**
• **Protein**: {macros['protein']}g ({macros['protein']*4} calories)
• **Carbs**: {macros['carbs']}g ({macros['carbs']*4} calories)  
• **Fat**: {macros['fat']}g ({macros['fat']*9} calories)

**Tips:**
• Eat protein with every meal
• Choose complex carbs over simple sugars
• Include healthy fats (nuts, olive oil, avocado)
• Stay hydrated (8-10 glasses of water daily)

*Note: These are estimates. Adjust based on your progress and how you feel!*
        """.strip()
        
        return response

# Legacy function for backward compatibility with agent.py
def calculate_macros(weight: float, height: float, age: int, gender: str, goal: str, activity: str) -> Dict[str, int]:
    """Legacy function to maintain compatibility with existing agent.py"""
    calculator = MacroCalculator()
    
    # Calculate BMR and TDEE
    bmr = calculator.calculate_bmr(weight, height, age, gender)
    
    # Map activity levels
    activity_mapping = {
        'sedentary': 'sedentary',
        'light': 'lightly_active', 
        'moderate': 'moderately_active',
        'active': 'very_active',
        'very_active': 'extremely_active'
    }
    
    activity_level = activity_mapping.get(activity.lower(), 'moderately_active')
    tdee = calculator.calculate_tdee(bmr, activity_level)
    
    # Adjust calories based on goal
    if 'lose' in goal.lower() or 'cut' in goal.lower():
        target_calories = tdee - 500
    elif 'gain' in goal.lower() or 'bulk' in goal.lower():
        target_calories = tdee + 300
    else:
        target_calories = tdee
    
    # Calculate macros
    macros = calculator.calculate_macros(target_calories, goal)
    
    # Return in the format expected by agent.py
    return {
        'calories': int(target_calories),
        'protein': macros['protein'],
        'carbs': macros['carbs'],
        'fats': macros['fat']  # Note: agent.py expects 'fats' not 'fat'
    }