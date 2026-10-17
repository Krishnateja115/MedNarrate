import 'package:flutter/material.dart';

import '../../../core/l10n/display_labels.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/services/api_service.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

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
                    Text(AppLocalizations.of(context)!.supportContactTitle,
                        style: Theme.of(context).textTheme.titleLarge),
                    const SizedBox(height: 8),
                    Text(AppLocalizations.of(context)!.supportDescribeHint),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: title,
                      maxLength: 255,
                      decoration: InputDecoration(labelText: AppLocalizations.of(context)!.supportSubject),
                      validator: (value) => (value ?? '').trim().length < 3
                          ? AppLocalizations.of(context)!.supportEnterSubject
                          : null,
                    ),
                    DropdownButtonFormField<String>(
                      initialValue: category,
                      decoration: InputDecoration(labelText: AppLocalizations.of(context)!.supportCategory),
                      items: categories
                          .map((value) => DropdownMenuItem(
                              value: value,
                              child: Text(supportCategoryLabel(AppLocalizations.of(context)!, value))))
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
                      decoration: InputDecoration(
                          labelText: AppLocalizations.of(context)!.supportWhatWentWrong,
                          alignLabelWithHint: true),
                      validator: (value) => (value ?? '').trim().length < 10
                          ? AppLocalizations.of(context)!.supportMoreDetail
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
                                    SnackBar(
                                        content: Text(AppLocalizations.of(this.context)!
                                            .supportRequestSent)),
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
                        child: Text(submitting
                            ? AppLocalizations.of(context)!.sendingEllipsis
                            : AppLocalizations.of(context)!.sendRequest),
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
                  title: Text(ticket['title']?.toString() ??
                      AppLocalizations.of(dialogContext)!.supportRequestDialogTitle),
                  content: SizedBox(
                    width: double.maxFinite,
                    child: ListView(
                      shrinkWrap: true,
                      children: [
                        Text(AppLocalizations.of(dialogContext)!.supportStatusLine(
                            supportStatusLabel(AppLocalizations.of(dialogContext)!,
                                ticket['status']?.toString() ?? ''))),
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
                          decoration: InputDecoration(
                            labelText: AppLocalizations.of(dialogContext)!.replyToSupport,
                            border: const OutlineInputBorder(),
                          ),
                        ),
                      ],
                    ),
                  ),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.of(dialogContext).pop(),
                      child: Text(AppLocalizations.of(dialogContext)!.close),
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
                      child: Text(AppLocalizations.of(dialogContext)!.sendReply),
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
      appBar: AppBar(title: Text(AppLocalizations.of(context)!.supportTitle)),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _createTicket,
        icon: const Icon(Icons.edit_outlined),
        label: Text(AppLocalizations.of(context)!.supportNewRequest),
      ),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _tickets,
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(AppLocalizations.of(context)!.supportCouldNotLoad),
                  TextButton(
                    onPressed: () => setState(_reload),
                    child: Text(AppLocalizations.of(context)!.retry),
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
            return Center(child: Text(AppLocalizations.of(context)!.supportNoRequests));
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
                  title: Text(ticket['title']?.toString() ?? AppLocalizations.of(context)!.supportRequestFallback),
                  subtitle: Text(supportStatusLabel(
                      AppLocalizations.of(context)!, ticket['status']?.toString() ?? '')),
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
