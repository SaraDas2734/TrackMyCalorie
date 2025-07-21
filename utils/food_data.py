COMMON_FOODS = {
    'roti': {
        'calories': 120,
        'protein': 3,
        'carbs': 24,
        'fats': 0.5,
        'serving_size': '1 piece'
    },
    'dal': {
        'calories': 150,
        'protein': 9,
        'carbs': 25,
        'fats': 2,
        'serving_size': '1 cup (240ml)'
    },
    'rice': {
        'calories': 130,
        'protein': 2.7,
        'carbs': 28,
        'fats': 0.3,
        'serving_size': '1 cup cooked'
    },
    'chicken breast': {
        'calories': 165,
        'protein': 31,
        'carbs': 0,
        'fats': 3.6,
        'serving_size': '100g'
    },
    'egg': {
        'calories': 70,
        'protein': 6,
        'carbs': 0,
        'fats': 5,
        'serving_size': '1 whole'
    },
    'paneer': {
        'calories': 265,
        'protein': 18,
        'carbs': 4,
        'fats': 21,
        'serving_size': '100g'
    }
}

SUPPLEMENTS = {
    'whey protein': {
        'calories': 120,
        'protein': 24,
        'carbs': 3,
        'fats': 2,
        'serving_size': '1 scoop (30g)'
    },
    'creatine': {
        'calories': 0,
        'protein': 0,
        'carbs': 0,
        'fats': 0,
        'serving_size': '5g'
    },
    'pea protein': {
        'calories': 100,
        'protein': 21,
        'carbs': 1,
        'fats': 1.5,
        'serving_size': '1 scoop (30g)'
    }
}

def get_food_info(food_name):
    """Get nutritional information for a food item"""
    return COMMON_FOODS.get(food_name.lower())

def get_supplement_info(supplement_name):
    """Get nutritional information for a supplement"""
    return SUPPLEMENTS.get(supplement_name.lower())

def calculate_portion_nutrients(food_info, portion_size):
    """Calculate nutrients based on portion size"""
    if not food_info:
        return None
    
    multiplier = portion_size
    return {
        'calories': round(food_info['calories'] * multiplier, 1),
        'protein': round(food_info['protein'] * multiplier, 1),
        'carbs': round(food_info['carbs'] * multiplier, 1),
        'fats': round(food_info['fats'] * multiplier, 1)
    }
