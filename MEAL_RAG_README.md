# Meal RAG Agent

A comprehensive RAG (Retrieval-Augmented Generation) agent for intelligent meal planning that combines meal APIs, nutrition databases, and AI to provide personalized meal plans and recipes.

## 🚀 Features

### Core Functionality
- **RAG-Enhanced Meal Planning**: Combines nutrition knowledge base with real-time API data
- **Multi-API Integration**: Spoonacular (recipes + nutrition) and USDA FoodData Central APIs
- **AI-Powered Generation**: Uses Google Gemini for intelligent meal plan creation
- **Nutrition Analysis**: Accurate macro and micronutrient calculations
- **Recipe Search**: Find recipes based on available ingredients
- **Dietary Restrictions**: Support for various dietary needs and restrictions

### Advanced Features
- **Intelligent Caching**: Reduces API calls and improves response times
- **Fallback Systems**: Graceful degradation when APIs are unavailable
- **Rate Limiting**: Prevents API quota exhaustion
- **Batch Processing**: Efficient handling of multiple requests
- **Context-Aware Planning**: Considers user's cooking ability, time, and budget

## 🏗️ Architecture

```
Meal RAG Agent
├── meal_rag_agent.py          # Main RAG agent class
├── food_api.py                # Enhanced API client for food services
├── meal_api_endpoint.py       # REST API endpoints
├── retriever.py               # RAG retrieval system (shared)
├── cache_manager.py           # Caching system (shared)
└── .env                       # Configuration
```

## 🔧 Setup & Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. API Keys Configuration
Create a `.env` file with the following keys:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Recommended for enhanced functionality
SPOONACULAR_API_KEY=your_spoonacular_api_key_here

# Optional for additional food data
USDA_API_KEY=your_usda_api_key_here
```

### 3. API Key Sources

#### Gemini API (Required)
- Get from: [Google AI Studio](https://makersuite.google.com/app/apikey)
- Free tier: 60 requests per minute
- Used for: AI meal plan generation

#### Spoonacular API (Recommended)
- Get from: [Spoonacular API](https://spoonacular.com/food-api)
- Free tier: 150 requests per day
- Used for: Recipe search, meal planning, nutrition analysis, ingredient substitutes

#### USDA FoodData Central (Optional)
- Get from: [USDA FDC](https://fdc.nal.usda.gov/api-guide.html)
- Free tier: 1,000 requests per hour
- Used for: Additional comprehensive food database

## 🚀 Usage

### 1. As a Standalone Service
```bash
# Run the meal API server
python meal_api_endpoint.py
```

### 2. Integrated with Main App
The meal RAG agent is automatically integrated with the main FastAPI app and accessible through the Next.js frontend.

### 3. Direct Python Usage
```python
from meal_rag_agent import MealRAGAgent

# Initialize the agent
meal_agent = MealRAGAgent()

# Generate a meal plan
meal_plan = meal_agent.generate_meal_plan(
    goal="build muscle",
    ingredients=["chicken", "rice", "broccoli", "eggs"],
    dietary_restrictions=["gluten-free"],
    target_calories=2500
)

