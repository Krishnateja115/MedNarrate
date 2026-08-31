import os
import sys
import argparse
import pandas as pd
import chromadb
import asyncio

# Ensure app imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.llm_client import generate

KB_INDEX = os.path.join(os.path.dirname(__file__), "..", "data", "kb_index")

async def generate_descriptions(tests):
    print(f"Generating descriptions for {len(tests)} tests...")
    prompt = "You are a clinical pathologist. For each of the following lab tests, provide a one-sentence plain-language description of what it measures. Format your response exactly as 'TestName: Description'.\n\nTests:\n"
    for t in tests:
        prompt += f"- {t}\n"
        
    try:
        response = await generate(prompt, timeout=120.0)
        
        # parse response
        descriptions = {}
        for line in response.strip().split('\n'):
            if ':' in line:
                name, desc = line.split(':', 1)
                name = name.strip().replace('-', '').strip()
                descriptions[name] = desc.strip()
        return descriptions
    except Exception as e:
        print(f"Failed to generate descriptions: {e}")
        return {}

async def process_lab_values(csv_path):
    print("Reading Lab_Values.csv...")
    os.makedirs(KB_INDEX, exist_ok=True)
    client = chromadb.PersistentClient(path=KB_INDEX)
    collection = client.get_or_create_collection("medical_knowledge")
    
    # Read CSV and find unique tests
    df = pd.read_csv(csv_path)
    
    # Filter to valid reference ranges
    valid_tests = df[(df['test_name'].notna()) & (df['reference_range'].notna()) & (df['unit'].notna())]
    
    # Deduplicate by test_name and unit
    unique_tests = valid_tests.drop_duplicates(subset=['test_name', 'unit'])
    
    tests_list = unique_tests['test_name'].tolist()
    
    print(f"Found {len(tests_list)} unique lab tests.")
    
    # Batch by 50
    batch_size = 50
    all_descriptions = {}
    
    for i in range(0, len(tests_list), batch_size):
        batch = tests_list[i:i+batch_size]
        descs = await generate_descriptions(batch)
        all_descriptions.update(descs)
        
    # Ingest into ChromaDB
    total_ingested = 0
    skipped = 0
    
    for _, row in unique_tests.iterrows():
        test_name = str(row['test_name'])
        unit = str(row['unit'])
        ref_range = str(row['reference_range'])
        
        desc = all_descriptions.get(test_name, "This test measures specific biomarkers in the blood.")
        content = f"Normal range for {test_name}: {ref_range} {unit}. {desc}"
        doc_id = f"lab_ref_{test_name.replace(' ', '_')}"
        
        try:
            collection.add(
                documents=[content],
                metadatas=[{"source": "MRAD_lab_ref", "test_name": test_name}],
                ids=[doc_id]
            )
            total_ingested += 1
        except chromadb.errors.IDAlreadyExistsError:
            skipped += 1
            
    print(f"Lab Reference Ingestion Complete. Ingested: {total_ingested}, Skipped: {skipped}")

def main():
    parser = argparse.ArgumentParser(description="Ingest MRAD Lab References")
    parser.add_argument("--csv", required=True, help="Path to Lab_Values.csv")
    args = parser.parse_args()
    
    asyncio.run(process_lab_values(args.csv))

if __name__ == "__main__":
    main()
