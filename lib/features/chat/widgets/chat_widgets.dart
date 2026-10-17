import 'dart:math' as math;

import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/l10n/app_l10n.dart';
import '../../../core/services/api_models.dart';
import '../../../core/utils/helpers.dart';
import '../../voice_input/transcript_insert.dart';
import '../../voice_input/voice_input_controller.dart';
import '../../voice_input/voice_input_widgets.dart';
import 'typing_indicator.dart';

/// Shared building blocks for the two chat screens (the full-screen assistant
/// and the report tab), so both look and behave the same.
///
/// Colours follow the app palette: the user's bubble is the brand green with
/// white text in both light and dark mode (the theme's `onSurface` is dark in
/// light mode, which made typed messages unreadable on the green bubble).

bool _isDark(BuildContext context) =>
    Theme.of(context).brightness == Brightness.dark;

/// Brand green used for the user's bubble and the send button.
const Color kChatUserBubble = AppColors.primary;

Color _assistantBubbleColor(BuildContext context) =>
    _isDark(context) ? AppColors.dark200 : AppColors.light100;

Color _assistantBorderColor(BuildContext context) =>
    _isDark(context) ? AppColors.dark300 : AppColors.light200;

/// One chat message. User messages sit on the right in brand green with white
/// text; assistant messages sit on the left in a soft neutral surface.
class ChatBubble extends StatelessWidget {
  final ChatMessageModel message;
  final VoidCallback? onCopy;

  const ChatBubble({super.key, required this.message, this.onCopy});

  bool get _isUser => message.role == 'user';

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final width = MediaQuery.of(context).size.width;
    final maxWidth = math.min(width * 0.82, 560.0);
    final isUser = _isUser;
    final textColor = isUser ? Colors.white : theme.colorScheme.onSurface;
    final mutedColor = theme.colorScheme.onSurface.withValues(alpha: 0.55);
    final time = MaterialLocalizations.of(context).formatTimeOfDay(
      TimeOfDay.fromDateTime(message.createdAt.toLocal()),
    );

