import os
import re
import logging
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)

# Search paths for full MRAD dataset
POSSIBLE_PATHS = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "mrad_full", "MRAD", "Unified_Medical_Dataset.csv")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "mrad_full", "MRAD", "Unified_Medical_Dataset.csv")),
    os.path.abspath("C:/Users/manas/Downloads/MedNarrate-main/data/mrad_full/MRAD/Unified_Medical_Dataset.csv")
]

def get_mrad_dataset_path() -> str:
    env_path = os.getenv("MRAD_DATASET_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
    for p in POSSIBLE_PATHS:
        if os.path.exists(p):
            return p
    return POSSIBLE_PATHS[0]

def clean_report_text_features(text: str) -> str:
    """
    Strips explicit metadata header lines (e.g. 'Report Type : Blood Test')
    to ensure ML feature vectors represent pure clinical document content
    without direct header label leakage.
    """
    if not text:
        return ""
    text_str = str(text)
    cleaned = re.sub(r'(?i)^\s*Report\s+Type\s*:\s*[^\n]+\n?', '', text_str)
    cleaned = re.sub(r'(?i)^\s*Source\s*:\s*[^\n]+\n?', '', cleaned)
    return cleaned.strip()

class MRADDatasetLoader:
    def __init__(self, csv_path: str = None):
        self.csv_path = csv_path or get_mrad_dataset_path()
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"MRAD Dataset file not found at: {self.csv_path}")

    def load_and_preprocess(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        logger.info(f"Loading full MRAD dataset from {self.csv_path}...")
        df_raw = pd.read_csv(self.csv_path, low_memory=False)
        raw_count = len(df_raw)

        df = df_raw.copy()
        df.columns = [c.strip() for c in df.columns]

        # Filter empty text
        df = df[df['Report_Text'].notnull()]
        df['Report_Text'] = df['Report_Text'].astype(str).str.strip()
        df = df[df['Report_Text'] != '']
        
        # Deduplicate exact patient-text duplicates
        duplicates_count = df.duplicated(subset=['Patient_ID', 'Report_Text']).sum()
        df = df.drop_duplicates(subset=['Patient_ID', 'Report_Text']).reset_index(drop=True)

        # Apply header-stripping for leakage-safe features
        df['clean_text'] = df['Report_Text'].apply(clean_report_text_features)
        df['target_label'] = df['Source'].astype(str).str.strip()

        usable_count = len(df)
        patient_count = df['Patient_ID'].nunique()
        report_count = df['Report_ID'].nunique()
        class_distribution = df['target_label'].value_counts().to_dict()

        summary = {
            "dataset_path": self.csv_path,
            "raw_record_count": raw_count,
            "usable_record_count": usable_count,
            "excluded_duplicates": int(duplicates_count),
            "unique_patients": int(patient_count),
            "unique_reports": int(report_count),
            "class_distribution": class_distribution
        }

        logger.info(f"MRAD Dataset Loaded. Raw: {raw_count}, Usable: {usable_count}, Patients: {patient_count}")
        return df, summary

    @staticmethod
    def patient_level_split(df: pd.DataFrame, random_seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Executes a patient-level split (80% train, 10% val, 10% test) to prevent data leakage.
        Ensures reports from the same patient NEVER overlap across splits.
        """
        unique_patients = list(df['Patient_ID'].unique())
        np.random.seed(random_seed)
        np.random.shuffle(unique_patients)

        n_patients = len(unique_patients)
        train_end = int(0.80 * n_patients)
        val_end = int(0.90 * n_patients)

        train_pts = set(unique_patients[:train_end])
        val_pts = set(unique_patients[train_end:val_end])
        test_pts = set(unique_patients[val_end:])

        train_df = df[df['Patient_ID'].isin(train_pts)].copy().reset_index(drop=True)
        val_df = df[df['Patient_ID'].isin(val_pts)].copy().reset_index(drop=True)
        test_df = df[df['Patient_ID'].isin(test_pts)].copy().reset_index(drop=True)

        # Leakage Verification Check
        overlap_tv = set(train_df['Patient_ID']).intersection(set(val_df['Patient_ID']))
        overlap_tt = set(train_df['Patient_ID']).intersection(set(test_df['Patient_ID']))
        overlap_vt = set(val_df['Patient_ID']).intersection(set(test_df['Patient_ID']))

        if overlap_tv or overlap_tt or overlap_vt:
            raise ValueError(f"CRITICAL: Patient data leakage detected! Overlap: TV={len(overlap_tv)}, TT={len(overlap_tt)}, VT={len(overlap_vt)}")

        logger.info(f"Patient-level split completed. Train: {len(train_df)} ({len(train_pts)} pts), Val: {len(val_df)} ({len(val_pts)} pts), Test: {len(test_df)} ({len(test_pts)} pts)")
        return train_df, val_df, test_df
