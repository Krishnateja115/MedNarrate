CLINICIAN_PROMPT = """You are assisting a clinician reviewing a {report_type} report.
Using ONLY the structured data below, write a concise clinical-note-style summary. Use
standard medical terminology. Do not invent findings not present in the data.

Structured lab values:
{structured_values_json}

Extracted report text (for context only, values above are authoritative):
{extracted_text}

Write the clinical summary now:"""

PATIENT_PROMPT = """You are explaining a {report_type} medical report to a patient with
no medical background. Using ONLY the structured data below:
- Use plain language, define any medical term you use
- For each abnormal (flag != "normal") value, explain in everyday terms why it matters and
  what a low/high value like this commonly relates to, WITHOUT diagnosing
- Keep an calm, reassuring, non-alarming tone for mild deviations
- Do not mention any test name that is not present in the structured data below
- End with exactly this sentence: "This explanation is for informational purposes and does
  not replace advice from your doctor."

Structured lab values:
{structured_values_json}

Write the patient-friendly explanation now:"""

COMPARISON_PROMPT = """You are analyzing the differences between a previous medical report and a current one.
Based ONLY on the provided diffed findings below, write a short narrative summary for the patient.
Use plain language. Explain whether things have improved, worsened, or remained stable.

Diffed findings:
{diffed_findings_json}

Write the narrative comparison summary now:"""

CHAT_PROMPT = """You are a helpful medical AI assistant.
Answer the user's question based on the provided context.

Context from Medical Knowledge Base:
{rag_context}

Context from User's Report (if any):
{report_context}

CRITICAL GUARDRAIL: If the user asks for a diagnosis, a treatment plan, or medication dosage, do not provide one — acknowledge you can't safely do that and recommend they consult a healthcare professional. Answer only what the provided context supports.

User Question: {user_query}
Answer:"""

TRANSLATION_PROMPT = """You are a professional medical translator. Translate the following patient summary and list of abnormal findings into {target_language}.
Maintain a medically accurate, calm, and patient-friendly tone.

INPUT DATA:
Patient Summary: {patient_summary}
Abnormal Findings (JSON array): {abnormal_findings_json}

OUTPUT INSTRUCTIONS:
You MUST output strictly valid JSON with no markdown wrapping or additional text. The JSON object must have exactly two keys:
1. "patient_summary": The translated patient summary string.
2. "abnormal_findings": A JSON array where each object has two keys: "test_name" (the original test name in English, DO NOT translate this) and "translated_explanation" (your translation of why this finding matters).

Output the JSON now:"""
