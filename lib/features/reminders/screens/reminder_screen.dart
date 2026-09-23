import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/services/api_service.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

class ReminderScreen extends StatefulWidget {
  final bool autoOpenAdd;
  final Map<String, dynamic>? prefillMed;
  
  const ReminderScreen({
    super.key, 
    this.autoOpenAdd = false,
    this.prefillMed,
  });

  @override
  State<ReminderScreen> createState() => _ReminderScreenState();
}

class _ReminderScreenState extends State<ReminderScreen> {
  final ApiService _apiService = ApiService.instance;
  List<Map<String, dynamic>> _reminders = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadReminders();
    
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (widget.autoOpenAdd || widget.prefillMed != null) {
        _showReminderForm(widget.prefillMed);
      }
    });
  }

  Future<void> _loadReminders() async {
    if (!mounted) return;
    setState(() => _loading = true);
    try {
      final reminders = await _apiService.getReminders();
      if (mounted) {
        setState(() {
          _reminders = reminders;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _loading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load reminders: $e')),
        );
      }
    }
  }

  Future<void> _deleteReminder(String id) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(AppLocalizations.of(context)!.deleteReminder),
        content: Text(AppLocalizations.of(context)!.deleteReminderConfirm),
        actions: [
          TextButton(onPressed: () => context.pop(false), child: Text(AppLocalizations.of(context)!.cancel)),
          TextButton(
            onPressed: () => context.pop(true),
            child: Text(AppLocalizations.of(context)!.delete, style: const TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
    if (confirm != true) return;
    
    try {
      await _apiService.deleteReminder(id);
      _loadReminders();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to delete reminder: $e')),
        );
      }
    }
  }

  Future<void> _toggleReminder(String id, bool currentStatus) async {
    try {
      await _apiService.updateReminder(id, {'is_active': !currentStatus});
      _loadReminders();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to update status: $e')),
        );
      }
    }
  }

  void _showReminderForm([Map<String, dynamic>? reminder]) {
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
        child: const Icon(Icons.add_rounded, size: 28),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _reminders.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.alarm_off_rounded, size: 64, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.38)),
                      const SizedBox(height: 16),
                      Text(AppLocalizations.of(context)!.noRemindersSet, style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontSize: 20, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      Text(AppLocalizations.of(context)!.setDailyReminders, style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54), fontSize: 14)),
                      const SizedBox(height: 24),
                      FilledButton.icon(
                        style: FilledButton.styleFrom(
                          backgroundColor: Theme.of(context).colorScheme.primary,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        ),
                        onPressed: () => _showReminderForm(),
                        icon: Icon(Icons.add_alarm_rounded, color: Theme.of(context).colorScheme.onSurface),
                        label: Text(AppLocalizations.of(context)!.addFirstReminder, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                      ),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _reminders.length,
                  itemBuilder: (context, index) {
                    final r = _reminders[index];
                    final times = List<String>.from(r['times_of_day'] ?? []);
                    final isActive = r['is_active'] ?? true;
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
                        title: Text(r['medication_name'], style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontWeight: FontWeight.bold, fontSize: 18)),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const SizedBox(height: 4),
                            Text([
                                if (r['dosage'] != null && r['dosage'].toString().isNotEmpty) r['dosage'],
                                if (r['frequency'] != null && r['frequency'].toString().isNotEmpty) r['frequency'],
                              ].join(' • '), 
                              style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70))
                            ),
                            if (r['notes'] != null && r['notes'].toString().isNotEmpty) ...[
                                const SizedBox(height: 2),
                                Text(r['notes'], style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.50), fontStyle: FontStyle.italic)),
                            ],
                            const SizedBox(height: 8),
                            Wrap(
                              spacing: 8,
                              runSpacing: 4,
                              children: times.map((t) {
                                return Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: Colors.orange.withValues(alpha: 0.15),
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      const Icon(Icons.access_time, size: 12, color: Colors.orange),
                                      const SizedBox(width: 4),
                                      Text(t, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.orange)),
                                    ],
                                  ),
                                );
                              }).toList(),
                            )
                          ],
                        ),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Switch(
                              value: isActive,
                              onChanged: (v) => _toggleReminder(r['id'], isActive),
                              activeThumbColor: Colors.orange,
                            ),
                            IconButton(
                              icon: Icon(Icons.edit_outlined, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54)),
                              onPressed: () => _showReminderForm(r),
                            ),
                            IconButton(
                              icon: const Icon(Icons.delete_outline, color: Colors.redAccent),
                              onPressed: () => _deleteReminder(r['id']),
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
  final Map<String, dynamic>? initialData;
  final VoidCallback onSaved;

  const _ReminderForm({this.initialData, required this.onSaved});

  @override
  State<_ReminderForm> createState() => _ReminderFormState();
}

