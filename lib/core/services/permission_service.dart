import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:permission_handler/permission_handler.dart';

/// PermissionService — wraps permission_handler.
/// If permanently denied, shows a rationale dialog and opens app settings.
class PermissionService {
  PermissionService._();
  static final PermissionService instance = PermissionService._();

  Future<bool> requestCamera(BuildContext context) async {
    return _request(context, Permission.camera, 'Camera access is needed to scan documents.');
  }

  Future<bool> requestPhotos(BuildContext context) async {
    // On Android 13+, READ_MEDIA_IMAGES; on older, READ_EXTERNAL_STORAGE
    return _request(context, Permission.photos, 'Photo access is needed to pick medical reports.');
  }

  Future<bool> requestNotifications(BuildContext context) async {
    return _request(context, Permission.notification, 'Notifications are needed for medicine reminders.');
  }

  Future<bool> _request(BuildContext context, Permission perm, String rationale) async {
    var status = await perm.status;
    if (status.isGranted) return true;
    if (status.isPermanentlyDenied) {
      if (!context.mounted) return false;
      await _showRationaleDialog(context, rationale);
      return false;
    }
    status = await perm.request();
    if (status.isPermanentlyDenied) {
      if (!context.mounted) return false;
      await _showRationaleDialog(context, rationale);
      return false;
    }
    return status.isGranted;
  }

  Future<void> _showRationaleDialog(BuildContext context, String rationale) async {
    if (!context.mounted) return;
    await showDialog<void>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Permission Required'),
        content: Text('$rationale\n\nPlease enable it in app settings.'),
        actions: [
          TextButton(onPressed: () => context.pop(), child: const Text('Cancel')),
          TextButton(
            onPressed: () async {
              context.pop();
              await openAppSettings();
            },
            child: const Text('Open Settings'),
          ),
        ],
      ),
    );
  }
}
