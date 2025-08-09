import faiss
import numpy as np
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY") or "YOUR_GEMINI_KEY_HERE")

# ✅ Load indexes with error handling
def load_index_safely(index_path):
    try:
        return faiss.read_index(index_path)
    except:
        return None

workout_index = load_index_safely("data/workout.index")
nutrition_index = load_index_safely("data/nutrition.index")

def retrieve_workouts(query, top_k=5):
    if workout_index is None:
        return ["Progressive overload is key for muscle growth", "Compound exercises like squats and deadlifts are most effective", "Rest 48-72 hours between training same muscle groups"]
    
    try:
        query_embedding = genai.embed_content(
            model="models/embedding-001",
            content=query
        )["embedding"]
        distances, indices = workout_index.search(np.array([query_embedding], dtype="float32"), top_k)
        with open("data/workout.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        return [lines[i].strip() for i in indices[0]]
    except:
        return ["Progressive overload is key for muscle growth", "Compound exercises like squats and deadlifts are most effective", "Rest 48-72 hours between training same muscle groups"]

def retrieve_nutrition(query, top_k=5):
    if nutrition_index is None:
        return ["Protein intake should be 1.6-2.2g per kg bodyweight", "Eat in a caloric deficit for fat loss, surplus for muscle gain", "Include variety of whole foods for micronutrients"]
    
    try:
        query_embedding = genai.embed_content(
            model="models/embedding-001",
            content=query
        )["embedding"]
        distances, indices = nutrition_index.search(np.array([query_embedding], dtype="float32"), top_k)
        with open("data/nutrition.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        return [lines[i].strip() for i in indices[0]]
    except:
        return ["Protein intake should be 1.6-2.2g per kg bodyweight", "Eat in a caloric deficit for fat loss, surplus for muscle gain", "Include variety of whole foods for micronutrients"] 