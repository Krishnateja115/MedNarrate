import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import 'package:go_router/go_router.dart';
import '../../../core/services/reminder_service.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

class ReminderScreen extends StatefulWidget {
  const ReminderScreen({super.key});

  @override
  State<ReminderScreen> createState() => _ReminderScreenState();
}

class _ReminderScreenState extends State<ReminderScreen> {
  final ReminderService _reminderService = ReminderService.instance;
  List<ReminderModel> _reminders = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadReminders();
  }

  Future<void> _loadReminders() async {
    setState(() => _loading = true);
    final reminders = await _reminderService.getAll();
    setState(() {
      _reminders = reminders;
      _loading = false;
    });
  }

  Future<void> _deleteReminder(int id) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(AppLocalizations.of(context)!.deleteReminder),
        content: Text(AppLocalizations.of(context)!.deleteReminderConfirm),
        actions: [
          TextButton(onPressed: () => context.pop(false), child: Text(AppLocalizations.of(context)!.cancel)),
          TextButton(
            onPressed: () => context.pop(true),
            child: Text(AppLocalizations.of(context)!.delete, style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
    if (confirm != true) return;
    
    await _reminderService.delete(id);
    _loadReminders();
  }

  void _showReminderForm([ReminderModel? reminder]) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (_) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
        ),
        child: _ReminderForm(
          initialData: reminder,
          onSaved: () {
            context.pop();
            _loadReminders();
          },
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: Text(AppLocalizations.of(context)!.medicineReminders),
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        elevation: 0,
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: Theme.of(context).colorScheme.primary,
                                    foregroundColor: Colors.white,
        elevation: 4,
        onPressed: () => _showReminderForm(),
        child: Icon(Icons.add_rounded, size: 28),
      ),
      body: _loading
          ? Center(child: CircularProgressIndicator())
          : _reminders.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.alarm_off_rounded, size: 64, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.38)),
                      SizedBox(height: 16),
                      Text(AppLocalizations.of(context)!.noRemindersSet, style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontSize: 20, fontWeight: FontWeight.bold)),
                      SizedBox(height: 8),
                      Text(AppLocalizations.of(context)!.setDailyReminders, style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54), fontSize: 14)),
                      SizedBox(height: 24),
                      FilledButton.icon(
                        style: FilledButton.styleFrom(
                          backgroundColor: Theme.of(context).colorScheme.primary,
                                    foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        ),
                        onPressed: () => _showReminderForm(),
                        icon: Icon(Icons.add_alarm_rounded, color: Theme.of(context).colorScheme.onSurface),
                        label: Text(AppLocalizations.of(context)!.addFirstReminder, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                      ),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _reminders.length,
                  itemBuilder: (context, index) {
                    final r = _reminders[index];
                    return Card(
                      color: Theme.of(context).cardColor,
                      margin: const EdgeInsets.only(bottom: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(18),
                        side: BorderSide(color: AppColors.border, width: 1),
                      ),
                      child: ListTile(
                        contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                        leading: Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.08),
                            shape: BoxShape.circle,
                            border: Border.all(color: AppColors.border, width: 1),
                          ),
                          child: Icon(Icons.medication_rounded, color: Theme.of(context).colorScheme.onSurface),
                        ),
                        title: Text(r.medicineName, style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontWeight: FontWeight.bold, fontSize: 18)),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            if (r.dosageNote != null && r.dosageNote!.isNotEmpty) ...[
                              SizedBox(height: 4),
                              Text(r.dosageNote!, style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70))),
                            ],
                            SizedBox(height: 8),
                            Row(
                              children: [
                                Icon(Icons.access_time_rounded, size: 15, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70)),
                                SizedBox(width: 6),
                                Text(
                                  TimeOfDay.fromDateTime(r.time).format(context),
                                  style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontWeight: FontWeight.bold),
                                ),
                                SizedBox(width: 12),
                                if (r.repeatDaily)
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                    decoration: BoxDecoration(
                                      color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.10),
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Row(
                                      children: [
                                        Icon(Icons.repeat_rounded, size: 12, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70)),
                                        SizedBox(width: 4),
                                        Text(AppLocalizations.of(context)!.daily, style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70), fontSize: 11)),
                                      ],
                                    ),
                                  ),
                              ],
                            ),
                          ],
                        ),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            IconButton(
                              icon: Icon(Icons.edit_outlined, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54)),
                              onPressed: () => _showReminderForm(r),
                            ),
                            IconButton(
                              icon: Icon(Icons.delete_outline, color: Colors.redAccent),
                              onPressed: () => _deleteReminder(r.id),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}

