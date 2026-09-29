"""Offline contract tests. Native-script fixtures are not live model results."""
import json
import unittest

from app.services.translation_validation import parse_translation, validate_translation


class TranslationValidationTests(unittest.TestCase):
    def payload(self, text="మీ రక్త పరీక్ష నివేదిక"):
        return {
            "patient_summary": f"{text} Hemoglobin 10.2 g/dL (12-16 g/dL)",
            "abnormal_findings": [{"test_name": "Hemoglobin", "translated_explanation": text}],
            "medications": [{"medication_name": "Iron", "translated_dosage": "100 mg",
                             "translated_frequency": text, "translated_times_of_day": ["08:00"],
                             "translated_instructions": text}],
            "doctor_discussion_points": [text], "ui_labels": {"heading": text},
        }

    def validate(self, payload, language="te"):
        return validate_translation(payload, language,
            "Hemoglobin 10.2 g/dL (12-16 g/dL)",
            [{"test_name": "Hemoglobin", "value": 10.2, "unit": "g/dL", "flag": "low"}],
            [{"medication_name": "Iron", "dosage": "100 mg", "frequency": "daily",
              "times_of_day": ["08:00"], "instructions": "After food"}], ["heading"])

    def test_supported_native_scripts(self):
        for language, text in {
            "te": "మీ రక్త పరీక్ష నివేదిక", "ta": "உங்கள் இரத்த பரிசோதனை அறிக்கை",
            "kn": "ನಿಮ್ಮ ರಕ್ತ ಪರೀಕ್ಷಾ ವರದಿ", "ml": "നിങ്ങളുടെ രക്ത പരിശോധന റിപ്പോർട്ട്",
            "hi": "आपकी रक्त परीक्षण रिपोर्ट", "mr": "तुमचा रक्त तपासणी अहवाल",
            "bn": "আপনার রক্ত পরীক্ষার রিপোর্ট",
        }.items():
            with self.subTest(language=language):
                result = self.validate(self.payload(text), language)
                self.assertEqual(result['abnormal_findings'][0]['value'], 10.2)
                self.assertEqual(result['abnormal_findings'][0]['unit'], 'g/dL')

    def test_rejects_english_transliteration_and_wrong_script(self):
        for text in ['English report', 'mee raktha pariksha nivedika', 'आपकी रक्त परीक्षण रिपोर्ट']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.validate(self.payload(text))

    def test_rejects_changed_values_units_and_identifiers(self):
        for old, new in [('10.2', '12.0'), ('g/dL', 'mg/dL'), ('Hemoglobin', 'Glucose')]:
            p = self.payload()
            p['patient_summary'] = p['patient_summary'].replace(old, new)
            with self.subTest(old=old), self.assertRaises(ValueError):
                self.validate(p)

    def test_rejects_missing_entries_and_labels(self):
        for key in ['abnormal_findings', 'medications', 'doctor_discussion_points', 'ui_labels']:
            p = self.payload()
            p[key] = {} if key == 'ui_labels' else []
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate(p)

    def test_rejects_changed_medication_facts(self):
        for key, value in [('medication_name', 'Other'), ('translated_dosage', '200 mg'), ('translated_times_of_day', ['09:00'])]:
            p = self.payload()
            p['medications'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate(p)

    def test_rejects_invented_discussion_values(self):
        p = self.payload()
        p['doctor_discussion_points'][0] += ' 999'
        with self.assertRaises(ValueError):
            self.validate(p)

    def test_json_fences_and_embedded_braces(self):
        p = self.payload()
        p['patient_summary'] += ' {note}'
        self.assertEqual(parse_translation('```json\n'+json.dumps(p)+'\n```'), p)

    def test_rejects_truncated_nonobject_or_trailing_json(self):
        for value in ['{"patient_summary":', '[]', '{} {}', 'text {"x": 1}']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_translation(value)


if __name__ == '__main__':
    unittest.main()
