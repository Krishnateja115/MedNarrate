import 'dart:ui';
import 'package:flutter/material.dart';

import '../../dashboard/screens/dashboard_screen.dart';
import '../../reports/screens/reports_screen.dart';
import '../../profile/screens/profile_screen.dart';

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _selectedIndex = 0;

  @override
  Widget build(BuildContext context) {
    final List<Widget> screens = [
      const DashboardScreen(),
      const ReportsScreen(),
      const ProfileScreen(),
    ];

    return Scaffold(
      extendBody: true, // Required for the body to flow under the transparent nav bar
      body: IndexedStack(
        index: _selectedIndex,
        children: screens,
      ),
      bottomNavigationBar: ClipRRect(
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
          child: Container(
            decoration: BoxDecoration(
              color: Colors.black.withValues(alpha: 0.6),
              border: const Border(
                top: BorderSide(color: Colors.white12, width: 0.5),
              ),
            ),
            child: BottomNavigationBar(
              elevation: 0,
              backgroundColor: Colors.transparent,
              selectedItemColor: Colors.white,
              unselectedItemColor: Colors.white38,
              showSelectedLabels: true,
              showUnselectedLabels: false,
              currentIndex: _selectedIndex,
              onTap: (index) {
                setState(() {
                  _selectedIndex = index;
                });
              },
              items: const [
                BottomNavigationBarItem(
                  icon: Icon(Icons.dashboard_outlined),
                  activeIcon: Icon(Icons.dashboard_rounded),
                  label: "Dashboard",
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.article_outlined),
                  activeIcon: Icon(Icons.article_rounded),
                  label: "Journal",
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.person_outline),
                  activeIcon: Icon(Icons.person_rounded),
                  label: "Profile",
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}