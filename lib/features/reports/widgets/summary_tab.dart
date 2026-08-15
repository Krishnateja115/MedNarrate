import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../reports/models/report_model.dart';
import '../../../core/utils/formatters.dart';
import '../../../core/utils/helpers.dart';

class SummaryTab extends StatelessWidget {
  final ReportModel report;
  final bool isProfessionalMode;

  const SummaryTab({super.key, required this.report, required this.isProfessionalMode});

  void _showTranslationBottomSheet(BuildContext context) {
    // Show bottom sheet with 8 languages (Mock implementation)
    final languages = {
      'en': 'English',
      'hi': 'Hindi (हिन्दी)',
      'ta': 'Tamil (தமிழ்)',
      'te': 'Telugu (తెలుగు)',
      'kn': 'Kannada (ಕನ್ನಡ)',
      'ml': 'Malayalam (മലയാളം)',
      'mr': 'Marathi (मराठी)',
      'bn': 'Bengali (বাংলা)',
    };

    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (_) {
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('Translate Summary', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              SizedBox(height: 16),
              Expanded(
                child: ListView(
                  children: languages.entries.map((e) {
                    return ListTile(
                      title: Text(e.value),
                      onTap: () {
                        Navigator.pop(context);
                        Helpers.showSuccess(context, 'Translated to ${e.value} (Coming Soon)');
                      },
                    );
                  }).toList(),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Patient Info Card
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.border),
            ),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 30,
                  backgroundColor: AppColors.primary.withValues(alpha: 0.1),
                  child: Icon(Icons.person, color: AppColors.primary, size: 30),
                ),
                SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('John Doe', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      Text('Male, 34 yrs', style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5))),
                      SizedBox(height: 8),
                      Row(
                        children: [
                          Icon(Icons.calendar_today, size: 14, color: Theme.of(context).colorScheme.primary),
                          SizedBox(width: 4),
                          Text(Formatters.formatDate(report.uploadedAt), style: TextStyle(fontSize: 12)),
                          SizedBox(width: 12),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: AppColors.accentTeal.withValues(alpha: 0.1),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(Helpers.reportTypeLabel(report.reportType), style: TextStyle(fontSize: 10, color: AppColors.accentTeal)),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          
          SizedBox(height: 24),

          // Abnormal Values Alert
          if (report.metrics.isNotEmpty) // Mock condition
            Container(
              margin: const EdgeInsets.only(bottom: 24),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.red.withValues(alpha: 0.05),
                borderRadius: BorderRadius.circular(12),
                border: Border(left: BorderSide(color: Colors.red, width: 4)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.warning_amber_rounded, color: Colors.red),
                      SizedBox(width: 8),
                      Text('Abnormal Values Detected', style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
                    ],
                  ),
                  SizedBox(height: 8),
                  Text('Some parameters are outside the normal reference range.', style: TextStyle(fontSize: 13)),
                  SizedBox(height: 8),
                  Text('Consult your doctor about these findings.', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                ],
              ),
            ),
            
          // Summary Section
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                isProfessionalMode ? 'Clinical Summary' : 'Patient-Friendly Summary',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              if (!isProfessionalMode)
                TextButton.icon(
                  onPressed: () => _showTranslationBottomSheet(context),
                  icon: Icon(Icons.translate, size: 16),
                  label: Text('Translate'),
                ),
            ],
          ),
          SizedBox(height: 8),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.border),
            ),
            child: SelectableText(
              isProfessionalMode 
                ? (report.clinicalSummary ?? 'No clinical summary available.')
                : (report.aiSummary ?? 'No patient-friendly summary available.'),
              style: TextStyle(height: 1.6, fontSize: 15),
            ),
          ),

          SizedBox(height: 24),
          
          Text('Key Findings', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          SizedBox(height: 12),
          
          // Mock Key Findings
          _buildKeyFinding(context, 'Vitamin D is low (12 ng/mL)', 'green'),
          _buildKeyFinding(context, 'LDL Cholesterol is elevated', 'amber'),
          _buildKeyFinding(context, 'Fasting Glucose is high (140 mg/dL)', 'red'),
          SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildKeyFinding(BuildContext context, String text, String severity) {
    Color dotColor = Colors.green;
    if (severity == 'amber') dotColor = Colors.orange;
    if (severity == 'red') dotColor = Colors.red;

    return Theme(
      data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
      child: ExpansionTile(
        tilePadding: EdgeInsets.zero,
        leading: Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(shape: BoxShape.circle, color: dotColor),
        ),
        title: Text(text, style: TextStyle(fontWeight: FontWeight.w500)),
        children: [
          Container(
            padding: EdgeInsets.all(12),
            margin: EdgeInsets.only(bottom: 12, left: 32, right: 16),
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: AppColors.border),
            ),
            child: Text(
              "What does this mean? This finding suggests a need for lifestyle changes or medical review. Please discuss this with your physician.",
              style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7), fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}
