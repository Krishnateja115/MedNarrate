# MedNarrate Data Directory

This directory stores offline reference materials and knowledge base chunks.

## Knowledge Base Index

The `kb_index` directory stores the ChromaDB persistent index used for RAG generation by the Chat API.

## MRAD Dataset Integration

MedNarrate ships with support for the MedNarrate Unified Medical Dataset (MRAD) v1.0,
a 123,371-report collection of Blood, Health, and TCGA Pathology reports.

### Ingesting MRAD into the Knowledge Base

1. Download the MRAD dataset ZIP and extract it
2. Run the ingestion scripts:

```bash
cd mednarrate-backend
# Ingest representative reports into ChromaDB (RAG knowledge base)
# and generate few-shot examples for Gemini
python scripts/ingest_mrad_dataset.py \
  --csv /path/to/MRAD/Unified_Medical_Dataset.csv \
  --mode both \
  --max-records 5000

# Ingest structured lab reference values
python scripts/ingest_mrad_lab_references.py \
  --csv /path/to/MRAD/Lab_Values.csv
```

This enhances the AI's ability to:
- Provide grounded, factual explanations of lab values
- Reference real anonymized medical report patterns
- Generate better-formatted summaries via few-shot examples
