import 'package:flutter/material.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/storage_service.dart';

class AnnouncementBanner extends StatefulWidget {
  final String role; // to fetch role-specific announcements
  const AnnouncementBanner({super.key, required this.role});

  @override
  State<AnnouncementBanner> createState() => _AnnouncementBannerState();
}

class _AnnouncementBannerState extends State<AnnouncementBanner> {
  Map<String, dynamic>? _activeAnnouncement;

  @override
  void initState() {
    super.initState();
    _loadAnnouncement();
  }

  Future<void> _loadAnnouncement() async {
    try {
      final language = await StorageService.instance.getPreferredLanguage();
      final audience = widget.role == 'clinician' ? 'doctors' : (widget.role == 'caregiver' ? 'caregivers' : 'patients');
      
      final announcements = await ApiService.instance.getAnnouncements(
        audience: audience,
        language: language,
      );

      for (var ann in announcements) {
        final id = ann['id'] as String;
        final dismissed = await StorageService.instance.isAnnouncementDismissed(id);
        if (!dismissed) {
          if (mounted) {
            setState(() {
              _activeAnnouncement = ann;
            });
          }
          break;
        }
      }
    } catch (e) {
      // Fail silently for announcements
    }
  }

  Future<void> _dismiss() async {
    if (_activeAnnouncement != null) {
      final id = _activeAnnouncement!['id'] as String;
      await StorageService.instance.dismissAnnouncement(id);
      setState(() {
        _activeAnnouncement = null;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_activeAnnouncement == null) return const SizedBox.shrink();

    final title = _activeAnnouncement!['title'] as String;
    final message = _activeAnnouncement!['message'] as String;

    return Container(
      margin: const EdgeInsets.fromLTRB(22, 16, 22, 0),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.primaryContainer,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.3),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.campaign, color: Theme.of(context).colorScheme.onPrimaryContainer),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Theme.of(context).colorScheme.onPrimaryContainer,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  message,
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.onPrimaryContainer.withValues(alpha: 0.9),
                  ),
                ),
              ],
            ),
          ),
          IconButton(
            icon: Icon(Icons.close, size: 20, color: Theme.of(context).colorScheme.onPrimaryContainer),
            onPressed: _dismiss,
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(),
          ),
        ],
      ),
    );
  }
}
