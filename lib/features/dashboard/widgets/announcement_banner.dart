import 'dart:async';
import 'package:flutter/material.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/storage_service.dart';

class AnnouncementBanner extends StatefulWidget {
  final String role; // to fetch role-specific announcements
  final Future<List<Map<String, dynamic>>> Function(String audience, String language)? loadAnnouncements;
  const AnnouncementBanner({super.key, required this.role, this.loadAnnouncements});

  @override
  State<AnnouncementBanner> createState() => _AnnouncementBannerState();
}

class _AnnouncementBannerState extends State<AnnouncementBanner> {
  Map<String, dynamic>? _activeAnnouncement;
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    _loadAnnouncement();
    _refreshTimer = Timer.periodic(const Duration(seconds: 30), (_) => _loadAnnouncement());
  }

  @override
  void didUpdateWidget(covariant AnnouncementBanner oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.role != widget.role) _loadAnnouncement();
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadAnnouncement() async {
    try {
      final language = await StorageService.instance.getPreferredLanguage();
      final audience = widget.role == 'clinician' ? 'doctors' : (widget.role == 'caregiver' ? 'caregivers' : 'patients');
      
      final announcements = await (widget.loadAnnouncements?.call(audience, language) ??
          ApiService.instance.getAnnouncements(audience: audience, language: language));

      Map<String, dynamic>? next;
      for (var ann in announcements) {
        final id = ann['id'] as String;
        final dismissed = await StorageService.instance.isAnnouncementDismissed(id);
        if (!dismissed) {
          next = ann;
          break;
        }
      }
      if (mounted) setState(() => _activeAnnouncement = next);
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
      _loadAnnouncement();
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