    final bubble = Container(
      constraints: BoxConstraints(maxWidth: maxWidth),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      decoration: BoxDecoration(
        color: isUser ? kChatUserBubble : _assistantBubbleColor(context),
        border: isUser
            ? null
            : Border.all(color: _assistantBorderColor(context)),
        borderRadius: BorderRadius.only(
          topLeft: const Radius.circular(18),
          topRight: const Radius.circular(18),
          bottomLeft: Radius.circular(isUser ? 18 : 4),
          bottomRight: Radius.circular(isUser ? 4 : 18),
        ),
      ),
      child: SelectableText(
        message.content,
        style: TextStyle(
          color: textColor,
          fontSize: 15,
          height: 1.5,
          fontWeight: isUser ? FontWeight.w500 : FontWeight.w400,
        ),
      ),
    );

    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment:
            isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          bubble,
          const SizedBox(height: 4),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 6),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(time, style: TextStyle(fontSize: 11, color: mutedColor)),
                if (!isUser && onCopy != null) ...[
                  const SizedBox(width: 6),
                  InkWell(
                    borderRadius: BorderRadius.circular(12),
                    onTap: onCopy,
                    child: Padding(
                      padding: const EdgeInsets.all(4),
                      child: Tooltip(
                        message: MaterialLocalizations.of(context)
                            .copyButtonLabel,
                        child: Icon(Icons.copy_rounded,
                            size: 14, color: mutedColor),
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
          if (!isUser && message.sources.isNotEmpty) ...[
            const SizedBox(height: 6),
            ConstrainedBox(
              constraints: BoxConstraints(maxWidth: maxWidth),
              child: Wrap(
                spacing: 6,
                runSpacing: 6,
                children: message.sources.map((src) {
                  final name = src['source']?.toString() ?? appL10n.chatReference;
                  return Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: AppColors.primary.withValues(alpha: 0.10),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      appL10n.chatSourceLine(name),
                      style: TextStyle(
                        fontSize: 10.5,
                        color: _isDark(context)
                            ? AppColors.darkPrimary
                            : AppColors.lightPrimary,
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// Assistant "typing" bubble.
class ChatTypingBubble extends StatelessWidget {
  const ChatTypingBubble({super.key});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 14),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: _assistantBubbleColor(context),
          border: Border.all(color: _assistantBorderColor(context)),
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(18),
            topRight: Radius.circular(18),
            bottomLeft: Radius.circular(4),
            bottomRight: Radius.circular(18),
          ),
        ),
        child: const TypingIndicator(),
      ),
    );
  }
}

/// Slim, readable medical disclaimer (replaces the full-width amber bar).
class ChatDisclaimer extends StatelessWidget {
  const ChatDisclaimer({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final accent = _isDark(context) ? AppColors.warningDark : AppColors.warning;
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 8, 16, 0),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: accent.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: accent.withValues(alpha: 0.25)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(top: 1),
            child: Icon(Icons.info_outline_rounded, size: 16, color: accent),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              appL10n.chatDisclaimer,
              style: TextStyle(
                fontSize: 12,
                height: 1.35,
                color: theme.colorScheme.onSurface.withValues(alpha: 0.75),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Empty state with tappable starter questions.
class ChatEmptyState extends StatelessWidget {
  final List<String> suggestions;
  final ValueChanged<String> onSelect;

  /// True for the general assistant (no report open): different wording.
  final bool general;

  const ChatEmptyState(
      {super.key,
      required this.suggestions,
      required this.onSelect,
      this.general = false});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final dark = _isDark(context);
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 440),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  color: dark ? AppColors.darkPrimarySoft : AppColors.primarySoft,
                  shape: BoxShape.circle,
                ),
                child: Icon(Icons.auto_awesome_rounded,
                    size: 28,
                    color:
                        dark ? AppColors.darkPrimary : AppColors.lightPrimary),
              ),
              const SizedBox(height: 16),
              Text(general ? appL10n.chatAskHealthTitle : appL10n.chatAskAboutReport,
                  textAlign: TextAlign.center,
                  style: theme.textTheme.titleMedium
                      ?.copyWith(fontWeight: FontWeight.w700)),
              const SizedBox(height: 6),
              Text(
                general ? appL10n.chatAskHealthBody : appL10n.chatEmptyBody,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 14,
                  height: 1.4,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.65),
                ),
              ),
              const SizedBox(height: 20),
              Wrap(
                alignment: WrapAlignment.center,
                spacing: 8,
                runSpacing: 8,
                children: suggestions
                    .map((q) => ActionChip(
                          label: Text(q,
                              style: TextStyle(
                                fontSize: 13,
                                color: dark
                                    ? AppColors.darkPrimary
                                    : AppColors.lightPrimary,
                              )),
                          backgroundColor: AppColors.primary
                              .withValues(alpha: dark ? 0.16 : 0.08),
                          side: BorderSide(
                              color: AppColors.primary.withValues(alpha: 0.25)),
                          shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(20)),
                          onPressed: () => onSelect(q),
                        ))
                    .toList(),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Message box + send button. Enter sends, Shift+Enter inserts a new line.
class ChatComposer extends StatefulWidget {
  final TextEditingController controller;
  final bool sending;
  final VoidCallback onSend;
  final String? hint;

  /// Shows a microphone inside the box when the server offers voice input.
  /// With it off (or the server's feature switched off) the box is the plain
  /// text field it always was.
  final bool enableVoice;

  const ChatComposer({
    super.key,
    required this.controller,
    required this.sending,
    required this.onSend,
    this.hint,
    this.enableVoice = true,
  });

  @override
  State<ChatComposer> createState() => _ChatComposerState();
}

class _ChatComposerState extends State<ChatComposer>
    with WidgetsBindingObserver {
  static const int _maxLength = 500;

  VoiceInputController? _voice;
  bool _voiceStarted = false;

  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_onChanged);
    if (widget.enableVoice && !kIsWeb) {
      WidgetsBinding.instance.addObserver(this);
      _voice = VoiceInputController()
        ..addListener(_onVoiceChanged)
        ..onTimeLimit = () => _finishVoice();
    }
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final voice = _voice;
    if (voice != null && !_voiceStarted) {
      _voiceStarted = true;
      final appLanguage = Localizations.localeOf(context).languageCode;
      voice.init(defaultLanguage: appLanguage);
    }
  }

  @override
  void didUpdateWidget(covariant ChatComposer oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.controller != widget.controller) {
      oldWidget.controller.removeListener(_onChanged);
      widget.controller.addListener(_onChanged);
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // Never keep the microphone open once the app is out of sight.
    if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.hidden) {
      final voice = _voice;
      if (voice != null && voice.isRecording) voice.cancel();
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    widget.controller.removeListener(_onChanged);
    _voice?.removeListener(_onVoiceChanged);
    _voice?.dispose();
    super.dispose();
  }

  void _onChanged() {
    if (mounted) setState(() {});
  }

  void _onVoiceChanged() {
    if (!mounted) return;
    final message = _voice?.takeError();
    setState(() {});
    if (message != null) Helpers.showError(context, message);
  }

  Future<void> _finishVoice() async {
    final voice = _voice;
    if (voice == null) return;
    final text = await voice.finish();
    if (!mounted || text == null || text.isEmpty) return;
    final outcome =
        insertTranscript(widget.controller, text, maxLength: _maxLength);
    if (outcome.truncated) {
      Helpers.showError(context, appL10n.chatMessageShortened(_maxLength));
    }
  }

  bool get _canSend =>
      !widget.sending && widget.controller.text.trim().isNotEmpty;

  KeyEventResult _onKey(FocusNode node, KeyEvent event) {
    if (event is KeyDownEvent &&
        (event.logicalKey == LogicalKeyboardKey.enter ||
            event.logicalKey == LogicalKeyboardKey.numpadEnter) &&
        !HardwareKeyboard.instance.isShiftPressed) {
      // Do not steal Enter while an input method is composing text.
      final composing = widget.controller.value.composing;
      if (composing.isValid && !composing.isCollapsed) {
        return KeyEventResult.ignored;
      }
      if (_canSend) widget.onSend();
      return KeyEventResult.handled;
    }
    return KeyEventResult.ignored;
  }

  Widget _buildTextRow(BuildContext context) {
    final theme = Theme.of(context);
    final dark = _isDark(context);
    final fieldColor = dark ? AppColors.dark200 : AppColors.light100;
    final borderColor = dark ? AppColors.dark300 : AppColors.light300;
    final canSend = _canSend;
    final voice = _voice;

    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Expanded(
          child: Container(
            padding: EdgeInsets.only(
                left: 16, right: voice != null && voice.available ? 4 : 16),
            decoration: BoxDecoration(
              color: fieldColor,
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: borderColor),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Expanded(
                  child: Focus(
                    onKeyEvent: _onKey,
                    child: TextField(
                      controller: widget.controller,
                      minLines: 1,
                      maxLines: 5,
                      maxLength: _maxLength,
                      keyboardType: TextInputType.multiline,
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) {
                        if (_canSend) widget.onSend();
                      },
                      style: TextStyle(
                          fontSize: 15, color: theme.colorScheme.onSurface),
                      decoration: InputDecoration(
                        hintText: widget.hint ?? appL10n.chatHintAsk,
                        hintStyle: TextStyle(
                          fontSize: 15,
                          color: theme.colorScheme.onSurface
                              .withValues(alpha: 0.5),
                        ),
                        isDense: true,
                        filled: false,
                        counterText: '',
                        contentPadding:
                            const EdgeInsets.symmetric(vertical: 13),
                        // The app theme draws its own border for every state;
                        // only the rounded container above should show.
                        border: InputBorder.none,
                        enabledBorder: InputBorder.none,
                        focusedBorder: InputBorder.none,
                        disabledBorder: InputBorder.none,
                        errorBorder: InputBorder.none,
                        focusedErrorBorder: InputBorder.none,
                      ),
                    ),
                  ),
                ),
                if (voice != null && voice.available)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 3),
                    child: VoiceMicButton(
                      controller: voice,
                      enabled: !widget.sending,
                    ),
                  ),
              ],
            ),
          ),
        ),
        const SizedBox(width: 8),
        AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          width: 46,
          height: 46,
          decoration: BoxDecoration(
            color: canSend
                ? kChatUserBubble
                : (dark ? AppColors.dark300 : AppColors.light200),
            shape: BoxShape.circle,
          ),
          child: IconButton(
            onPressed: canSend ? widget.onSend : null,
            icon: Icon(
              Icons.arrow_upward_rounded,
              color: canSend
                  ? Colors.white
                  : theme.colorScheme.onSurface.withValues(alpha: 0.4),
            ),
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final voice = _voice;

    return Container(
      decoration: BoxDecoration(
        color: theme.scaffoldBackgroundColor,
        border: Border(
            top: BorderSide(color: theme.colorScheme.outlineVariant)),
      ),
      child: SafeArea(
        top: false,
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 760),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 10, 12, 12),
              child: voice != null && voice.isBusy
                  ? VoiceRecordingBar(
                      controller: voice,
                      onConfirm: _finishVoice,
                    )
                  : _buildTextRow(context),
            ),
          ),
        ),
      ),
    );
  }
}
