# AI Fitness & Diet Coach - RAG + Gemini API

A personalized fitness and nutrition coach using Retrieval-Augmented Generation (RAG), Gemini AI, and FAISS for vector similarity search.

## Features
- 🏋️ Personalized workout plans (gym, home gym, bodyweight/calisthenics)
- 🥗 Adaptive nutrition plans (cooking, no-cook, hostel-friendly)
- 🧠 RAG-powered responses using research-based fitness knowledge
- 💬 Conversational chat interface
- 🎯 Context-aware recommendations based on user constraints

## Quick Deploy

### Railway (Recommended)
1. Fork this repository
2. Connect to Railway
3. Set environment variables:
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `FRONTEND_URL`: Your Vercel app URL (e.g., https://your-app.vercel.app)
   - `ENVIRONMENT`: production
4. Deploy automatically

### Render
1. Fork this repository
2. Connect to Render
3. Set environment variables (same as above)
4. Deploy with `render.yaml` configuration

### Manual Docker Deploy
```bash
docker build -t fitness-rag-agent .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key fitness-rag-agent
```

## Environment Variables
- `GEMINI_API_KEY`: Required - Your Google Gemini API key
- `FRONTEND_URL`: Your frontend URL for CORS
- `ENVIRONMENT`: Set to "production" for production deployment
- `SPOONACULAR_API_KEY`: Optional - For enhanced food suggestions

## API Endpoints
- `POST /chat` - Conversational chat with the fitness agent
- `POST /api/generate-plan` - Generate detailed fitness/nutrition plans
- `GET /api/health` - Health check endpoint
- `POST /api/test-scenarios` - Test different user scenarios

## Local Development
```bash
pip install -r requirements.txt
python ingest.py  # Build knowledge base
uvicorn app:app --reload --port 8000
```

## Knowledge Base
The system uses research-based PDFs for:
- Workout principles and calisthenics
- Nutrition fundamentals and hostel-friendly meals
- Evidence-based fitness recommendations

Built with FastAPI, FAISS, and Google Gemini AI.