"""Build the general medical knowledge base that chat searches for health questions.

Sources (both optional):
  data/knowledge_base/*.pdf   medical textbook PDFs or clinical guidelines you drop in
  data/knowledge/*.md|*.txt   the short reference notes that ship with the project

Safe to run again: chunks have fixed ids and are upserted, so nothing is duplicated.
Run from the mednarrate-backend folder:  python scripts/build_knowledge_base.py
"""
import glob
import os

import chromadb

ROOT = os.path.join(os.path.dirname(__file__), "..", "data")
PDF_DIR = os.path.join(ROOT, "knowledge_base")
NOTES_DIR = os.path.join(ROOT, "knowledge")
KB_INDEX = os.path.join(ROOT, "kb_index")


def _note_chunks(path: str):
    """One chunk per paragraph; a heading line stays with the paragraph after it."""
    with open(path, "r", encoding="utf-8") as f:
        paragraphs = [p.strip() for p in f.read().split("\n\n") if p.strip()]
    title = ""
    for p in paragraphs:
        if p.startswith("#") and "\n" not in p:
            title = p.lstrip("# ").strip()
            continue
        yield (f"{title}\n{p}" if title else p)


def build_kb(embedding_function=None) -> int:
    print("Building Knowledge Base...")
    os.makedirs(KB_INDEX, exist_ok=True)
    client = chromadb.PersistentClient(
        path=KB_INDEX,
        settings=chromadb.Settings(anonymized_telemetry=False),
    )
    kwargs = {"embedding_function": embedding_function} if embedding_function else {}
    collection = client.get_or_create_collection("medical_knowledge", **kwargs)

    ids, docs, metas = [], [], []

    for path in sorted(
        glob.glob(os.path.join(NOTES_DIR, "*.md")) + glob.glob(os.path.join(NOTES_DIR, "*.txt"))
    ):
        name = os.path.basename(path)
        for i, chunk in enumerate(_note_chunks(path)):
            ids.append(f"{name}_c{i}")
            docs.append(chunk)
            metas.append({"source": name, "chunk": i})

    pdf_files = sorted(glob.glob(os.path.join(PDF_DIR, "*.pdf")))
    if pdf_files:
        import fitz  # PyMuPDF, only needed when PDFs are present

        for pdf_path in pdf_files:
            print(f"Processing {pdf_path}")
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                text = doc.load_page(page_num).get_text("text").strip()
                if text:
                    name = os.path.basename(pdf_path)
                    ids.append(f"{name}_p{page_num}")
                    docs.append(text)
                    metas.append({"source": name, "page": page_num})

    if not ids:
        print(f"Nothing to index. Add notes to {NOTES_DIR} or PDFs to {PDF_DIR}.")
        return 0

    collection.upsert(ids=ids, documents=docs, metadatas=metas)
    print(f"Knowledge base built: {len(ids)} chunks indexed ({collection.count()} in total).")
    return len(ids)


if __name__ == "__main__":
    build_kb()
