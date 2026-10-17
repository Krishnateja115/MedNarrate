import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/routing/routes.dart';
import '../../../core/services/storage_service.dart';
import '../../../shared/widgets/primary_button.dart';
import '../widgets/onboarding_page.dart';
import '../widgets/page_indicator.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _controller = PageController();

  int currentPage = 0;

  // Icons are fixed; the words come from the app's translations so they follow
  // the language the user picked.
  static const List<IconData> _pageIcons = [
    Icons.description_rounded,
    Icons.smart_toy_rounded,
    Icons.medication_rounded,
    Icons.insights_rounded,
  ];

  String _pageTitle(AppLocalizations l10n, int index) {
    switch (index) {
      case 0:
        return l10n.onbTitle1;
      case 1:
        return l10n.onbTitle2;
      case 2:
        return l10n.onbTitle3;
      default:
        return l10n.onbTitle4;
    }
  }

  String _pageSubtitle(AppLocalizations l10n, int index) {
    switch (index) {
      case 0:
        return l10n.onbBody1;
      case 1:
        return l10n.onbBody2;
      case 2:
        return l10n.onbBody3;
      default:
        return l10n.onbBody4;
    }
  }

  Future<void> _navigateToSignup() async {
    await StorageService.instance.setOnboardingSeen();
    if (!mounted) return;
    context.go(Routes.signup);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,

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
                    onPressed: _navigateToSignup,
                    child: Text(
                      AppLocalizations.of(context)!.skip,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70),
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

                itemCount: _pageIcons.length,

                onPageChanged: (index) {
                  setState(() {
                    currentPage = index;
                  });
                },

                itemBuilder: (context, index) {
                  final l10n = AppLocalizations.of(context)!;

                  return AnimatedSwitcher(
                    duration: const Duration(milliseconds: 400),
                    child: OnboardingPage(
                      key: ValueKey(index),
                      icon: _pageIcons[index],
                      title: _pageTitle(l10n, index),
                      subtitle: _pageSubtitle(l10n, index),
                      pageIndex: index,
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
                _pageIcons.length,
                (index) => PageIndicator(
                  active: currentPage == index,
                ),
              ),
            ),

            SizedBox(height: 40),

            //-----------------------------------
            // Button
            //-----------------------------------

            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),

              child: PrimaryButton(
                text: currentPage == _pageIcons.length - 1
                    ? AppLocalizations.of(context)!.getStarted
                    : AppLocalizations.of(context)!.continueLabel,

                onPressed: () {
                  if (currentPage < _pageIcons.length - 1) {
                    _controller.nextPage(
                      duration: const Duration(milliseconds: 350),
                      curve: Curves.easeInOut,
                    );
                  } else {
                    _navigateToSignup();
                  }
                },
              ),
            ),

            SizedBox(height: 35),
          ],
        ),
      ),
    );
  }
}