import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../shared/widgets/primary_button.dart';
import '../widgets/onboarding_page.dart';
import '../widgets/page_indicator.dart';
import 'signup_screen.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _controller = PageController();

  int currentPage = 0;

  final List<Map<String, dynamic>> pages = [
    {
      "icon": Icons.description_rounded,
      "title": "Understand\nMedical Reports",
      "subtitle":
          "Upload any medical report and let AI explain every medical term in simple language."
    },
    {
      "icon": Icons.smart_toy_rounded,
      "title": "AI Health\nAssistant",
      "subtitle":
          "Ask questions about your uploaded reports and receive clear, easy-to-understand explanations."
    },
    {
      "icon": Icons.medication_rounded,
      "title": "Medicine\nReminders",
      "subtitle":
          "Never miss your medicines. Receive intelligent reminders based on your prescriptions."
    },
    {
      "icon": Icons.insights_rounded,
      "title": "Track Your\nHealth",
      "subtitle":
          "Monitor health trends, compare reports and understand your progress over time."
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,

      body: SafeArea(
        child: Column(
          children: [

            //-----------------------------------
            // Skip Button
            //-----------------------------------

            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: 20,
                vertical: 10,
              ),

              child: Row(
                mainAxisAlignment: MainAxisAlignment.end,

                children: [

                  TextButton(
                    onPressed: () {
                      Navigator.pushReplacement(
                        context,
                        MaterialPageRoute(
                          builder: (_) => const SignupScreen(),
                        ),
                      );
                    },
                    child: const Text(
                      "Skip",
                      style: TextStyle(
                        color: Colors.white70,
                        fontSize: 16,
                      ),
                    ),
                  ),

                ],
              ),
            ),

            //-----------------------------------

            Expanded(
              child: PageView.builder(
                controller: _controller,

                itemCount: pages.length,

                onPageChanged: (index) {
                  setState(() {
                    currentPage = index;
                  });
                },

                itemBuilder: (context, index) {
                  final page = pages[index];

                  return AnimatedSwitcher(
                    duration: const Duration(milliseconds: 400),

                    child: OnboardingPage(
                      key: ValueKey(index),
                      icon: page["icon"],
                      title: page["title"],
                      subtitle: page["subtitle"],
                    ),
                  );
                },
              ),
            ),

            //-----------------------------------
            // Indicators
            //-----------------------------------

            Row(
              mainAxisAlignment: MainAxisAlignment.center,

              children: List.generate(
                pages.length,
                (index) => PageIndicator(
                  active: currentPage == index,
                ),
              ),
            ),

            const SizedBox(height: 40),

            //-----------------------------------
            // Button
            //-----------------------------------

            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),

              child: PrimaryButton(
                text: currentPage == pages.length - 1
                    ? "Get Started"
                    : "Continue",

                onPressed: () {
                  if (currentPage < pages.length - 1) {
                    _controller.nextPage(
                      duration: const Duration(milliseconds: 350),
                      curve: Curves.easeInOut,
                    );
                  } else {
                    Navigator.pushReplacement(
                      context,
                      MaterialPageRoute(
                        builder: (_) => const SignupScreen(),
                      ),
                    );
                  }
                },
              ),
            ),

            const SizedBox(height: 35),
          ],
        ),
      ),
    );
  }
}