import 'package:flutter/material.dart';
import '../../../../core/constants/app_colors.dart';
import '../../../../core/services/api_service.dart';
import '../../../../core/services/api_models.dart';
import '../../../../core/services/api_exception.dart';
import '../../../../core/utils/helpers.dart';
import '../../chat/widgets/typing_indicator.dart';
import '../../chat/widgets/quick_question_chips.dart';

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
      final existing = sessions.where((s) => s.reportId == widget.reportId).toList();
      if (existing.isNotEmpty) {
        _sessionId = existing.first.id;
      } else {
        final session = await ApiService.instance.createChatSession(reportId: widget.reportId);
        _sessionId = session.id;
      }
      await _loadMessages();
    } on ApiException catch (e) {
      if (mounted) setState(() { _error = e.message; _initializing = false; });
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
      if (mounted) setState(() { _error = e.message; _initializing = false; });
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

    _messageController.clear();
    setState(() {
      _sending = true;
      _messages.add(
        ChatMessageModel(
          id: DateTime.now().toString(),
          chatSessionId: _sessionId!,
          role: 'user',
          content: text,
          createdAt: DateTime.now(),
        ),
      );
    });
    _scrollToBottom();

    try {
      final response = await ApiService.instance.sendChatMessage(_sessionId!, text);
      if (mounted) {
        setState(() {
          _messages.add(response);
          _sending = false;
        });
        _scrollToBottom();
      }
    } on ApiException catch (e) {
      if (mounted) {
        setState(() => _sending = false);
        Helpers.showError(context, e.message);
      }
    }
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
      return Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return Center(child: Text(_error!, style: TextStyle(color: Colors.red)));
    }

    return Column(
      children: [
        if (_messages.isEmpty && !_sending)
          Padding(
            padding: const EdgeInsets.only(top: 16),
            child: QuickQuestionChips(
              onSelect: (q) {
                _messageController.text = q;
                _sendMessage(textOverride: q);
              },
            ),
          ),
        Expanded(
          child: ListView.builder(
            controller: _scrollController,
            padding: const EdgeInsets.all(16),
            itemCount: _messages.length,
            itemBuilder: (context, index) {
              final msg = _messages[index];
              final isUser = msg.role == 'user';
              return _buildMessageBubble(msg, isUser);
            },
          ),
        ),
        if (_sending)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 8.0, horizontal: 16),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Theme.of(context).cardColor,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.border),
                ),
                child: TypingIndicator(),
              ),
            ),
          ),
        Container(
          padding: EdgeInsets.only(
            left: 16,
            right: 16,
            top: 12,
            bottom: MediaQuery.of(context).viewInsets.bottom > 0 ? 12 : 24,
          ),
          decoration: BoxDecoration(
            color: Theme.of(context).cardColor,
            border: Border(top: BorderSide(color: AppColors.border)),
          ),
          child: Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  decoration: BoxDecoration(
                    color: Theme.of(context).scaffoldBackgroundColor,
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: TextField(
                    controller: _messageController,
                    maxLength: 500,
                    minLines: 1,
                    maxLines: 4,
                    decoration: InputDecoration(
                      hintText: "Ask about your report...",
                      border: InputBorder.none,
                      counterText: '',
                    ),
                  ),
                ),
              ),
              SizedBox(width: 8),
              Container(
                decoration: BoxDecoration(
                  color: AppColors.primary,
                  shape: BoxShape.circle,
                ),
                child: IconButton(
                  onPressed: _sending ? null : _sendMessage,
                  icon: Icon(Icons.send_rounded, color: Colors.white),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildMessageBubble(ChatMessageModel msg, bool isUser) {
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: GestureDetector(
        onLongPress: () {
          if (!isUser) {
            // Show copy
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Message copied')));
          }
        },
        child: Container(
          margin: const EdgeInsets.only(bottom: 16),
          constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: isUser ? AppColors.primary : Theme.of(context).cardColor,
            border: isUser ? null : Border.all(color: AppColors.border),
            borderRadius: BorderRadius.only(
              topLeft: const Radius.circular(16),
              topRight: const Radius.circular(16),
              bottomLeft: Radius.circular(isUser ? 16 : 4),
              bottomRight: Radius.circular(isUser ? 4 : 16),
            ),
          ),
          child: SelectableText(
            msg.content,
            style: TextStyle(
              color: isUser ? Colors.white : Theme.of(context).colorScheme.onSurface,
              height: 1.5,
              fontSize: 15,
            ),
          ),
        ),
      ),
    );
  }
}
