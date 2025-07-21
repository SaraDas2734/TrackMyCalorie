def calculate_bmr(weight, height, age, gender):
    """Calculate Basal Metabolic Rate using the Mifflin-St Jeor Equation"""
    if gender.lower() == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    return round(bmr)

def calculate_tdee(bmr, activity_level):
    """Calculate Total Daily Energy Expenditure"""
    activity_multipliers = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'very_active': 1.725,
        'extra_active': 1.9
    }
    return round(bmr * activity_multipliers.get(activity_level, 1.2))

def calculate_macros(tdee, goal, weight):
    """Calculate macronutrient targets based on goal"""
    if goal == 'bulk':
        calories = tdee + 500
        protein = round(2 * weight)  # 2g per kg of body weight
    elif goal == 'lean_bulk':
        calories = tdee + 200  # smaller surplus for lean bulk
        protein = round(2.2 * weight)  # slightly higher protein
    elif goal == 'cut':
        calories = tdee - 500
        protein = round(2.2 * weight)  # 2.2g per kg to preserve muscle
    else:  # maintain
        calories = tdee
        protein = round(1.8 * weight)  # 1.8g per kg for maintenance
    
    # Calculate remaining macros
    protein_cals = protein * 4
    fats = round((calories * 0.25) / 9)  # 25% of calories from fat
    fat_cals = fats * 9
    carbs = round((calories - protein_cals - fat_cals) / 4)
    
    return {
        'calories': calories,
        'protein': protein,
        'carbs': carbs,
        'fats': fats
    }
