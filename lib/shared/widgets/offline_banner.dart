import 'package:flutter/material.dart';
import '../../core/services/connectivity_service.dart';

class OfflineBanner extends StatefulWidget {
  const OfflineBanner({super.key});

  @override
  State<OfflineBanner> createState() => _OfflineBannerState();
}

class _OfflineBannerState extends State<OfflineBanner> with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<Offset> _offsetAnimation;
  bool _wasOffline = false;
  bool _showingReconnected = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _offsetAnimation = Tween<Offset>(
      begin: const Offset(0.0, -1.0),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeInOut,
    ));

    // Initial check
    if (!ConnectivityService.instance.isOnline) {
      _wasOffline = true;
      _controller.forward();
    }

    // Listen to changes
    ConnectivityService.instance.onConnectivityChanged.listen((isOnline) {
      if (!mounted) return;
      
      if (!isOnline) {
        _wasOffline = true;
        setState(() {
          _showingReconnected = false;
        });
        _controller.forward();
      } else if (_wasOffline) {
        _wasOffline = false;
        setState(() {
          _showingReconnected = true;
        });
        
        // Hide after showing reconnected message briefly
        Future.delayed(const Duration(seconds: 2), () {
          if (mounted && ConnectivityService.instance.isOnline) {
            _controller.reverse().then((_) {
              if (mounted) {
                setState(() {
                  _showingReconnected = false;
                });
              }
            });
          }
        });
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SlideTransition(
      position: _offsetAnimation,
      child: Container(
        height: 36,
        width: double.infinity,
        color: _showingReconnected ? Colors.green : Colors.amber.shade900,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              _showingReconnected ? Icons.wifi : Icons.wifi_off,
              color: Colors.white,
              size: 16,
            ),
            const SizedBox(width: 8),
            Text(
              _showingReconnected 
                  ? "Back online! Refreshing..." 
                  : "You're offline. Viewing cached data.",
              style: const TextStyle(
                color: Colors.white,
                fontSize: 13,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
