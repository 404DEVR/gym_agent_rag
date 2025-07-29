from agent import generate_plan

# Test Scenario 1: Hostel student with no gym access
hostel_student = {
    "age": 20,
    "weight": 65,
    "height": 170,
    "gender": "male",
    "goal": "muscle_gain",
    "activity": "moderate",
    "diet": "vegetarian",
    "days": 4,
    "living_situation": "hostel",
    "cooking_ability": "no_cooking",
    "gym_access": "no_gym",
    "equipment_available": [],
    "dietary_restrictions": ["vegetarian"],
    "budget_level": "low"
}

# Test Scenario 2: Home gym enthusiast
home_gym_user = {
    "age": 28,
    "weight": 75,
    "height": 175,
    "gender": "male",
    "goal": "muscle_gain",
    "activity": "active",
    "diet": "omnivore",
    "days": 5,
    "living_situation": "home",
    "cooking_ability": "can_cook",
    "gym_access": "home_gym",
    "equipment_available": ["dumbbells", "resistance_bands", "pull_up_bar"],
    "dietary_restrictions": [],
    "budget_level": "moderate"
}

# Test Scenario 3: Working professional with limited time
busy_professional = {
    "age": 30,
    "weight": 80,
    "height": 180,
    "gender": "female",
    "goal": "fat_loss",
    "activity": "light",
    "diet": "omnivore",
    "days": 3,
    "living_situation": "apartment",
    "cooking_ability": "limited_cooking",
    "gym_access": "full_gym",
    "equipment_available": [],
    "dietary_restrictions": [],
    "budget_level": "high"
}

if __name__ == "__main__":
    print("=" * 80)
    print("SCENARIO 1: HOSTEL STUDENT - NO GYM, NO COOKING")
    print("=" * 80)
    try:
        plan1 = generate_plan(hostel_student)
        print(plan1)
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 80)
    print("SCENARIO 2: HOME GYM USER - LIMITED EQUIPMENT")
    print("=" * 80)
    try:
        plan2 = generate_plan(home_gym_user)
        print(plan2)
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 80)
    print("SCENARIO 3: BUSY PROFESSIONAL - FULL GYM ACCESS")
    print("=" * 80)
    try:
        plan3 = generate_plan(busy_professional)
        print(plan3)
    except Exception as e:
        print(f"Error: {e}")