class _ReminderForm extends StatefulWidget {
  final ReminderModel? initialData;
  final VoidCallback onSaved;

  const _ReminderForm({this.initialData, required this.onSaved});

  @override
  State<_ReminderForm> createState() => _ReminderFormState();
}

class _ReminderFormState extends State<_ReminderForm> {
  final _formKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  final _noteCtrl = TextEditingController();
  TimeOfDay _time = TimeOfDay.now();
  bool _repeatDaily = true;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    if (widget.initialData != null) {
      _nameCtrl.text = widget.initialData!.medicineName;
      _noteCtrl.text = widget.initialData!.dosageNote ?? '';
      _time = TimeOfDay.fromDateTime(widget.initialData!.time);
      _repeatDaily = widget.initialData!.repeatDaily;
    }
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    
    final now = DateTime.now();
    final dt = DateTime(now.year, now.month, now.day, _time.hour, _time.minute);
    
    final reminder = ReminderModel(
      id: widget.initialData?.id ?? DateTime.now().millisecondsSinceEpoch,
      medicineName: _nameCtrl.text.trim(),
      dosageNote: _noteCtrl.text.trim().isEmpty ? null : _noteCtrl.text.trim(),
      time: dt,
      repeatDaily: _repeatDaily,
    );

    if (widget.initialData == null) {
      await ReminderService.instance.add(reminder);
    } else {
      await ReminderService.instance.update(reminder);
    }
    
    widget.onSaved();
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _noteCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              widget.initialData == null ? 'New Reminder' : 'Edit Reminder',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Theme.of(context).colorScheme.onSurface),
            ),
            SizedBox(height: 24),
            TextFormField(
              controller: _nameCtrl,
              style: TextStyle(color: Theme.of(context).colorScheme.onSurface),
              decoration: InputDecoration(
                labelText: 'Medicine Name',
                labelStyle: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70)),
                prefixIcon: Icon(Icons.medication_outlined, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54)),
                filled: true,
                fillColor: Theme.of(context).cardColor,
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: BorderSide(color: AppColors.border),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: BorderSide(color: Theme.of(context).colorScheme.onSurface, width: 1.5),
                ),
              ),
              validator: (v) => v == null || v.trim().isEmpty ? 'Medicine name is required' : null,
            ),
            SizedBox(height: 16),
            TextFormField(
              controller: _noteCtrl,
              style: TextStyle(color: Theme.of(context).colorScheme.onSurface),
              decoration: InputDecoration(
                labelText: 'Dosage Note (optional)',
                labelStyle: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70)),
                prefixIcon: Icon(Icons.note_alt_outlined, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54)),
                filled: true,
                fillColor: Theme.of(context).cardColor,
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: BorderSide(color: AppColors.border),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: BorderSide(color: Theme.of(context).colorScheme.onSurface, width: 1.5),
                ),
              ),
            ),
            SizedBox(height: 20),
            Row(
              children: [
                Expanded(
                  child: InkWell(
                    onTap: () async {
                      final picked = await showTimePicker(
                        context: context,
                        initialTime: _time,
                      );
                      if (picked != null) setState(() => _time = picked);
                    },
                    borderRadius: BorderRadius.circular(14),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                      decoration: BoxDecoration(
                        color: Theme.of(context).cardColor,
                        border: Border.all(color: AppColors.border),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.access_time_rounded, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70)),
                          SizedBox(width: 12),
                          Text(
                            _time.format(context),
                            style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontSize: 16, fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
            SizedBox(height: 16),
            SwitchListTile(
              title: Text(AppLocalizations.of(context)!.repeatDaily, style: TextStyle(color: Theme.of(context).colorScheme.onSurface)),
              contentPadding: EdgeInsets.zero,
              value: _repeatDaily,
              onChanged: (v) => setState(() => _repeatDaily = v),
              activeThumbColor: Theme.of(context).colorScheme.onSurface,
            ),
            SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              height: 55,
              child: FilledButton(
                style: FilledButton.styleFrom(
                  backgroundColor: Theme.of(context).colorScheme.primary,
                                    foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                ),
                onPressed: _saving ? null : _save,
                child: Text(
                  _saving ? 'Saving…' : 'Save Reminder',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
