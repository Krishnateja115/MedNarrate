# MedNarrate: models, performance measures and explainability (XAI)

This document answers two course requirements:

1. *All deep-learning models' performance measures must be shown in the UI output.*
2. *The XAI algorithm must be reflected in the document and in the UI output.*

Every number in the UI comes from a measurement run (`scripts/evaluate_models.py`). A model that has not
been measured shows **"Not evaluated yet"**; nothing is typed in by hand.

## 1. Where it appears in the product

| Place | What it shows |
|---|---|
| **Admin portal → AI & Data Ops → Model Performance & XAI** | Every model with architecture, test data, measured scores, per-model detail (confusion matrix, per-language scores, keyword baseline), the four XAI methods, worked examples, and a box to explain your own text. |
| **App → Settings → Support & About → AI models & explainability** | The same models and scores in the user's language (8 languages), plus the XAI methods and worked examples. |
| **App → report → lab result card → "Why flagged?"** | The rule trace for that lab value: the number, the range, the distance outside it, and which rule produced the flag. |
| `docs/MODEL_RESULTS.md` | Auto-generated Markdown of the latest run, for pasting into the report. |

API: `GET /api/v1/ml/model-performance` (signed-in users), `GET /api/v1/admin/ml/model-performance`,
`POST /api/v1/admin/ml/explain/report-type` and `POST /api/v1/admin/ml/explain/entities` (admins with `ai.view`;
only the text length is written to the audit log).

## 2. Model inventory

| # | Model | Kind | Used in the live app | Task |
|---|---|---|---|---|
| 1 | `d4data/biomedical-ner-all` | Deep learning (transformer, token classification) | Yes | Finds symptoms, diseases, medicines, doses, lab terms |
| 2 | Gemini `gemini-embedding-001` | Deep learning (transformer embeddings) | Yes (BM25 fall-back) | Retrieves the parts of a user's report that answer a chat question |
| 3 | ChromaDB default `all-MiniLM-L6-v2` | Deep learning (MiniLM sentence transformer) | Yes | Retrieves general health knowledge |
| 4 | `pritamdeka/S-PubMedBert-MS-MARCO` | Deep learning (BERT) | Offline ingestion script only | Biomedical passage embeddings |
| 5 | LLM chain (Gemini, Groq, Cerebras, OpenRouter, GitHub Models) | Deep learning (large decoder-only LMs) | Yes | Summaries, grounded chat answers, translation |
| 6 | Qwen2.5-1.5B-Instruct (GGUF, CPU) | Deep learning (decoder-only LM) | Yes (offline translation fall-back) | Translation without internet |
| 7 | Whisper large-v3 (via Groq) | Deep learning (encoder-decoder speech model) | Yes (voice input) | Speech to text |
| 8 | TF-IDF + Logistic Regression | **Classical ML, not deep learning** | No (research model) | Report type: Blood / Health / TCGA |
| 9 | Lab-value extractor | **Rule-based, not machine learning** | Yes | Test name, value, unit, reference range |

Models 1-7 are the deep-learning models. Models 8 and 9 are listed so the product is described honestly; they
are shown in their own groups and are not counted as deep learning.

## 3. How each model is measured

Test sets live in `mednarrate-backend/app/ml/eval_data/` and are small and hand-checked. They show strengths and
weaknesses; they are **not** evidence of clinical accuracy.

| Model(s) | Test data | Metrics |
|---|---|---|
| 1 NER | 25 hand-labelled clinical sentences, 84 entities | Span precision, recall, F1 (a prediction counts if it overlaps the gold span with IoU ≥ 0.5), entity-type accuracy, latency |
| 2, 3, 4 embeddings | 23 questions over the 21 knowledge-base paragraphs | Recall@1/3/5, mean reciprocal rank (MRR), latency; a BM25 keyword baseline is reported next to each |
| 5 LLM chain | 10 questions answerable from a synthetic report + 5 that are not; 8 English sentences translated into 7 Indian languages | Answer accuracy, abstention rate (says "not in the report"), number preservation, chrF for Hindi, latency p50/p95 |
| 6 Qwen | The same translation set | Number preservation, chrF (Hindi), latency |
| 7 Whisper | 10 English and 5 Hindi sentences spoken by the computer's own voice | Word error rate per language, latency |
| 8 Classifier | MRAD held-out test split (12,454 reports, patient-level split) | Accuracy, macro precision/recall/F1, confusion matrix |
| 9 Lab extractor | 5 report layouts, 42 gold values (rules only; production adds an LLM fall-back) | Precision, recall, F1 per layout |

Number preservation matters in a medical product: a translation that turns 11.2 into 12.2 is dangerous, so it is
reported next to language quality.

### Reproduce

```bash
cd mednarrate-backend
python scripts/evaluate_models.py                # everything that can run on this machine
python scripts/evaluate_models.py --only ner,lab # selected parts
python scripts/evaluate_models.py --quick        # translate into Hindi and Tamil only
```

