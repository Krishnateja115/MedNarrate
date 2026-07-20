import 'package:flutter/material.dart';

import '../upload/upload_screen.dart';
import '../reports/reports_screen.dart';
import '../insights/insights_screen.dart';
import '../profile/profile_screen.dart';

import '../../widgets/upload_card.dart';
import '../../widgets/report_card.dart';
import '../../widgets/snapshot_card.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int currentIndex = 0;

  final List<Widget> pages = const [
    HomeBody(),
    ReportsScreen(),
    UploadScreen(),
    InsightsScreen(),
    ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF151B2F),

      body: pages[currentIndex],

      bottomNavigationBar: NavigationBar(
        backgroundColor: const Color(0xFF252C42),
        indicatorColor: const Color(0xFF4F6BFF),
        selectedIndex: currentIndex,

        onDestinationSelected: (index) {
          setState(() {
            currentIndex = index;
          });
        },

        destinations: const [

          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home),
            label: "Home",
          ),

          NavigationDestination(
            icon: Icon(Icons.description_outlined),
            selectedIcon: Icon(Icons.description),
            label: "Reports",
          ),

          NavigationDestination(
            icon: Icon(Icons.add_circle_outline),
            selectedIcon: Icon(Icons.add_circle),
            label: "Upload",
          ),

          NavigationDestination(
            icon: Icon(Icons.bar_chart_outlined),
            selectedIcon: Icon(Icons.bar_chart),
            label: "Insights",
          ),

          NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person),
            label: "Profile",
          ),
        ],
      ),
    );
  }
}

class HomeBody extends StatelessWidget {
  const HomeBody({super.key});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(20),

        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,

          children: [

            Row(
              children: [

                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [

                      Text(
                        "Good Evening,",
                        style: TextStyle(
                          color: Colors.white70,
                          fontSize: 16,
                        ),
                      ),

                      SizedBox(height: 4),

                      Text(
                        "Krishna",
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 32,
                          fontWeight: FontWeight.bold,
                        ),
                      ),

                    ],
                  ),
                ),

                CircleAvatar(
                  radius: 24,
                  backgroundColor: const Color(0xFF252C42),

                  child: IconButton(
                    onPressed: () {},
                    icon: const Icon(
                      Icons.notifications_none,
                      color: Colors.white,
                    ),
                  ),
                ),

              ],
            ),

            const SizedBox(height: 30),

            InkWell(
              borderRadius: BorderRadius.circular(24),
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => const UploadScreen(),
                  ),
                );
              },
              child: const UploadCard(),
            ),

            const SizedBox(height: 35),

            const Text(
              "Quick Health Snapshot",
              style: TextStyle(
                color: Colors.white,
                fontSize: 22,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 20),

            const Row(
              children: [

                SnapshotCard(
                  number: "3",
                  title: "Uploaded",
                  circleColor: Colors.blue,
                ),

                SnapshotCard(
                  number: "0",
                  title: "Normal",
                  circleColor: Colors.green,
                ),

                SnapshotCard(
                  number: "0",
                  title: "Attention",
                  circleColor: Colors.orange,
                ),

              ],
            ),

            const SizedBox(height: 35),

            const Text(
              "Recent Reports",
              style: TextStyle(
                color: Colors.white,
                fontSize: 22,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 20),

            const ReportCard(
              title: "Blood Test",
              hospital: "Apollo Diagnostic Centre",
              date: "15 Jul 2026",
            ),

            const ReportCard(
              title: "Lipid Panel",
              hospital: "City Health Labs",
              date: "10 Jul 2026",
            ),

            const ReportCard(
              title: "HbA1c Report",
              hospital: "MedPlus Diagnostics",
              date: "04 Jul 2026",
            ),

            const SizedBox(height: 20),

          ],
        ),
      ),
    );
  }
}