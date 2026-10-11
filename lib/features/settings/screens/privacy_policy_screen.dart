import 'package:flutter/material.dart';

class PrivacyPolicyScreen extends StatelessWidget {
  const PrivacyPolicyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Privacy Policy'),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Privacy Policy',
              style: TextStyle(
                color: theme.colorScheme.onSurface,
                fontSize: 26,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              'Last updated: September 8, 2026',
              style: TextStyle(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                fontSize: 13.5,
              ),
            ),
            const SizedBox(height: 24),

            _buildSection(
              theme,
              title: '1. Overview & Data Transparency',
              content:
                  'MedNarrate respects your health privacy. This Privacy Policy describes how we collect, store, process, and protect your personal and medical information when using the MedNarrate application.',
            ),

            _buildSection(
              theme,
              title: '2. Information We Collect',
              content:
                  'We collect only information necessary to deliver medical report analysis:\n'
                  '• Account Credentials: Email address and hashed password for user authentication.\n'
                  '• Medical Documents: PDF and image files uploaded for lab extraction.\n'
                  '• Medical Profile Inputs: Blood group, allergies, chronic conditions, and emergency contact details entered voluntarily.\n'
                  '• Medication Schedules: Reminder times and medicine names configured by you.',
            ),

            _buildSection(
              theme,
              title: '3. Biometric Authentication Privacy',
              content:
                  'Biometric authentication (fingerprint / face unlock) is performed locally by your device operating system via standard OS security frameworks (LocalAuthentication). MedNarrate NEVER stores, receives, or transmits your fingerprint, face scan, or raw biometric templates.',
            ),

            _buildSection(
              theme,
              title: '4. Data Storage & Local Caching',
              content:
                  'Your account data is stored securely in our PostgreSQL database using encrypted connections. Report text and offline preferences are cached locally on your device using Hive database storage.',
            ),

            _buildSection(
              theme,
              title: '5. AI & Report Processing',
              content:
                  'Uploaded documents are processed by the MedNarrate backend. Text needed for analysis, chat, and translation may be sent to configured third-party AI providers. We do not sell your medical documents. AI outputs can be wrong, so compare important findings with your original report and a qualified clinician.',
            ),

            _buildSection(
              theme,
              title: '6. Third-Party Services',
              content:
                  'MedNarrate may use a hosting and database provider, a file-storage provider, configured AI providers for report analysis or translation, and an error-monitoring provider if enabled. The final public policy must name the production providers and describe their retention terms before release.',
            ),

            _buildSection(
              theme,
              title: '7. Data Retention & Deletion',
              content:
                  'You can delete uploaded reports, save an account-data archive, or delete your account from Settings. The archive contains sensitive medical information, so store it securely. Account deletion removes uploaded files and personal medical data; limited non-identifying operational records may remain where necessary.',
            ),

            _buildSection(
              theme,
              title: '8. Security Measures',
              content:
                  'We employ industry-standard security protocols including JWT access tokens with automatic rotation, bcrypt password hashing, HTTP security headers, and rate-limiting to prevent unauthorized access.',
            ),

            _buildSection(
              theme,
              title: '9. Changes to Privacy Policy',
              content:
                  'We may update this Privacy Policy periodically. Notice of material changes will be posted within the application.',
            ),

            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }

  Widget _buildSection(ThemeData theme, {required String title, required String content}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 22),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: TextStyle(
              color: theme.colorScheme.onSurface,
              fontSize: 17,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            content,
            style: TextStyle(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.75),
              fontSize: 14,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }
}
