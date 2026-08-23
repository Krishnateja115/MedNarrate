import os
import glob
import chromadb
import fitz  # PyMuPDF
from chromadb.config import Settings
from app.core.config import settings

KB_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base")
KB_INDEX = os.path.join(os.path.dirname(__file__), "..", "data", "kb_index")

def build_kb():
    print("Building Knowledge Base...")
    os.makedirs(KB_INDEX, exist_ok=True)
    client = chromadb.PersistentClient(path=KB_INDEX)
    
    collection = client.get_or_create_collection("medical_knowledge")
    
    pdf_files = glob.glob(os.path.join(KB_DIR, "*.pdf"))
    if not pdf_files:
        print(f"No PDFs found in {KB_DIR}. Skipping.")
        return
        
    for pdf_path in pdf_files:
        print(f"Processing {pdf_path}")
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text").strip()
            if text:
                doc_id = f"{os.path.basename(pdf_path)}_p{page_num}"
                collection.add(
                    documents=[text],
                    metadatas=[{"source": os.path.basename(pdf_path), "page": page_num}],
                    ids=[doc_id]
                )
    print("Knowledge base built successfully.")

if __name__ == "__main__":
    build_kb()
