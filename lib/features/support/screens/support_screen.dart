import 'package:flutter/material.dart';

import '../../../core/services/api_exception.dart';
import '../../../core/services/api_service.dart';

class SupportScreen extends StatefulWidget {
  const SupportScreen({super.key, this.reportId, this.reportTitle});

  final String? reportId;
  final String? reportTitle;

  @override
  State<SupportScreen> createState() => _SupportScreenState();
}

class _SupportScreenState extends State<SupportScreen> {
  static const categories = [
    'Login/Account',
    'Report Processing',
    'AI/Analysis',
    'Chat',
    'Translation',
    'Notifications',
    'Medication Reminder',
    'Performance',
    'Security',
    'Privacy',
    'Other',
  ];

  late Future<List<Map<String, dynamic>>> _tickets;

  @override
  void initState() {
    super.initState();
    _reload();
    if (widget.reportId != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) _createTicket();
      });
    }
  }

  void _reload() {
    _tickets = ApiService.instance.listSupportTickets();
  }

  Future<void> _createTicket() async {
    final formKey = GlobalKey<FormState>();
    final title = TextEditingController(
      text: widget.reportId == null
          ? ''
          : 'Check result in ${widget.reportTitle ?? 'my report'}',
    );
    final description = TextEditingController();
    var category = widget.reportId == null ? 'Other' : 'AI/Analysis';
    var submitting = false;
    try {
      await showModalBottomSheet<void>(
        context: context,
        isScrollControlled: true,
        builder: (sheetContext) => StatefulBuilder(
          builder: (context, setSheetState) => Padding(
            padding: EdgeInsets.fromLTRB(
              20,
              20,
              20,
              MediaQuery.viewInsetsOf(context).bottom + 20,
            ),
            child: Form(
              key: formKey,
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Contact support',
                        style: Theme.of(context).textTheme.titleLarge),
                    const SizedBox(height: 8),
                    const Text(
                      'Describe the problem without pasting your full medical report. '
                      'We will attach the report ID when relevant.',
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: title,
                      maxLength: 255,
                      decoration: const InputDecoration(labelText: 'Subject'),
                      validator: (value) => (value ?? '').trim().length < 3
                          ? 'Enter a subject'
                          : null,
                    ),
                    DropdownButtonFormField<String>(
                      initialValue: category,
                      decoration: const InputDecoration(labelText: 'Category'),
                      items: categories
                          .map((value) => DropdownMenuItem(
                              value: value, child: Text(value)))
                          .toList(),
                      onChanged: (value) {
                        if (value != null) category = value;
                      },
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: description,
                      minLines: 3,
                      maxLines: 6,
                      maxLength: 5000,
                      decoration: const InputDecoration(
                          labelText: 'What went wrong?',
                          alignLabelWithHint: true),
                      validator: (value) => (value ?? '').trim().length < 10
                          ? 'Please add a little more detail'
                          : null,
                    ),
                    const SizedBox(height: 8),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton(
                        onPressed: submitting
                            ? null
                            : () async {
                                if (!formKey.currentState!.validate()) return;
                                setSheetState(() => submitting = true);
                                try {
                                  await ApiService.instance.createSupportTicket(
                                    title: title.text.trim(),
                                    description: description.text.trim(),
                                    category: category,
                                    relatedReportId: widget.reportId,
                                  );
                                  if (!mounted || !sheetContext.mounted) return;
                                  Navigator.of(sheetContext).pop();
                                  setState(_reload);
                                  ScaffoldMessenger.of(this.context)
                                      .showSnackBar(
                                    const SnackBar(
                                        content: Text('Support request sent')),
                                  );
                                } on ApiException catch (error) {
                                  if (!mounted) return;
                                  ScaffoldMessenger.of(this.context)
                                      .showSnackBar(
                                    SnackBar(content: Text(error.message)),
                                  );
                                } finally {
                                  if (sheetContext.mounted) {
                                    setSheetState(() => submitting = false);
                                  }
                                }
                              },
                        child: Text(submitting ? 'Sending…' : 'Send request'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      );
    } finally {
      title.dispose();
      description.dispose();
    }
  }

  Future<void> _openTicket(String id) async {
    final reply = TextEditingController();
    try {
      var ticket = await ApiService.instance.getSupportTicket(id);
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (dialogContext) => StatefulBuilder(
            builder: (dialogContext, setDialogState) => AlertDialog(
                  title: Text(ticket['title']?.toString() ?? 'Support request'),
                  content: SizedBox(
                    width: double.maxFinite,
                    child: ListView(
                      shrinkWrap: true,
                      children: [
                        Text('Status: ${ticket['status']}'),
                        const SizedBox(height: 12),
                        for (final message
                            in (ticket['messages'] as List<dynamic>? ?? []))
                          Padding(
                            padding: const EdgeInsets.only(bottom: 12),
                            child: Text(
                                (message as Map<String, dynamic>)['content']
                                        ?.toString() ??
                                    ''),
                          ),
                        const SizedBox(height: 8),
                        TextField(
                          controller: reply,
                          minLines: 2,
                          maxLines: 4,
                          decoration: const InputDecoration(
                            labelText: 'Reply to support',
                            border: OutlineInputBorder(),
                          ),
                        ),
                      ],
                    ),
                  ),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.of(dialogContext).pop(),
                      child: const Text('Close'),
                    ),
                    TextButton(
                      onPressed: () async {
                        final message = reply.text.trim();
                        if (message.isEmpty) return;
                        try {
                          await ApiService.instance
                              .replyToSupportTicket(id, message);
                          final updated =
                              await ApiService.instance.getSupportTicket(id);
                          if (!dialogContext.mounted) return;
                          setDialogState(() {
                            ticket = updated;
                            reply.clear();
                          });
                          if (mounted) setState(_reload);
                        } on ApiException catch (error) {
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text(error.message)),
                            );
                          }
                        }
                      },
                      child: const Text('Send reply'),
                    ),
                  ],
                )),
      );
    } on ApiException catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error.message)),
        );
      }
    } finally {
      reply.dispose();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Support')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _createTicket,
        icon: const Icon(Icons.edit_outlined),
        label: const Text('New request'),
      ),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _tickets,
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('Could not load support requests.'),
                  TextButton(
                    onPressed: () => setState(_reload),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final tickets = snapshot.data!;
          if (tickets.isEmpty) {
            return const Center(child: Text('No support requests yet.'));
          }
          return RefreshIndicator(
            onRefresh: () async {
              setState(_reload);
              await _tickets;
            },
            child: ListView.builder(
              itemCount: tickets.length,
              itemBuilder: (context, index) {
                final ticket = tickets[index];
                return ListTile(
                  title: Text(ticket['title']?.toString() ?? 'Request'),
                  subtitle: Text(ticket['status']?.toString() ?? ''),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => _openTicket(ticket['id'].toString()),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
