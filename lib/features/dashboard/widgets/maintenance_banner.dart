import 'dart:async';

import 'package:flutter/material.dart';

import '../../../core/services/api_service.dart';

class MaintenanceBanner extends StatefulWidget {
  const MaintenanceBanner({super.key, this.loadStatus});

  final Future<Map<String, dynamic>> Function()? loadStatus;

  @override
  State<MaintenanceBanner> createState() => _MaintenanceBannerState();
}

class _MaintenanceBannerState extends State<MaintenanceBanner> {
  Map<String, dynamic>? _status;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _load();
    _timer = Timer.periodic(const Duration(seconds: 15), (_) => _load());
  }

  Future<void> _load() async {
    try {
      final status = await (widget.loadStatus?.call() ??
          ApiService.instance.getMaintenanceStatus());
      if (mounted) setState(() => _status = status);
    } catch (_) {
      // Keep the last known notice during a temporary network outage.
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_status?['is_enabled'] != true) return const SizedBox.shrink();
    final message = _status?['message'] as String? ??
        'MedNarrate is temporarily under maintenance. Please try again shortly.';
    return Semantics(
      liveRegion: true,
      child: Container(
        width: double.infinity,
        margin: const EdgeInsets.fromLTRB(22, 12, 22, 0),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.errorContainer,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            const Icon(Icons.build_outlined),
            const SizedBox(width: 10),
            Expanded(child: Text(message)),
          ],
        ),
      ),
    );
  }
}
