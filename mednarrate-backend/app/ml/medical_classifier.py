import os
import json
import logging
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, classification_report
from app.ml.dataset_loader import clean_report_text_features

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "artifacts")
)

class MedicalReportClassifier:
    def __init__(self, artifacts_dir: str = None):
        self.artifacts_dir = artifacts_dir or ARTIFACTS_DIR
        os.makedirs(self.artifacts_dir, exist_ok=True)
        self.vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1, 2), min_df=2)
        self.label_encoder = LabelEncoder()
        self.model = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
        self.is_trained = False

    def train_and_evaluate(self, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame, dataset_summary: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Fitting LabelEncoder and TF-IDF Vectorizer on clean MRAD report text...")
        y_train = self.label_encoder.fit_transform(train_df['target_label'])
        y_val = self.label_encoder.transform(val_df['target_label'])
        y_test = self.label_encoder.transform(test_df['target_label'])

        text_col = 'clean_text' if 'clean_text' in train_df.columns else 'Report_Text'
        X_train = self.vectorizer.fit_transform(train_df[text_col])
        X_val = self.vectorizer.transform(val_df[text_col])
        X_test = self.vectorizer.transform(test_df[text_col])

        logger.info(f"Training LogisticRegression model on {X_train.shape[0]} clean training samples...")
        self.model.fit(X_train, y_train)
        self.is_trained = True

        val_preds = self.model.predict(X_val)
        val_acc = accuracy_score(y_val, val_preds)

        test_preds = self.model.predict(X_test)
        test_acc = accuracy_score(y_test, test_preds)
        prec, rec, f1, _ = precision_recall_fscore_support(y_test, test_preds, average='macro')
        w_prec, w_rec, w_f1, _ = precision_recall_fscore_support(y_test, test_preds, average='weighted')
        cm = confusion_matrix(y_test, test_preds).tolist()
        class_names = [str(c) for c in self.label_encoder.classes_]

        per_class = classification_report(y_test, test_preds, target_names=class_names, output_dict=True)

        metrics = {
            "dataset_info": {
                "dataset_path": dataset_summary["dataset_path"],
                "raw_record_count": dataset_summary["raw_record_count"],
                "usable_record_count": dataset_summary["usable_record_count"],
                "excluded_duplicates": dataset_summary["excluded_duplicates"],
                "unique_patients": dataset_summary["unique_patients"],
                "train_samples": len(train_df),
                "val_samples": len(val_df),
                "test_samples": len(test_df),
                "class_names": class_names,
                "feature_cleaning": "Metadata header stripping applied (re.sub Report Type header)"
            },
            "validation_accuracy": float(val_acc),
            "test_accuracy": float(test_acc),
            "test_precision_macro": float(prec),
            "test_recall_macro": float(rec),
            "test_f1_macro": float(f1),
            "test_precision_weighted": float(w_prec),
            "test_recall_weighted": float(w_rec),
            "test_f1_weighted": float(w_f1),
            "confusion_matrix": cm,
            "per_class_report": per_class
        }

        self.save_artifacts(metrics)
        logger.info(f"Leakage-Safe Model Training Complete! Test Accuracy: {test_acc:.4f}, Macro F1: {f1:.4f}")
        return metrics

    def save_artifacts(self, metrics: Dict[str, Any]):
        model_path = os.path.join(self.artifacts_dir, "medical_classifier.joblib")
        vectorizer_path = os.path.join(self.artifacts_dir, "vectorizer.joblib")
        encoder_path = os.path.join(self.artifacts_dir, "label_encoder.joblib")
        metrics_path = os.path.join(self.artifacts_dir, "metrics.json")
        metadata_path = os.path.join(self.artifacts_dir, "metadata.json")

        joblib.dump(self.model, model_path)
        joblib.dump(self.vectorizer, vectorizer_path)
        joblib.dump(self.label_encoder, encoder_path)

        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)

        metadata = {
            "model_type": "LogisticRegression + TFIDF",
            "mrad_dataset": "FULL",
            "raw_records": metrics["dataset_info"]["raw_record_count"],
            "duplicates_removed": metrics["dataset_info"]["excluded_duplicates"],
            "usable_records": metrics["dataset_info"]["usable_record_count"],
            "train_records": metrics["dataset_info"]["train_samples"],
            "validation_records": metrics["dataset_info"]["val_samples"],
            "test_records": metrics["dataset_info"]["test_samples"],
            "unique_patients": metrics["dataset_info"]["unique_patients"],
            "target": "Report_Type (Source)",
            "classes": metrics["dataset_info"]["class_names"],
            "features_used": ["cleaned_report_text_tfidf"],
            "split_method": "patient-level GroupKFold",
            "random_seed": 42,
            "test_accuracy": metrics["test_accuracy"],
            "test_f1_macro": metrics["test_f1_macro"]
        }
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved versioned leakage-safe artifacts to {self.artifacts_dir}")

    def load_artifacts(self):
        model_path = os.path.join(self.artifacts_dir, "medical_classifier.joblib")
        vectorizer_path = os.path.join(self.artifacts_dir, "vectorizer.joblib")
        encoder_path = os.path.join(self.artifacts_dir, "label_encoder.joblib")

        if not (os.path.exists(model_path) and os.path.exists(vectorizer_path) and os.path.exists(encoder_path)):
            raise FileNotFoundError(f"Model artifacts missing from {self.artifacts_dir}")

        self.model = joblib.load(model_path)
        self.vectorizer = joblib.load(vectorizer_path)
        self.label_encoder = joblib.load(encoder_path)
        self.is_trained = True

    def predict(self, text: str) -> Dict[str, Any]:
        if not self.is_trained:
            self.load_artifacts()

        clean_text = clean_report_text_features(text)
        X = self.vectorizer.transform([clean_text])
        pred_idx = self.model.predict(X)[0]
        probs = self.model.predict_proba(X)[0]

        predicted_class = str(self.label_encoder.inverse_transform([pred_idx])[0])
        confidence = float(np.max(probs))

        return {
            "predicted_category": predicted_class,
            "confidence": confidence,
            "class_probabilities": {
                str(cls): float(prob)
                for cls, prob in zip(self.label_encoder.classes_, probs)
            }
        }