Needs the same `.env` as the backend (AI keys for models 2 and 5, `VOICE_INPUT_ENABLED=true` for model 7), the
Hugging Face models downloadable for models 1, 3, 4 and 6, and macOS (`say`, `afconvert`) to generate the speech
test audio. A part that cannot run is recorded with its reason and shown as "Could not run"; a previous good
result is never overwritten by a failed re-run. Results are written to `app/ml/artifacts/model_report.json` and
`docs/MODEL_RESULTS.md`.

## 4. Results

Measured results are in `docs/MODEL_RESULTS.md` (regenerated on every run) and in the UI. Numbers measured while
building the feature:

| Model | Result | Note |
|---|---|---|
| 9 Lab extractor (rules only) | precision 100%, recall 81.0%, F1 89.5% on 42 values | Real PDF 22/22; inline rows 5/6; vertical columns 4/4; thyroid panel 3/5; pipe-separated 0/5 (the LLM fall-back handles these in production) |
| 8 Classifier | test accuracy 100%, macro F1 100% | A perfect score on a patient-level split suggests the three MRAD sources differ in wording, so it should not be read as clinical accuracy. Short invented health-check text is misclassified, which is why the model is not wired into the app |
| BM25 keyword baseline (retrieval) | Recall@1 82.6%, Recall@3 100%, MRR 0.913 | The knowledge base is only 21 paragraphs, so Recall@3 saturates; compare the embedding models on Recall@1 and MRR |

Scores for models 1-7 appear after you run the script; until then the UI says "Not evaluated yet".

## 5. Explainability (XAI) algorithms

Implemented in `app/ml/xai.py` with plain numpy, so they run without extra dependencies and are unit-tested
(`tests/test_ml_evaluation.py`).

### 5.1 LIME, a local surrogate for any text classifier (model 8)

For a text *x* with *d* distinct words, draw *N* binary masks *z ∈ {0,1}^d* (1 = keep the word) and build the
perturbed texts. Query the model *f* (probability of the explained class). Weight each sample by a kernel on its
distance from the original

    π(z) = exp(−D(1, z)² / σ²),   D = cosine distance,   σ = 0.25

and fit the weighted ridge regression

    w* = argmin  Σ π(z) (f(z) − (w·z + b))² + λ‖w‖²

The coefficient *w_j* is the word's local effect on the predicted probability (positive = pushes towards the
class). The surrogate's weighted R² is reported as its **fidelity**, so a poor explanation is visible as such. The
seed is fixed, so the same text always gets the same explanation.

### 5.2 Exact linear attribution, SHAP for linear models (model 8)

The classifier is multinomial logistic regression, so the score of class *c* is

    s_c(x) = b_c + Σ_j W_cj · x_j

with *x_j* the TF-IDF value of feature *j*. Each feature's contribution is *φ_j = W_cj · x_j*, and
*b_c + Σ φ_j = s_c(x)* exactly (a unit test checks this against `decision_function`). For a linear model with
independent features this equals the SHAP value against a zero baseline (the empty document), which is why it is
exact and needs no sampling. The UI shows LIME and the exact attribution side by side so they can be compared.

### 5.3 Occlusion saliency for entity recognition (model 1)

For each entity the NER model finds, blank one other word at a time (replaced by spaces of equal length, so
character offsets stay valid), re-run the model, and measure

    importance(w) = p(entity | x) − p(entity | x with w blanked)

where the entity counts as lost (p = 0) if no prediction with the same type overlaps the original span (IoU ≥ 0.5).
Large positive values are context words the model relied on (Zeiler & Fergus, 2014).

### 5.4 Rule trace for lab flags (model 9, and every High/Low flag in the app)

A lab value is flagged by comparing it with the reference range printed in the report: below the lower bound is
Low, above the upper bound is High, otherwise Normal; with no range it cannot be flagged. If the laboratory
marked the value itself, that marking wins, and the "Why flagged?" sheet says so. The sheet shows the value, the
range, the distance outside it in percent, a range bar with the value marked, and the sentence that applies. It
runs on the device, so it works offline and in all 8 languages.

### 5.5 What XAI does and does not tell you

- LIME and attributions explain **the model's behaviour**, not medical truth. A word with a large weight is
  something the model used, not proof that the word is clinically meaningful.
- Large language models (models 5 and 6) and Whisper are not explained token by token; their quality is
  measured instead (section 3).
- The embedding models are measured by retrieval quality; their vectors are not interpretable word by word.

## 6. Limitations

- Test sets are small and written for this project; confidence intervals would be wide.
- Speech audio is computer-generated, so word error rates are optimistic; add real recordings to improve realism.
- Latency depends on the machine that ran the evaluation.
- The classifier's near-perfect score is probably a property of the dataset (see section 4).