class _ReminderFormState extends State<_ReminderForm> {
  final _formKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  final _dosageCtrl = TextEditingController();
  final _noteCtrl = TextEditingController();
  final _durationCtrl = TextEditingController();
  
  String _frequency = "Once daily";
  final List<String> _frequencies = [
    "Once daily",
    "Twice daily",
    "Three times daily",
    "Four times daily",
    "As needed",
    "Custom"
  ];
  
  final List<TimeOfDay> _times = [];
  bool _saving = false;
  String? _reportId;

  @override
  void initState() {
    super.initState();
    if (widget.initialData != null) {
      _nameCtrl.text = widget.initialData!['medication_name'] ?? widget.initialData!['name'] ?? '';
      _dosageCtrl.text = widget.initialData!['dosage'] ?? '';
      
      final freq = widget.initialData!['frequency'];
      if (freq != null && freq.toString().isNotEmpty) {
        if (_frequencies.contains(freq)) {
          _frequency = freq;
        } else {
          _frequencies.add(freq);
          _frequency = freq;
        }
      }
      
      _durationCtrl.text = widget.initialData!['duration_days']?.toString() ?? '';
      _noteCtrl.text = widget.initialData!['notes'] ?? '';
      _reportId = widget.initialData!['report_id'];
      
      final rawTimes = widget.initialData!['times_of_day'] as List<dynamic>? ?? [];
      for (var rt in rawTimes) {
        final t = _parseTime(rt.toString());
        if (t != null) _times.add(t);
      }
    }
    
    // Always start with at least one time slot if empty
    if (_times.isEmpty) {
      _times.add(TimeOfDay.now());
    }
  }

