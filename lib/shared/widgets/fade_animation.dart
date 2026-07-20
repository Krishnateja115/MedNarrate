import 'package:flutter/material.dart';

class FadeAnimation extends StatefulWidget {

  final Widget child;

  const FadeAnimation({
    super.key,
    required this.child,
  });

  @override
  State<FadeAnimation> createState() =>
      _FadeAnimationState();
}

class _FadeAnimationState
    extends State<FadeAnimation>
    with SingleTickerProviderStateMixin {

  late AnimationController controller;

  @override
  void initState() {
    super.initState();

    controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 700),
    );

    controller.forward();
  }

  @override
  Widget build(BuildContext context) {

    return FadeTransition(
      opacity: controller,
      child: widget.child,
    );
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }
}