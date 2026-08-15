import 'package:flutter/material.dart';

/// Medical-themed SVG illustrations rendered as Flutter widgets.
/// These use CustomPainter so no external asset files are needed.

class OnboardingIllustration1 extends StatelessWidget {
  const OnboardingIllustration1({super.key});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 280,
      height: 220,
      child: CustomPaint(painter: _Illustration1Painter()),
    );
  }
}

class _Illustration1Painter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..style = PaintingStyle.fill;

    // Background circle
    paint.color = Color(0xFFE8F0FF);
    canvas.drawCircle(Offset(size.width / 2, size.height / 2), 100, paint);

    // Document shape
    paint.color = Color(0xFF0F172A);
    final docRect = RRect.fromRectAndRadius(
      Rect.fromCenter(center: Offset(size.width / 2, size.height / 2 + 5), width: 100, height: 130),
      const Radius.circular(10),
    );
    canvas.drawRRect(docRect, paint);
    paint.color = Color(0xFF1A6BFF).withValues(alpha: 0.15);
    canvas.drawRRect(docRect, paint);

    // Lines on document
    final linePaint = Paint()
      ..color = Color(0xFF1A6BFF).withValues(alpha: 0.4)
      ..strokeWidth = 2.5
      ..strokeCap = StrokeCap.round;

    for (int i = 0; i < 5; i++) {
      final y = size.height / 2 - 35.0 + i * 18.0;
      final xEnd = i == 2 ? size.width / 2 + 25 : size.width / 2 + 38;
      canvas.drawLine(Offset(size.width / 2 - 38, y), Offset(xEnd, y), linePaint);
    }

    // Medical cross
    paint.color = Color(0xFF1A6BFF);
    canvas.drawRect(
      Rect.fromCenter(center: Offset(size.width / 2 + 42, size.height / 2 - 55), width: 6, height: 22),
      paint,
    );
    canvas.drawRect(
      Rect.fromCenter(center: Offset(size.width / 2 + 42, size.height / 2 - 55), width: 22, height: 6),
      paint,
    );

    // Magnifying glass
    final glassPaint = Paint()
      ..color = Color(0xFF00C48C)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 4;
    canvas.drawCircle(Offset(size.width / 2 + 50, size.height / 2 + 45), 18, glassPaint);
    canvas.drawLine(
      Offset(size.width / 2 + 63, size.height / 2 + 58),
      Offset(size.width / 2 + 72, size.height / 2 + 68),
      glassPaint,
    );
  }

  @override
  bool shouldRepaint(_) => false;
}

// ─────────────────────────────────────────────────────────────────────────────

class OnboardingIllustration2 extends StatelessWidget {
  const OnboardingIllustration2({super.key});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 280,
      height: 220,
      child: CustomPaint(painter: _Illustration2Painter()),
    );
  }
}

class _Illustration2Painter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..style = PaintingStyle.fill;
    final cx = size.width / 2;
    final cy = size.height / 2;

    // Background
    paint.color = Color(0xFFE8F0FF);
    canvas.drawCircle(Offset(cx, cy), 100, paint);

    // Bar chart bars
    final barColors = [
      Color(0xFF1A6BFF),
      Color(0xFF00C48C),
      Color(0xFFF5A623),
      Color(0xFF1A6BFF),
    ];
    final barHeights = [60.0, 90.0, 45.0, 75.0];
    final barWidth = 20.0;
    final startX = cx - 50.0;

    for (int i = 0; i < 4; i++) {
      paint.color = barColors[i];
      final x = startX + i * (barWidth + 8);
      final barRect = Rect.fromLTWH(x, cy + 30 - barHeights[i], barWidth, barHeights[i]);
      canvas.drawRRect(RRect.fromRectAndRadius(barRect, const Radius.circular(4)), paint);
    }

    // Highlight badge
    paint.color = Color(0xFF0F172A);
    final badge = RRect.fromRectAndRadius(
      Rect.fromCenter(center: Offset(cx + 55, cy - 55), width: 80, height: 36),
      const Radius.circular(12),
    );
    canvas.drawRRect(badge, paint);
    final textPaint = Paint()..color = Color(0xFF00C48C);
    // Draw check circle
    canvas.drawCircle(Offset(cx + 22, cy - 55), 10, textPaint);

    // Warning dot
    paint.color = Color(0xFFE53935);
    canvas.drawCircle(Offset(cx - 65, cy - 60), 10, paint);
    paint.color = Color(0xFF0F172A);
    canvas.drawRect(Rect.fromCenter(center: Offset(cx - 65, cy - 60), width: 10, height: 2), paint);
    canvas.drawRect(Rect.fromCenter(center: Offset(cx - 65, cy - 54), width: 3, height: 3), paint);
  }

  @override
  bool shouldRepaint(_) => false;
}

