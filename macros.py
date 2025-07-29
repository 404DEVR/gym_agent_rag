def calculate_macros(weight, height, age, gender, goal, activity):
    bmr = 10*weight + 6.25*height - 5*age + (5 if gender=="male" else -161)
    activity_multiplier = {"sedentary":1.2, "light":1.375, "moderate":1.55, "active":1.725}
    tdee = bmr * activity_multiplier[activity]
    
    if goal=="fat_loss": tdee -= 500
    if goal=="muscle_gain": tdee += 300

    protein = weight * 1.8
    fat = (0.25 * tdee) / 9
    carbs = (tdee - (protein*4 + fat*9)) / 4

    return {
        "calories": round(tdee),
        "protein": round(protein),
        "fats": round(fat),
        "carbs": round(carbs)
    } 