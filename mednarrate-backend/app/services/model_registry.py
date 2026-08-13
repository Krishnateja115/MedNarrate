from functools import lru_cache
from transformers import pipeline

@lru_cache(maxsize=1)
def get_ner_pipeline():
    return pipeline("ner", model="d4data/biomedical-ner-all", aggregation_strategy="simple")

@lru_cache(maxsize=1)
def get_embedding_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("pritamdeka/S-PubMedBert-MS-MARCO")