// ─────────────────────────────────────────────────────────────────────────────

class OnboardingIllustration3 extends StatelessWidget {
  const OnboardingIllustration3({super.key});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 280,
      height: 220,
      child: CustomPaint(painter: _Illustration3Painter()),
    );
  }
}

class _Illustration3Painter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..style = PaintingStyle.fill;
    final cx = size.width / 2;
    final cy = size.height / 2;

    // Background
    paint.color = Color(0xFFE8F0FF);
    canvas.drawCircle(Offset(cx, cy), 100, paint);

    // Three person circles
    final positions = [
      Offset(cx - 55, cy + 20),
      Offset(cx, cy - 10),
      Offset(cx + 55, cy + 20),
    ];
    final colors = [
      Color(0xFF00C48C),
      Color(0xFF1A6BFF),
      Color(0xFFF5A623),
    ];
    final sizes = [32.0, 40.0, 32.0];

    for (int i = 0; i < 3; i++) {
      paint.color = colors[i].withValues(alpha: 0.2);
      canvas.drawCircle(positions[i], sizes[i], paint);
      paint.color = colors[i];
      canvas.drawCircle(positions[i] - Offset(0, 8), sizes[i] * 0.35, paint);
      paint.color = colors[i].withValues(alpha: 0.7);
      final bodyRect = Rect.fromCenter(
        center: positions[i] + const Offset(0, 10),
        width: sizes[i] * 0.9,
        height: sizes[i] * 0.6,
      );
      canvas.drawArc(bodyRect, 0, 3.14159, true, paint);
    }

    // Heart in center-top
    paint.color = Color(0xFFE53935);
    final heartPath = Path();
    final hx = cx;
    final hy = cy - 65.0;
    heartPath.moveTo(hx, hy + 12);
    heartPath.cubicTo(hx, hy + 5, hx - 10, hy - 3, hx - 10, hy + 4);
    heartPath.cubicTo(hx - 10, hy + 10, hx, hy + 18, hx, hy + 18);
    heartPath.cubicTo(hx, hy + 18, hx + 10, hy + 10, hx + 10, hy + 4);
    heartPath.cubicTo(hx + 10, hy - 3, hx, hy + 5, hx, hy + 12);
    canvas.drawPath(heartPath, paint);
  }

  @override
  bool shouldRepaint(_) => false;
}

/// Empty state illustration for history and home screens
class EmptyHistoryIllustration extends StatelessWidget {
  const EmptyHistoryIllustration({super.key});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 200,
      height: 160,
      child: CustomPaint(painter: _EmptyHistoryPainter()),
    );
  }
}

class _EmptyHistoryPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..style = PaintingStyle.fill;
    final cx = size.width / 2;
    final cy = size.height / 2;

    paint.color = Color(0xFFE8F0FF);
    canvas.drawCircle(Offset(cx, cy), 75, paint);

    // Folder shape
    paint.color = Color(0xFF1A6BFF).withValues(alpha: 0.3);
    final folder = RRect.fromRectAndRadius(
      Rect.fromCenter(center: Offset(cx, cy + 10), width: 90, height: 65),
      const Radius.circular(8),
    );
    canvas.drawRRect(folder, paint);

    paint.color = Color(0xFF1A6BFF).withValues(alpha: 0.15);
    final tab = RRect.fromRectAndRadius(
      Rect.fromLTWH(cx - 45, cy - 22, 35, 12),
      const Radius.circular(4),
    );
    canvas.drawRRect(tab, paint);

    // Question mark
    final textPaint = TextPainter(
      text: const TextSpan(
        text: '?',
        style: TextStyle(
          color: Color(0xFF1A6BFF),
          fontSize: 36,
          fontWeight: FontWeight.bold,
        ),
      ),
      textDirection: TextDirection.ltr,
    );
    textPaint.layout();
    textPaint.paint(canvas, Offset(cx - textPaint.width / 2, cy - 8));
  }

  @override
  bool shouldRepaint(_) => false;
}
