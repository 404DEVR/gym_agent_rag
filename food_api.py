import requests
import os

def get_food_suggestions(query, api_key=None):
    """
    Get real-time food suggestions using Spoonacular API
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

if __name__ == "__main__":
    print(get_food_suggestions("high protein vegetarian"))