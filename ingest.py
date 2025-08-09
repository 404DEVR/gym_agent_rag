import os
import fitz  # PyMuPDF for PDF extraction
import faiss
import numpy as np
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY") or "YOUR_GEMINI_KEY_HERE")

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text

def extract_text_from_txt(txt_path):
    with open(txt_path, 'r', encoding='utf-8') as f:
        return f.read()

def chunk_text(text, chunk_size=500):
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

def ingest_files(folder_path, index_name, txt_name):
    dimension = 768
    index = faiss.IndexFlatL2(dimension)
    texts, embeddings = [], []

    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        raw_text = ""
        
        if file_name.endswith(".pdf"):
            raw_text = extract_text_from_pdf(file_path)
        elif file_name.endswith(".txt"):
            raw_text = extract_text_from_txt(file_path)
        else:
            continue
            
        chunks = chunk_text(raw_text)
        for chunk in chunks:
            try:
                embedding = genai.embed_content(
                    model="models/embedding-001",
                    content=chunk
                )["embedding"]
                embeddings.append(embedding)
                texts.append(chunk)
            except Exception as e:
                continue

    if embeddings:
        embeddings_np = np.array(embeddings).astype("float32")
        index.add(embeddings_np)
        faiss.write_index(index, f"data/{index_name}")
        
        with open(f"data/{txt_name}", "w", encoding="utf-8") as f:
            for t in texts:
                f.write(t + "\n")
    else:
        pass

if __name__ == "__main__":
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Create 2 separate indexes
    ingest_files("pdfs/workouts", "workout.index", "workout.txt")
    ingest_files("pdfs/nutrition", "nutrition.index", "nutrition.txt") 