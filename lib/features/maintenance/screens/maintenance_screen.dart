import 'package:flutter/material.dart';

import '../../../core/services/maintenance_controller.dart';

class MaintenanceScreen extends StatelessWidget {
  const MaintenanceScreen({super.key, this.controller});

  final MaintenanceController? controller;

  @override
  Widget build(BuildContext context) {
    final maintenance = controller ?? MaintenanceController.instance;
    return ListenableBuilder(
      listenable: maintenance,
      builder: (context, _) {
        final state = maintenance.availability;
        final active = state == MaintenanceAvailability.active;
        final checking = state == MaintenanceAvailability.checking;
        final title = active
            ? 'MedNarrate is under maintenance'
            : checking
                ? 'Checking service status'
                : 'Unable to verify service status';
        final body = active
            ? maintenance.message
            : checking
                ? 'Please wait a moment while we check availability.'
                : 'Check your connection and try again. Your data is safe.';
        return PopScope(
          canPop: false,
          child: Scaffold(
            body: SafeArea(
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 440),
                  child: Padding(
                    padding: const EdgeInsets.all(28),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          active ? Icons.build_circle_outlined : Icons.wifi_find,
                          size: 64,
                          color: Theme.of(context).colorScheme.primary,
                        ),
                        const SizedBox(height: 24),
                        Text(title,
                            textAlign: TextAlign.center,
                            style: Theme.of(context).textTheme.headlineSmall),
                        const SizedBox(height: 12),
                        Text(body, textAlign: TextAlign.center),
                        const SizedBox(height: 22),
                        if (checking)
                          const CircularProgressIndicator()
                        else
                          FilledButton.icon(
                            onPressed: () => maintenance.refresh(),
                            icon: const Icon(Icons.refresh),
                            label: const Text('Check again'),
                          ),
                        const SizedBox(height: 14),
                        Text(
                          'This screen will update automatically when the service is available.',
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