print(f"Generated {len(meal_plan.meals)} meals")
print(f"Total calories: {meal_plan.total_calories}")
```

## 📡 API Endpoints

### POST `/meal-plan`
Generate a comprehensive meal plan using RAG + APIs + AI

**Request Body:**
```json
{
    "goal": "build muscle",
    "ingredients": ["chicken", "rice", "broccoli"],
    "dietary_restrictions": ["gluten-free"],
    "target_calories": 2500
}
```

**Response:**
```json
{
    "meal_plan": {
        "goal": "build muscle",
        "ingredients": ["chicken", "rice", "broccoli"],
        "meals": [
            {
                "name": "Protein-Packed Breakfast Bowl",
                "type": "breakfast",
                "calories": 450,
                "protein": 35,
                "carbs": 40,
                "fat": 15,
                "fiber": 8,
                "ingredients_used": ["eggs", "rice"],
                "steps": ["Step 1", "Step 2", "Step 3"],
                "prep_time": 10,
                "cook_time": 15,
                "tips": "Add vegetables for extra nutrients"
            }
        ],
        "total_nutrition": {
            "calories": 2480,
            "protein": 185,
            "carbs": 280,
            "fat": 65
        },
        "created_at": "2024-01-15T10:30:00"
    }
}
```

### POST `/recipe-suggestions`
Get recipe suggestions based on ingredients

**Request Body:**
```json
{
    "ingredients": ["chicken", "rice"],
    "meal_type": "dinner"
}
```

### POST `/nutrition-analysis`
Analyze nutrition content of ingredients

**Request Body:**
```json
{
    "ingredients": ["chicken breast", "brown rice"],
    "quantities": ["150g", "1 cup cooked"]
}
```

### POST `/ingredient-substitutes`
Get ingredient substitutes

**Request Body:**
```json
{
    "ingredient": "chicken breast"
}
```

## 🧠 How It Works

### 1. RAG Retrieval
- Searches nutrition knowledge base for relevant information
- Combines with user's specific requirements
- Provides context for AI generation

### 2. API Integration
- **Spoonacular**: Recipe search, meal planning, and nutrition analysis
- **USDA**: Comprehensive food database (optional)

### 3. AI Generation
- Uses Gemini AI with enhanced prompts
- Incorporates RAG context and API data
- Generates personalized meal plans

### 4. Enhancement Pipeline
```
User Input → RAG Retrieval → API Search → AI Generation → Nutrition Enhancement → Response
```

## 🎯 Key Features

### Intelligent Meal Planning
- **Context-Aware**: Considers cooking ability, time, budget
- **Goal-Oriented**: Aligns with fitness objectives
- **Restriction-Friendly**: Handles dietary limitations
- **Calorie-Targeted**: Meets specific caloric needs

### Recipe Intelligence
- **Ingredient-Based Search**: Find recipes with available ingredients
- **Nutrition-Optimized**: Prioritize recipes meeting macro goals
- **Difficulty-Filtered**: Match user's cooking skill level
- **Time-Conscious**: Consider prep and cook times

### Nutrition Accuracy
- **API-Enhanced**: Real nutrition data from databases
- **Macro-Balanced**: Proper protein/carb/fat ratios
- **Micronutrient-Aware**: Consider vitamins and minerals
- **Portion-Controlled**: Accurate serving sizes

## 🔄 Integration with Next.js Frontend

The meal RAG agent integrates seamlessly with the Next.js frontend:

1. **Chef Page**: Uses `/api/generate-meal-plan` endpoint
2. **Automatic Fallback**: Falls back to Gemini-only if RAG agent unavailable
3. **Enhanced Features**: Dietary restrictions, calorie targeting
4. **Profile Integration**: Save generated meal plans

## 🚀 Deployment

### Local Development
```bash
# Start the meal RAG service
python meal_api_endpoint.py

# Start the main FastAPI app
python app.py
```

### Production Deployment
The meal RAG agent is integrated into the main FastAPI application and deploys automatically with the fitness RAG agent.

## 🔧 Configuration

### Environment Variables
- `GEMINI_API_KEY`: Required for AI generation
- `SPOONACULAR_API_KEY`: Enhanced recipe search and nutrition analysis
- `USDA_API_KEY`: Additional food database access (optional)
- `CACHE_ENABLED`: Enable/disable caching (default: true)
- `LOG_LEVEL`: Logging level (default: INFO)

### Rate Limiting
- Automatic rate limiting prevents API quota exhaustion
- Configurable request intervals
- Graceful fallback when limits reached

## 🧪 Testing

### Test the Meal RAG Agent
```python
# Run the example in meal_rag_agent.py
python meal_rag_agent.py
```

### Test API Endpoints
```bash
# Test meal plan generation
curl -X POST http://localhost:8001/meal-plan \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "build muscle",
    "ingredients": ["chicken", "rice", "broccoli"],
    "dietary_restrictions": ["gluten-free"],
    "target_calories": 2500
  }'
```

## 🔮 Future Enhancements

- **Image Recognition**: Upload food photos for ingredient detection
- **Meal Prep Planning**: Weekly meal prep optimization
- **Shopping List Generation**: Automated grocery lists
- **Cost Optimization**: Budget-conscious meal planning
- **Seasonal Ingredients**: Incorporate seasonal availability
- **Cultural Cuisine**: Region-specific meal planning

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.