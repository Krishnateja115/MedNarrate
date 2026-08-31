import os
import sys
import argparse
import pandas as pd
import chromadb

# Ensure app imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

KB_INDEX = os.path.join(os.path.dirname(__file__), "..", "data", "kb_index")
EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "examples")

def ingest_kb(csv_path, max_records):
    print(f"Ingesting up to {max_records} records into Knowledge Base...")
    os.makedirs(KB_INDEX, exist_ok=True)
    client = chromadb.PersistentClient(path=KB_INDEX)
    collection = client.get_or_create_collection("medical_knowledge")
    
    counts = {"Blood": 0, "Health": 0, "TCGA": 0}
    max_counts = {"Blood": min(2000, max_records), "Health": min(1500, max_records), "TCGA": min(1500, max_records)}
    
    total_ingested = 0
    skipped = 0
    errors = 0
    
    for chunk in pd.read_csv(csv_path, chunksize=1000):
        # Filter
        valid_chunk = chunk[(chunk['Report_Quality_Score'] >= 95) & (chunk['Report_Text'].notna()) & (chunk['Report_Text'] != "")]
        
        for _, row in valid_chunk.iterrows():
            if total_ingested >= max_records:
                break
                
            r_type = str(row['Report_Type'])
            if counts.get(r_type, 0) >= max_counts.get(r_type, 1500):
                continue
                
            try:
                report_id = str(row['Report_ID'])
                diagnosis = str(row['Diagnosis']) if pd.notna(row['Diagnosis']) else ""
                text = str(row['Report_Text'])[:800]
                
                content = f"REPORT TYPE: {r_type}\n"
                if diagnosis:
                    content += f"DIAGNOSIS: {diagnosis}\n"
                content += f"CONTENT:\n{text}"
                
                collection.add(
                    documents=[content],
                    metadatas=[{"source": "MRAD", "report_type": r_type, "source_dataset": str(row.get('Source', 'MRAD'))}],
                    ids=[report_id]
                )
                counts[r_type] = counts.get(r_type, 0) + 1
                total_ingested += 1
                
                if total_ingested % 500 == 0:
                    print(f"Progress: Ingested {total_ingested} records...")
                    
            except chromadb.errors.IDAlreadyExistsError:
                skipped += 1
            except Exception as e:
                errors += 1
                
        if total_ingested >= max_records:
            break
            
    print(f"KB Ingestion Complete. Ingested: {total_ingested}, Skipped: {skipped}, Errors: {errors}")

def generate_examples(csv_path, max_records):
    print(f"Generating up to {max_records} examples per type...")
    os.makedirs(EXAMPLES_DIR, exist_ok=True)
    
    counts = {"Blood": 0, "Health": 0, "TCGA": 0}
    
    for chunk in pd.read_csv(csv_path, chunksize=1000):
        # Select best examples
        valid_chunk = chunk[(chunk['Report_Quality_Score'] == 100) & (chunk['Diagnosis'].notna()) & (chunk['Diagnosis'] != "")]
        
        for _, row in valid_chunk.iterrows():
            r_type = str(row['Report_Type'])
            if counts.get(r_type, 0) >= max_records:
                continue
                
            diagnosis = str(row['Diagnosis'])
            text = str(row['Report_Text'])[:600]
            
            content = f"REPORT TYPE: {r_type}\nDIAGNOSIS: {diagnosis}\nSUMMARY EXAMPLE:\n{text}\n"
            
            counts[r_type] += 1
            filename = os.path.join(EXAMPLES_DIR, f"mrad_{r_type.lower()}_example_{counts[r_type]}.txt")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
                
            if all(c >= max_records for c in counts.values()):
                break
                
        if all(c >= max_records for c in counts.values()):
            break
            
    print(f"Examples Generation Complete. Generated: {counts}")

def main():
    parser = argparse.ArgumentParser(description="Ingest MRAD Dataset")
    parser.add_argument("--csv", required=True, help="Path to Unified_Medical_Dataset.csv")
    parser.add_argument("--mode", choices=['kb', 'examples', 'both'], required=True, help="Ingestion mode")
    parser.add_argument("--max-records", type=int, default=5000, help="Max records for KB (default 5000). For examples, defaults to 10 per type.")
    
    args = parser.parse_args()
    
    if args.mode in ['kb', 'both']:
        ingest_kb(args.csv, args.max_records)
        
    if args.mode in ['examples', 'both']:
        # For examples mode, if user passed max_records=5000 (default), cap it at 10 per type as requested in instructions
        examples_max = 10 if args.max_records == 5000 else min(args.max_records, 30)
        generate_examples(args.csv, examples_max)

if __name__ == "__main__":
    main()
