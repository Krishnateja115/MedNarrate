import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../../core/l10n/app_l10n.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/api_models.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/utils/helpers.dart';
import '../../chat/widgets/chat_widgets.dart';
import '../../chat/widgets/quick_question_chips.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

class AIChatTab extends StatefulWidget {
  final String reportId;
  final String? initialQuery;

  const AIChatTab({super.key, required this.reportId, this.initialQuery});

  @override
  State<AIChatTab> createState() => _AIChatTabState();
}

class _AIChatTabState extends State<AIChatTab> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  bool _initializing = true;
  bool _sending = false;
  String? _sessionId;
  List<ChatMessageModel> _messages = [];
  String? _error;

  @override
  void initState() {
    super.initState();
    _initSession();
    if (widget.initialQuery != null && widget.initialQuery!.isNotEmpty) {
      _messageController.text = widget.initialQuery!;
      // Add slight delay to allow init then send
      Future.delayed(const Duration(milliseconds: 1000), () {
        if (mounted && !_sending && _sessionId != null) {
          _sendMessage();
        }
      });
    }
  }

  Future<void> _initSession() async {
    try {
      final sessions = await ApiService.instance.listChatSessions();
      final existing =
          sessions.where((s) => s.reportId == widget.reportId).toList();
      if (existing.isNotEmpty) {
        _sessionId = existing.first.id;
      } else {
        final session = await ApiService.instance
            .createChatSession(reportId: widget.reportId);
        _sessionId = session.id;
      }
      await _loadMessages();
    } on ApiException catch (e) {
      if (mounted) {
        setState(() {
          _error = e.message;
          _initializing = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _error = appL10n.chatCouldNotOpen;
          _initializing = false;
        });
      }
    }
  }

  Future<void> _loadMessages() async {
    if (_sessionId == null) return;
    try {
      final messages = await ApiService.instance.getChatMessages(_sessionId!);
      if (mounted) {
        setState(() {
          _messages = messages;
          _messages.sort((a, b) => a.createdAt.compareTo(b.createdAt));
          _initializing = false;
        });
        _scrollToBottom();
      }
    } on ApiException catch (e) {
      if (mounted) {
        setState(() {
          _error = e.message;
          _initializing = false;
        });
      }
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _sendMessage({String? textOverride}) async {
    final text = textOverride ?? _messageController.text.trim();
    if (text.isEmpty || _sending || _sessionId == null) return;

    final pending = ChatMessageModel(
      id: DateTime.now().toString(),
      chatSessionId: _sessionId!,
      role: 'user',
      content: text,
      createdAt: DateTime.now(),
    );
    _messageController.clear();
    setState(() {
      _sending = true;
      _messages.add(pending);
    });
    _scrollToBottom();

    // When the answer cannot be produced the server removes the question as
    // well, so the optimistic bubble is taken back out and the text returns to
    // the input box instead of leaving an unanswered message behind.
    void giveUp(String message) {
      if (!mounted) return;
      setState(() {
        _sending = false;
        _messages.remove(pending);
      });
      if (_messageController.text.isEmpty) {
        _messageController.value = TextEditingValue(
          text: text,
          selection: TextSelection.collapsed(offset: text.length),
        );
      }
      Helpers.showError(context, message);
    }

    try {
      final lang = Localizations.localeOf(context).languageCode;
      final response =
          await ApiService.instance.sendChatMessage(_sessionId!, text, language: lang);
      if (mounted) {
        setState(() {
          _messages.add(response);
          _sending = false;
        });
        _scrollToBottom();
      }
    } on ApiException catch (e) {
      giveUp(e.message);
    } catch (_) {
      giveUp(appL10n.somethingWentWrongRetry);
    }
  }

  Future<void> _copyMessage(ChatMessageModel msg) async {
    await Clipboard.setData(ClipboardData(text: msg.content));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(AppLocalizations.of(context)!.messageCopied),
      duration: const Duration(seconds: 2),
    ));
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_initializing) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.cloud_off_rounded,
                  size: 40,
                  color: Theme.of(context)
                      .colorScheme
                      .onSurface
                      .withValues(alpha: 0.5)),
              const SizedBox(height: 12),
              Text(_error!,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                      color: Theme.of(context).colorScheme.onSurface)),
              const SizedBox(height: 16),
              OutlinedButton.icon(
                onPressed: () {
                  setState(() {
                    _initializing = true;
                    _error = null;
                  });
                  _initSession();
                },
                icon: const Icon(Icons.refresh_rounded),
                label: Text(AppLocalizations.of(context)!.tryAgain),
              ),
            ],
          ),
        ),
      );
    }

    return Column(
      children: [
        const ChatDisclaimer(),
        Expanded(
          child: _messages.isEmpty && !_sending
              ? ChatEmptyState(
                  suggestions: QuickQuestionChips.questions,
                  onSelect: (q) => _sendMessage(textOverride: q),
                )
              : Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 760),
                    child: ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                      itemCount: _messages.length + (_sending ? 1 : 0),
                      itemBuilder: (context, index) {
                        if (index >= _messages.length) {
                          return const ChatTypingBubble();
                        }
                        final msg = _messages[index];
                        return ChatBubble(
                          message: msg,
                          onCopy: msg.role == 'user'
                              ? null
                              : () => _copyMessage(msg),
                        );
                      },
                    ),
                  ),
                ),
        ),
        ChatComposer(
          controller: _messageController,
          sending: _sending,
          onSend: _sendMessage,
        ),
      ],
    );
  }
}
