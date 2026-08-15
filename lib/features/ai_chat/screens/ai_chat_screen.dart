import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/api_models.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/utils/helpers.dart';

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

  Future<void> _initSession() async {
    try {
      if (widget.reportId != null) {
        // Try to find an existing session for this report
        final sessions = await ApiService.instance.listChatSessions();
        final existing = sessions.where((s) => s.reportId == widget.reportId).toList();
        if (existing.isNotEmpty) {
          _sessionId = existing.first.id;
        } else {
          final session = await ApiService.instance.createChatSession(reportId: widget.reportId);
          _sessionId = session.id;
        }
      } else {
        // Create a general session
        final session = await ApiService.instance.createChatSession();
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
          _messages = messages.reversed.toList(); // Assuming API returns newest first or we just want them chronological
          // If the API returns newest first (common for paginated chat), reversing puts oldest at top. 
          // Let's sort by createdAt to be safe:
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

  Future<void> _sendMessage() async {
    final text = _messageController.text.trim();
    if (text.isEmpty || _sending || _sessionId == null) return;

    _messageController.clear();
    setState(() {
      _sending = true;
      // Optimistic update
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
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        elevation: 0,
        centerTitle: false,
        title: Row(
          children: [
            CircleAvatar(radius: 18, child: Icon(Icons.smart_toy, size: 20)),
            SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("MedNarrate AI", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                Text("Online", style: TextStyle(fontSize: 12, color: Colors.green)),
              ],
            ),
          ],
        ),
      ),
      body: _initializing
          ? Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: TextStyle(color: Colors.red)))
              : Column(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      color: Colors.amber.withValues(alpha: 0.1),
                      child: Row(
                        children: [
                          Icon(Icons.warning_amber_rounded, color: Colors.amber, size: 18),
                          SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              "AI responses are for informational purposes and do not replace professional medical advice. Always consult your doctor.",
                              style: TextStyle(color: Colors.amber, fontSize: 11, height: 1.3),
                            ),
                          ),
                        ],
                      ),
                    ),
                    Expanded(
                      child: _messages.isEmpty
                          ? Center(
                              child: Text(
                                "Hello! I'm MedNarrate AI.\nAsk me any health-related question.",
                                textAlign: TextAlign.center,
                                style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70), fontSize: 16),
                              ),
                            )
                          : ListView.builder(
                              controller: _scrollController,
                              padding: const EdgeInsets.all(18),
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
                        padding: EdgeInsets.symmetric(vertical: 8),
                        child: CircularProgressIndicator(),
                      ),
                    Container(
                      padding: const EdgeInsets.all(15),
                      decoration: BoxDecoration(
                        color: Theme.of(context).cardColor,
                        borderRadius: const BorderRadius.vertical(top: Radius.circular(25)),
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _messageController,
                              style: TextStyle(color: Theme.of(context).colorScheme.onSurface),
                              decoration: InputDecoration(
                                hintText: "Ask about your report...",
                                hintStyle: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54)),
                                border: InputBorder.none,
                              ),
                              onSubmitted: (_) => _sendMessage(),
                            ),
                          ),
                          IconButton(
                            onPressed: _sendMessage,
                            icon: Icon(Icons.send_rounded, color: Colors.blue),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
    );
  }

  Widget _buildMessageBubble(ChatMessageModel msg, bool isUser) {
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 18),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
        child: Column(
          crossAxisAlignment: isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: isUser ? AppColors.primary : Theme.of(context).cardColor,
                border: isUser ? null : Border.all(color: AppColors.border, width: 1),
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(20),
                  topRight: const Radius.circular(20),
                  bottomLeft: Radius.circular(isUser ? 20 : 4),
                  bottomRight: Radius.circular(isUser ? 4 : 20),
                ),
              ),
              child: Text(
                msg.content,
                style: TextStyle(color: isUser ? Theme.of(context).colorScheme.onSurface : Theme.of(context).colorScheme.onSurface, fontSize: 15, height: 1.5),
              ),
            ),
            if (!isUser && msg.sources.isNotEmpty) ...[
              SizedBox(height: 6),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: msg.sources.map((src) {
                  final sourceName = src['source']?.toString() ?? 'Reference';
                  return Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.10),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      'Source: $sourceName',
                      style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54), fontSize: 10),
                    ),
                  );
                }).toList(),
              ),
            ]
          ],
        ),
      ),
    );
  }
}