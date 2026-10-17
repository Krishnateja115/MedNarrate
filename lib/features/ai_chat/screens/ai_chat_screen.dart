import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/l10n/app_l10n.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/services/api_models.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/connectivity_service.dart';
import '../../../core/utils/helpers.dart';
import '../../chat/widgets/chat_widgets.dart';
import '../../chat/widgets/quick_question_chips.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

class AIChatScreen extends StatefulWidget {
  final String? reportId;

  const AIChatScreen({super.key, this.reportId});

  @override
  State<AIChatScreen> createState() => _AIChatScreenState();
}

class _AIChatScreenState extends State<AIChatScreen> {
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
  }

  void _retry() {
    setState(() {
      _initializing = true;
      _error = null;
    });
    _initSession();
  }

  Future<void> _initSession() async {
    try {
      if (widget.reportId != null) {
        // Reuse the existing conversation for this report, if there is one.
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
      } else {
        if (!ConnectivityService.instance.isOnline) {
          final sessions = await ApiService.instance.listChatSessions();
          if (sessions.isEmpty) {
            throw const ApiException(0, 'No saved chat is available offline.');
          }
          _sessionId = sessions.first.id;
        } else {
          final session = await ApiService.instance.createChatSession();
          _sessionId = session.id;
        }
      }
      await _loadMessages();
    } on ApiException catch (e) {
      _fail(e.message);
    } catch (_) {
      _fail(appL10n.chatCouldNotOpen);
    }
  }

  void _fail(String message) {
    if (!mounted) return;
    setState(() {
      _error = message;
      _initializing = false;
    });
  }

  Future<void> _loadMessages() async {
    if (_sessionId == null) return;
    try {
      final messages = await ApiService.instance.getChatMessages(_sessionId!);
      if (!mounted) return;
      setState(() {
        _messages = List<ChatMessageModel>.of(messages)
          ..sort((a, b) => a.createdAt.compareTo(b.createdAt));
        _initializing = false;
      });
      _scrollToBottom(animated: false);
    } on ApiException catch (e) {
      _fail(e.message);
    } catch (_) {
      _fail(appL10n.chatCouldNotLoad);
    }
  }

  void _scrollToBottom({bool animated = true}) {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      final target = _scrollController.position.maxScrollExtent;
      if (animated) {
        _scrollController.animateTo(
          target,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      } else {
        _scrollController.jumpTo(target);
      }
    });
  }

  Future<void> _sendMessage({String? textOverride}) async {
    final text = (textOverride ?? _messageController.text).trim();
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

    // When no answer can be produced the server also removes the question, so
    // the optimistic bubble is taken back out and the text returns to the box.
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
      final response = await ApiService.instance
          .sendChatMessage(_sessionId!, text, language: lang);
      if (!mounted) return;
      setState(() {
        _messages.add(response);
        _sending = false;
      });
      _scrollToBottom();
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

  PreferredSizeWidget _buildAppBar(BuildContext context) {
    final theme = Theme.of(context);
    final dark = theme.brightness == Brightness.dark;
    final online = ConnectivityService.instance.isOnline;
    final statusColor = online
        ? (dark ? AppColors.successDark : AppColors.success)
        : theme.colorScheme.onSurface.withValues(alpha: 0.5);
    return AppBar(
      backgroundColor: theme.scaffoldBackgroundColor,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
      titleSpacing: 0,
      shape: Border(
          bottom: BorderSide(color: theme.colorScheme.outlineVariant)),
      title: Row(
        children: [
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              color: dark ? AppColors.darkPrimarySoft : AppColors.primarySoft,
              shape: BoxShape.circle,
            ),
            child: Icon(
              Icons.auto_awesome_rounded,
              size: 20,
              color: dark ? AppColors.darkPrimary : AppColors.lightPrimary,
            ),
          ),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('MedNarrate AI',
                  style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
              const SizedBox(height: 2),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 7,
                    height: 7,
                    decoration: BoxDecoration(
                        color: statusColor, shape: BoxShape.circle),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    online ? appL10n.chatOnline : appL10n.chatOffline,
                    style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                        color: statusColor),
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildBody(BuildContext context) {
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
                onPressed: _retry,
                icon: const Icon(Icons.refresh_rounded),
                label: Text(appL10n.tryAgain),
              ),
            ],
          ),
        ),
      );
    }

    final showTyping = _sending;
    return Column(
      children: [
        const ChatDisclaimer(),
        Expanded(
          child: _messages.isEmpty && !showTyping
              ? ChatEmptyState(
                  general: widget.reportId == null,
                  suggestions: widget.reportId == null
                      ? QuickQuestionChips.generalQuestions
                      : QuickQuestionChips.questions,
                  onSelect: (q) => _sendMessage(textOverride: q),
                )
              : Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 760),
                    child: ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                      itemCount: _messages.length + (showTyping ? 1 : 0),
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
          hint: widget.reportId == null ? appL10n.chatHintAskHealth : null,
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: _buildAppBar(context),
      body: _buildBody(context),
    );
  }
}
