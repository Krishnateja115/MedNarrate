import logging
import os
import sys

# Ensure app directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ml.dataset_loader import MRADDatasetLoader
from app.ml.medical_classifier import MedicalReportClassifier

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=== Starting Full MRAD Dataset Training Pipeline ===")
    loader = MRADDatasetLoader()
    df, summary = loader.load_and_preprocess()

    logger.info("Summary of loaded dataset:")
    for k, v in summary.items():
        logger.info(f"  {k}: {v}")

    logger.info(
        "Performing patient-level GroupKFold split (80% train, 10% val, 10% test)..."
    )
    train_df, val_df, test_df = MRADDatasetLoader.patient_level_split(
        df, random_seed=42
    )

    logger.info("Initializing MedicalReportClassifier and starting training...")
    classifier = MedicalReportClassifier()
    metrics = classifier.train_and_evaluate(train_df, val_df, test_df, summary)

    logger.info("=== Training completed successfully! ===")
    logger.info(f"Test Accuracy: {metrics['test_accuracy']:.4f}")
    logger.info(f"Test Macro F1: {metrics['test_f1_macro']:.4f}")
    logger.info("Per-class performance:")
    for cls_name, cls_metrics in metrics["per_class_report"].items():
        if isinstance(cls_metrics, dict):
            logger.info(
                f"  {cls_name}: Precision={cls_metrics['precision']:.4f}, Recall={cls_metrics['recall']:.4f}, F1={cls_metrics['f1-score']:.4f}"
            )


if __name__ == "__main__":
    main()
