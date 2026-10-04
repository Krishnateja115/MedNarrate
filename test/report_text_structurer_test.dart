import 'package:flutter_test/flutter_test.dart';
import 'package:mednarrate/core/utils/report_text_structurer.dart';

/// Strips every character the structurer is allowed to introduce
/// (whitespace, "###" heading markers and "•" bullets) so we can prove the
/// translated wording itself is untouched.
String _core(String s) => s.replaceAll(RegExp(r'[\s#•]'), '');

void main() {
  group('ReportTextStructurer.restoreStructure', () {
    test('returns already-structured (English / Telugu) text unchanged', () {
      const english = '### 1. What Your Report Says\n'
          'Your report contains 20 results.\n\n'
          '### 2. Key Findings\n• MCV: 80.0 — LOW (range: 81.0 - 101.0).';
      expect(ReportTextStructurer.restoreStructure(english), same(english));
    });

    test('restores numbered sections and lab items for a flattened Malayalam summary', () {
      const ml = '1. നിങ്ങളുടെ റിപ്പോർട്ട് പറയുന്നത്: നിങ്ങളുടെ റിപ്പോർട്ടിൽ 20 ലബോറട്ടറി പരിശോധനാ ഫലങ്ങൾ അടങ്ങിയിരിക്കുന്നു. '
          '2. പ്രധാന കണ്ടെത്തലുകൾ: ഫ്ലാഗ് ചെയ്ത ഫലങ്ങൾ: MCV: 80.0 — ഫ്ലാഗ് ചെയ്തത് കുറവ് (പരിധി: 81.0 - 101.0). '
          'MCHC: 37.5 — ഫ്ലാഗ് ചെയ്തത് ഉയർന്നത് (പരിധി: 31.5 - 34.5). '
          'സാധാരണ ഫലങ്ങൾ: ഹീമോഗ്ലോബിൻ: 15.0 — സാധാരണ (പരിധി: 13.0 - 17.0).';
      final out = ReportTextStructurer.restoreStructure(ml);
      final lines = out.split('\n').where((l) => l.trim().isNotEmpty).toList();

      expect(lines.first, '### 1. നിങ്ങളുടെ റിപ്പോർട്ട് പറയുന്നത്:');
      expect(lines, contains('### 2. പ്രധാന കണ്ടെത്തലുകൾ:'));
      expect(lines, contains('ഫ്ലാഗ് ചെയ്ത ഫലങ്ങൾ:'));
      expect(lines, contains('• MCV: 80.0 — ഫ്ലാഗ് ചെയ്തത് കുറവ് (പരിധി: 81.0 - 101.0).'));
      expect(lines, contains('സാധാരണ ഫലങ്ങൾ:'));
      expect(lines.last, '• ഹീമോഗ്ലോബിൻ: 15.0 — സാധാരണ (പരിധി: 13.0 - 17.0).');
      // Translated wording, numbers and punctuation preserved exactly.
      expect(_core(out), _core(ml));
    });

    test('recognises native-script section numbers (Marathi / Bengali)', () {
      const mr = '१. तुमचा अहवाल काय सांगतो: तुमच्या अहवालात २० निकाल आहेत. '
          '२. मुख्य निष्कर्ष: MCV: 80.0 — कमी (मर्यादा: 81.0 - 101.0). MCHC: 37.5 — जास्त (मर्यादा: 31.5 - 34.5).';
      final out = ReportTextStructurer.restoreStructure(mr);
      expect(out, contains('### १. तुमचा अहवाल काय सांगतो:'));
      expect(out, contains('### २. मुख्य निष्कर्ष:'));
      expect(out, contains('\n• MCHC: 37.5 — जास्त (मर्यादा: 31.5 - 34.5).'));
      expect(_core(out), _core(mr));

      const bn = '১. আপনার রিপোর্টে ২০টি ফলাফল রয়েছে। ২. মূল ফলাফল: MCV: 80.0 — LOW (সীমা: 81.0 - 101.0)। MCHC: 37.5 — HIGH (সীমা: 31.5 - 34.5)।';
      final outBn = ReportTextStructurer.restoreStructure(bn);
      expect(outBn, contains('### ২. মূল ফলাফল:'));
      expect(outBn, contains('\n• MCHC: 37.5 — HIGH (সীমা: 31.5 - 34.5)।'));
      expect(_core(outBn), _core(bn));
    });

    test('splits explicit inline bullets (Kannada style)', () {
      const kn = '1. ವರದಿ: ಫಲಿತಾಂಶಗಳು. 2. ಪ್ರಮುಖ: ಹೊರಗಿನ ಫಲಿತಾಂಶಗಳು: • MCV: 80.0 — ಕಡಿಮೆ (ವ್ಯಾಪ್ತಿ: 81.0 - 101.0). '
          'ಸಾಮಾನ್ಯ ಫಲಿತಾಂಶಗಳು: • ಹಿಮೋಗ್ಲೋಬಿನ್: 15.0 — ಸಾಮಾನ್ಯ (ವ್ಯಾಪ್ತಿ: 13.0 - 17.0).';
      final lines = ReportTextStructurer.restoreStructure(kn).split('\n');
      expect(lines, contains('ಹೊರಗಿನ ಫಲಿತಾಂಶಗಳು:'));
      expect(lines, contains('• MCV: 80.0 — ಕಡಿಮೆ (ವ್ಯಾಪ್ತಿ: 81.0 - 101.0).'));
      expect(lines, contains('ಸಾಮಾನ್ಯ ಫಲಿತಾಂಶಗಳು:'));
      expect(lines, contains('• ಹಿಮೋಗ್ಲೋಬಿನ್: 15.0 — ಸಾಮಾನ್ಯ (ವ್ಯಾಪ್ತಿ: 13.0 - 17.0).'));
    });

    test('does not treat decimals or non-sequential numbers as sections', () {
      const prose = 'Value 80.0 is fine. 3. Not a section. Plain sentence.';
      expect(ReportTextStructurer.restoreStructure(prose), prose);
    });
  });
}
