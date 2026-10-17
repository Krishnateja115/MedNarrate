import 'package:flutter/material.dart';

import '../../core/constants/app_colors.dart';
import '../../core/l10n/app_l10n.dart';
import 'voice_input_controller.dart';
import 'voice_languages.dart';

Color _accent(BuildContext context) =>
    Theme.of(context).brightness == Brightness.dark
        ? AppColors.darkPrimary
        : AppColors.lightPrimary;

/// The microphone that sits inside the chat box, beside the text.
class VoiceMicButton extends StatelessWidget {
  final VoiceInputController controller;
  final bool enabled;

  const VoiceMicButton({
    super.key,
    required this.controller,
    this.enabled = true,
  });

  @override
  Widget build(BuildContext context) {
    final active = enabled && !controller.isStarting;
    final color = active
        ? _accent(context)
        : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.35);
    return Semantics(
      button: true,
      label: appL10n.voiceInputLabel,
      child: IconButton(
        tooltip: appL10n.voiceSpeakYourMessage,
        visualDensity: VisualDensity.compact,
        constraints: const BoxConstraints(minWidth: 40, minHeight: 40),
        padding: EdgeInsets.zero,
        onPressed: active ? controller.start : null,
        icon: controller.isStarting
            ? SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(strokeWidth: 2, color: color),
              )
            : Icon(Icons.mic_none_rounded, size: 24, color: color),
      ),
    );
  }
}

/// Replaces the text box while recording: ✕ to discard, live level bars with
/// the time and language, ✓ to convert the speech into text.
class VoiceRecordingBar extends StatelessWidget {
  final VoiceInputController controller;
  final VoidCallback onConfirm;

  const VoiceRecordingBar({
    super.key,
    required this.controller,
    required this.onConfirm,
  });

  String _clock(Duration d) {
    final minutes = d.inMinutes;
    final seconds = (d.inSeconds % 60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final dark = theme.brightness == Brightness.dark;
    final accent = _accent(context);
    final fieldColor = dark ? AppColors.dark200 : AppColors.light100;
    final borderColor = dark ? AppColors.dark300 : AppColors.light300;
    final transcribing = controller.isTranscribing;

    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Semantics(
          button: true,
          label: transcribing
              ? appL10n.voiceCancelTranscription
              : appL10n.voiceDiscardRecording,
          child: Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: fieldColor,
              border: Border.all(color: borderColor),
            ),
            child: IconButton(
              tooltip: transcribing ? appL10n.cancel : appL10n.voiceDiscard,
              onPressed: controller.cancel,
              icon: Icon(Icons.close_rounded,
                  size: 22, color: theme.colorScheme.onSurface),
            ),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Container(
            height: 48,
            padding: const EdgeInsets.only(left: 16, right: 6),
            decoration: BoxDecoration(
              color: fieldColor,
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: borderColor),
            ),
            child: transcribing
                ? Row(
                    children: [
                      SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: accent),
                      ),
                      const SizedBox(width: 12),
                      Flexible(
                        child: Text(
                          appL10n.voiceConverting,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 14,
                            color: theme.colorScheme.onSurface
                                .withValues(alpha: 0.75),
                          ),
                        ),
                      ),
                    ],
                  )
                : Row(
                    children: [
                      Text(
                        _clock(controller.elapsed),
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          fontFeatures: const [FontFeature.tabularFigures()],
                          color: theme.colorScheme.onSurface,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: SizedBox(
                          height: 28,
                          child: CustomPaint(
                            painter: _LevelPainter(
                              levels: controller.levels,
                              color: accent,
                            ),
                            size: Size.infinite,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      _LanguageChip(controller: controller),
                    ],
                  ),
          ),
        ),
        const SizedBox(width: 8),
        Semantics(
          button: true,
          label: appL10n.voiceFinishConvert,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 150),
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: transcribing
                  ? (dark ? AppColors.dark300 : AppColors.light200)
                  : AppColors.primary,
            ),
            child: IconButton(
              tooltip: appL10n.done,
              onPressed: transcribing ? null : onConfirm,
              icon: Icon(
                Icons.check_rounded,
                size: 24,
                color: transcribing
                    ? theme.colorScheme.onSurface.withValues(alpha: 0.4)
                    : Colors.white,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _LanguageChip extends StatelessWidget {
  final VoiceInputController controller;

  const _LanguageChip({required this.controller});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final dark = theme.brightness == Brightness.dark;
    final language = voiceLanguageFor(controller.language);
    final canChange = controller.languages.length > 1;
    return Semantics(
      button: canChange,
      label: appL10n.voiceSpokenLanguage(language.name),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: canChange ? () => showVoiceLanguageSheet(context, controller) : null,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            color: dark ? AppColors.darkPrimarySoft : AppColors.primarySoft,
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                language.nativeName,
                style: TextStyle(
                  fontSize: 12.5,
                  fontWeight: FontWeight.w600,
                  color: _accent(context),
                ),
              ),
              if (canChange) ...[
                const SizedBox(width: 2),
                Icon(Icons.arrow_drop_down_rounded,
                    size: 18, color: _accent(context)),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

/// Lets the user pick the language they are about to speak.
Future<void> showVoiceLanguageSheet(
    BuildContext context, VoiceInputController controller) {
  return showModalBottomSheet<void>(
    context: context,
    showDragHandle: true,
    builder: (sheetContext) {
      final theme = Theme.of(sheetContext);
      final options = kVoiceLanguages
          .where((l) => controller.languages.contains(l.code))
          .toList();
      return SafeArea(
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 0, 20, 8),
                child: Text(
                  appL10n.voiceSpeakIn,
                  style: theme.textTheme.titleMedium
                      ?.copyWith(fontWeight: FontWeight.w700),
                ),
              ),
              for (final l in options)
                ListTile(
                  title: Text(l.nativeName),
                  subtitle: l.nativeName == l.name ? null : Text(l.name),
                  trailing: l.code == controller.language
                      ? Icon(Icons.check_rounded, color: _accent(sheetContext))
                      : null,
                  onTap: () {
                    controller.setLanguage(l.code);
                    Navigator.of(sheetContext).pop();
                  },
                ),
              const SizedBox(height: 8),
            ],
          ),
        ),
      );
    },
  );
}

class _LevelPainter extends CustomPainter {
  final List<double> levels;
  final Color color;

  _LevelPainter({required this.levels, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    if (levels.isEmpty || size.width <= 0) return;
    const barWidth = 3.0;
    const gap = 3.0;
    final count = (size.width / (barWidth + gap)).floor().clamp(1, levels.length);
    final shown = levels.sublist(levels.length - count);
    final paint = Paint()
      ..color = color
      ..strokeCap = StrokeCap.round
      ..strokeWidth = barWidth;
    final midY = size.height / 2;
    final startX = size.width - count * (barWidth + gap) + gap / 2 + barWidth / 2;
    for (var i = 0; i < shown.length; i++) {
      final level = shown[i];
      final half = (2 + level * (size.height / 2 - 2)).clamp(2.0, size.height / 2);
      final x = startX + i * (barWidth + gap);
      canvas.drawLine(Offset(x, midY - half), Offset(x, midY + half), paint);
    }
  }

  @override
  bool shouldRepaint(covariant _LevelPainter old) => true;
}
