import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import 'package:go_router/go_router.dart';
import '../../../core/services/reminder_service.dart';

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
        title: const Text('Delete Reminder'),
        content: const Text('Are you sure you want to delete this reminder?'),
        actions: [
          TextButton(onPressed: () => context.pop(false), child: const Text('Cancel')),
          TextButton(
            onPressed: () => context.pop(true),
            child: const Text('Delete', style: TextStyle(color: Colors.red)),
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
      backgroundColor: AppColors.background,
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
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Medicine Reminders'),
        backgroundColor: AppColors.background,
        elevation: 0,
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showReminderForm(),
        child: const Icon(Icons.add),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _reminders.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.alarm_off, size: 70, color: Colors.grey),
                      const SizedBox(height: 16),
                      const Text('No reminders set', style: TextStyle(color: Colors.white70, fontSize: 18)),
                      const SizedBox(height: 16),
                      FilledButton.icon(
                        onPressed: () => _showReminderForm(),
                        icon: const Icon(Icons.add_alarm),
                        label: const Text('Add your first reminder'),
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
                      color: AppColors.card,
                      margin: const EdgeInsets.only(bottom: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      child: ListTile(
                        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                        leading: Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.blue.withValues(alpha: 0.2),
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(Icons.medication, color: Colors.blue),
                        ),
                        title: Text(r.medicineName, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18)),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            if (r.dosageNote != null && r.dosageNote!.isNotEmpty) ...[
                              const SizedBox(height: 4),
                              Text(r.dosageNote!, style: const TextStyle(color: Colors.white70)),
                            ],
                            const SizedBox(height: 8),
                            Row(
                              children: [
                                const Icon(Icons.access_time, size: 14, color: Colors.blue),
                                const SizedBox(width: 4),
                                Text(
                                  TimeOfDay.fromDateTime(r.time).format(context),
                                  style: const TextStyle(color: Colors.blue, fontWeight: FontWeight.bold),
                                ),
                                const SizedBox(width: 12),
                                if (r.repeatDaily)
                                  const Row(
                                    children: [
                                      Icon(Icons.repeat, size: 14, color: Colors.white54),
                                      SizedBox(width: 4),
                                      Text('Daily', style: TextStyle(color: Colors.white54)),
                                    ],
                                  ),
                              ],
                            ),
                          ],
                        ),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            IconButton(
                              icon: const Icon(Icons.edit, color: Colors.white54),
                              onPressed: () => _showReminderForm(r),
                            ),
                            IconButton(
                              icon: const Icon(Icons.delete, color: Colors.red),
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
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white),
            ),
            const SizedBox(height: 24),
            TextFormField(
              controller: _nameCtrl,
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                labelText: 'Medicine Name',
                labelStyle: const TextStyle(color: Colors.white70),
                prefixIcon: const Icon(Icons.medication_outlined, color: Colors.white54),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: Colors.white24),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: Colors.blue),
                ),
              ),
              validator: (v) => v == null || v.trim().isEmpty ? 'Medicine name is required' : null,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _noteCtrl,
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                labelText: 'Dosage Note (optional)',
                labelStyle: const TextStyle(color: Colors.white70),
                prefixIcon: const Icon(Icons.note_alt_outlined, color: Colors.white54),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: Colors.white24),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: Colors.blue),
                ),
              ),
            ),
            const SizedBox(height: 20),
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
                    borderRadius: BorderRadius.circular(12),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                      decoration: BoxDecoration(
                        border: Border.all(color: Colors.white24),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.access_time, color: Colors.white54),
                          const SizedBox(width: 12),
                          Text(
                            _time.format(context),
                            style: const TextStyle(color: Colors.white, fontSize: 16),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            SwitchListTile(
              title: const Text('Repeat Daily', style: TextStyle(color: Colors.white)),
              contentPadding: EdgeInsets.zero,
              value: _repeatDaily,
              onChanged: (v) => setState(() => _repeatDaily = v),
              activeThumbColor: Colors.blue,
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              height: 55,
              child: FilledButton(
                onPressed: _saving ? null : _save,
                child: Text(_saving ? 'Saving…' : 'Save Reminder'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