  TimeOfDay? _parseTime(String t) {
    t = t.toLowerCase().trim();
    if (t.contains('morning')) return const TimeOfDay(hour: 8, minute: 0);
    if (t.contains('afternoon')) return const TimeOfDay(hour: 14, minute: 0);
    if (t.contains('evening')) return const TimeOfDay(hour: 18, minute: 0);
    if (t.contains('night') || t.contains('bedtime')) return const TimeOfDay(hour: 21, minute: 0);
    
    final parts = t.split(RegExp(r'[:.]'));
    if (parts.length >= 2) {
      int h = int.tryParse(parts[0]) ?? 8;
      int m = int.tryParse(parts[1].replaceAll(RegExp(r'[^0-9]'), '')) ?? 0;
      if (t.contains('pm') && h < 12) h += 12;
      if (t.contains('am') && h == 12) h = 0;
      return TimeOfDay(hour: h.clamp(0, 23), minute: m.clamp(0, 59));
    }
    return const TimeOfDay(hour: 8, minute: 0);
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    
    final timesStr = _times.map((t) => '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}').toList();
    
    try {
      if (widget.initialData == null || widget.initialData!['id'] == null) {
        await ApiService.instance.createReminder(
           medicationName: _nameCtrl.text.trim(),
           dosage: _dosageCtrl.text.trim(),
           frequency: _frequency,
           timesOfDay: timesStr,
           durationDays: int.tryParse(_durationCtrl.text),
           notes: _noteCtrl.text.trim().isEmpty ? null : _noteCtrl.text.trim(),
           reportId: _reportId,
        );
      } else {
        await ApiService.instance.updateReminder(
           widget.initialData!['id'],
           {
               'medication_name': _nameCtrl.text.trim(),
               'dosage': _dosageCtrl.text.trim(),
               'frequency': _frequency,
               'times_of_day': timesStr,
               'duration_days': int.tryParse(_durationCtrl.text),
               'notes': _noteCtrl.text.trim().isEmpty ? null : _noteCtrl.text.trim(),
           }
        );
      }
      widget.onSaved();
    } catch (e) {
      if (mounted) {
        setState(() => _saving = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error saving reminder: $e')),
        );
      }
    }
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _dosageCtrl.dispose();
    _noteCtrl.dispose();
    _durationCtrl.dispose();
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
              (widget.initialData == null || widget.initialData!['id'] == null) ? 'New Medication' : 'Edit Medication',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Theme.of(context).colorScheme.onSurface),
            ),
            const SizedBox(height: 24),
            TextFormField(
              controller: _nameCtrl,
              style: TextStyle(color: Theme.of(context).colorScheme.onSurface),
              decoration: InputDecoration(
                labelText: 'Medicine Name',
                prefixIcon: const Icon(Icons.medication_outlined),
                filled: true,
                fillColor: Theme.of(context).cardColor,
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
              ),
              validator: (v) => v == null || v.trim().isEmpty ? 'Medicine name is required' : null,
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    controller: _dosageCtrl,
                    style: TextStyle(color: Theme.of(context).colorScheme.onSurface),
                    decoration: InputDecoration(
                      labelText: 'Dosage (e.g. 500mg, 1 tablet)',
                      filled: true,
                      fillColor: Theme.of(context).cardColor,
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              initialValue: _frequency,
              decoration: InputDecoration(
                labelText: 'Frequency',
                filled: true,
                fillColor: Theme.of(context).cardColor,
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
              ),
              items: _frequencies.map((f) => DropdownMenuItem(value: f, child: Text(f))).toList(),
              onChanged: (v) => setState(() => _frequency = v!),
            ),
            const SizedBox(height: 20),
            Text('Times of Day', style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                ..._times.asMap().entries.map((e) {
                  final idx = e.key;
                  final t = e.value;
                  return Chip(
                    label: Text(t.format(context), style: const TextStyle(fontWeight: FontWeight.bold)),
                    onDeleted: () {
                      setState(() => _times.removeAt(idx));
                    },
                    backgroundColor: Colors.orange.withValues(alpha: 0.15),
                    deleteIconColor: Colors.orange,
                  );
                }),
                ActionChip(
                  label: const Text('Add Time'),
                  avatar: const Icon(Icons.add, size: 16),
                  onPressed: () async {
                    final picked = await showTimePicker(context: context, initialTime: TimeOfDay.now());
                    if (picked != null) {
                      setState(() => _times.add(picked));
                    }
                  },
                ),
              ],
            ),
            if (_times.isEmpty)
              const Padding(
                padding: EdgeInsets.only(top: 8.0),
                child: Text("Please add at least one time.", style: TextStyle(color: Colors.red, fontSize: 12)),
              ),
            const SizedBox(height: 20),
            TextFormField(
              controller: _noteCtrl,
              style: TextStyle(color: Theme.of(context).colorScheme.onSurface),
              decoration: InputDecoration(
                labelText: 'Additional Notes (optional)',
                prefixIcon: const Icon(Icons.note_alt_outlined),
                filled: true,
                fillColor: Theme.of(context).cardColor,
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
              ),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              height: 55,
              child: FilledButton(
                style: FilledButton.styleFrom(
                  backgroundColor: Theme.of(context).colorScheme.primary,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                ),
                onPressed: (_saving || _times.isEmpty) ? null : _save,
                child: Text(
                  _saving ? 'Saving…' : 'Save Medication',
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
