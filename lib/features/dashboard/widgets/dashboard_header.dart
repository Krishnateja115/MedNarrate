import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/services/storage_service.dart';
import '../../../main.dart';

class DashboardHeader extends StatefulWidget {
  final String name;

  const DashboardHeader({
    super.key,
    required this.name,
  });

  @override
  State<DashboardHeader> createState() => _DashboardHeaderState();
}

class _DashboardHeaderState extends State<DashboardHeader> {
  bool _notificationsEnabled = true;

  @override
  void initState() {
    super.initState();
    _loadNotificationState();
  }

  Future<void> _loadNotificationState() async {
    final enabled = await StorageService.instance.getNotificationsEnabled();
    if (mounted) setState(() => _notificationsEnabled = enabled);
  }

  void _showTopBanner(String message, bool isEnabled) {
    final overlay = Overlay.of(context);
    late OverlayEntry overlayEntry;

    overlayEntry = OverlayEntry(
      builder: (context) => Positioned(
        top: MediaQuery.of(context).padding.top + 16,
        left: 24,
        right: 24,
        child: Material(
          color: Colors.transparent,
          child: TweenAnimationBuilder<double>(
            tween: Tween(begin: 0.0, end: 1.0),
            duration: Duration(milliseconds: 250),
            curve: Curves.easeOutCubic,
            builder: (context, val, child) {
              return Transform.translate(
                offset: Offset(0, (1 - val) * -20),
                child: Opacity(
                  opacity: val,
                  child: child,
                ),
              );
            },
            child: Container(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: BoxDecoration(
                color: Theme.of(context).cardColor,
                borderRadius: BorderRadius.circular(30),
                border: Border.all(
                  color: isEnabled ? Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.38) : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.12),
                  width: 1,
                ),
                boxShadow: [
                  BoxShadow(
                    color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.10),
                    blurRadius: 10,
                    offset: Offset(0, 4),
                  ),
                ],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    isEnabled ? Icons.notifications_active_rounded : Icons.notifications_off_outlined,
                    color: isEnabled ? Theme.of(context).colorScheme.onSurface : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54),
                    size: 17,
                  ),
                  SizedBox(width: 8),
                  Text(
                    message,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.onSurface,
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 0.2,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );

    overlay.insert(overlayEntry);
    Future.delayed(Duration(milliseconds: 1000), () {
      overlayEntry.remove();
    });
  }

  Future<void> _toggleNotifications() async {
    final newState = !_notificationsEnabled;
    await StorageService.instance.setNotificationsEnabled(newState);
    if (mounted) setState(() => _notificationsEnabled = newState);
    _showTopBanner(
      newState ? "Notifications enabled" : "Notifications disabled",
      newState,
    );
  }

  Future<void> _toggleTheme() async {
    final current = themeModeNotifier.value;
    final next = current == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    await StorageService.instance.setThemeMode(next);
    themeModeNotifier.value = next;
    _showTopBanner(
      next == ThemeMode.dark ? "Dark mode enabled" : "Light mode enabled",
      true,
    );
  }

  String get _greeting {
    final hour = DateTime.now().hour;
    if (hour < 12) return "Good Morning ☀️";
    if (hour < 17) return "Good Afternoon 🌤️";
    return "Good Evening 🌙";
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                _greeting,
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 15,
                  fontWeight: FontWeight.w500,
                ),
              ),
              SizedBox(height: 4),
              Text(
                widget.name,
                style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurface,
                  fontSize: 30,
                  fontWeight: FontWeight.bold,
                  letterSpacing: -0.5,
                ),
              ),
            ],
          ),
        ),

        // Quick Theme Toggle
        ValueListenableBuilder<ThemeMode>(
          valueListenable: themeModeNotifier,
          builder: (context, mode, _) {
            final isDark = mode == ThemeMode.dark || mode == ThemeMode.system;
            return Container(
              margin: EdgeInsets.only(right: 8),
              decoration: BoxDecoration(
                color: Theme.of(context).cardColor,
                shape: BoxShape.circle,
                border: Border.all(color: AppColors.border, width: 1),
              ),
              child: IconButton(
                icon: Icon(
                  isDark ? Icons.light_mode_outlined : Icons.dark_mode_outlined,
                  color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70),
                  size: 20,
                ),
                onPressed: _toggleTheme,
                tooltip: isDark ? "Switch to Light Mode" : "Switch to Dark Mode",
              ),
            );
          },
        ),

        // Notification Toggle Bell
        Container(
          decoration: BoxDecoration(
            color: _notificationsEnabled
                ? Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.12)
                : Theme.of(context).cardColor,
            shape: BoxShape.circle,
            border: Border.all(
              color: _notificationsEnabled
                  ? Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54)
                  : AppColors.border,
              width: 1,
            ),
          ),
          child: IconButton(
            icon: Icon(
              _notificationsEnabled
                  ? Icons.notifications_active_rounded
                  : Icons.notifications_off_outlined,
              color: _notificationsEnabled ? Theme.of(context).colorScheme.onSurface : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.38),
              size: 20,
            ),
            onPressed: _toggleNotifications,
            tooltip: _notificationsEnabled ? "Disable Notifications" : "Enable Notifications",
          ),
        ),
      ],
    );
  }
}