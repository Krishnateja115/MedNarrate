import 'package:flutter/material.dart';
import '../../../core/services/api_service.dart';
import '../../../shared/widgets/glassmorphism_card.dart';
import '../models/medication_schedule_model.dart';

class MedicationSchedulesScreen extends StatefulWidget {
  const MedicationSchedulesScreen({super.key});

  @override
  State<MedicationSchedulesScreen> createState() => _MedicationSchedulesScreenState();
}

class _MedicationSchedulesScreenState extends State<MedicationSchedulesScreen> {
  bool _isLoading = true;
  String? _error;
  List<MedicationScheduleModel> _schedules = [];
  final Set<String> _togglingIds = {};

  @override
  void initState() {
    super.initState();
    _fetchSchedules();
  }

  Future<void> _fetchSchedules() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final data = await ApiService.instance.getMedicationSchedules();
      setState(() {
        _schedules = data.map((e) => MedicationScheduleModel.fromMap(e)).toList();
      });
    } catch (e) {
      setState(() {
        _error = "Failed to load schedules: $e";
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _toggleSchedule(String id, bool currentValue) async {
    setState(() {
      _togglingIds.add(id);
    });

    try {
      await ApiService.instance.toggleMedicationSchedule(id);
      // Update local state
      setState(() {
        final index = _schedules.indexWhere((s) => s.id == id);
        if (index != -1) {
          final old = _schedules[index];
          _schedules[index] = MedicationScheduleModel(
            id: old.id,
            reportId: old.reportId,
            medicationName: old.medicationName,
            dosage: old.dosage,
            frequency: old.frequency,
            timesOfDay: old.timesOfDay,
            durationDays: old.durationDays,
            notes: old.notes,
            isActive: !currentValue,
            createdAt: old.createdAt,
          );
        }
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to update schedule: $e')),
        );
      }
    } finally {
      setState(() {
        _togglingIds.remove(id);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: const Text('Medication Reminders'),
        flexibleSpace: ClipRect(
          child: BackdropFilter(
            filter: ColorFilter.mode(Colors.black.withValues(alpha: 0.01), BlendMode.srcOver),
          ),
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Theme.of(context).colorScheme.surface,
              Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
            ],
          ),
        ),
        child: SafeArea(
          child: _isLoading
              ? const Center(child: CircularProgressIndicator())
              : _error != null
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(_error!, style: const TextStyle(color: Colors.red)),
                          ElevatedButton(onPressed: _fetchSchedules, child: const Text('Retry')),
                        ],
                      ),
                    )
                  : _schedules.isEmpty
                      ? _buildEmptyState()
                      : ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: _schedules.length,
                          itemBuilder: (context, index) {
                            return _buildMedicationCard(_schedules[index]);
                          },
                        ),
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.medication, size: 80, color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.5)),
            const SizedBox(height: 24),
            Text(
              'No medication schedules found in your reports yet. Upload a report that contains prescriptions to start tracking.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
                  ),
            ),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: () {
                Navigator.pop(context);
                // Optionally navigate to reports tab if using bottom nav
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFE8183C),
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: const Text('Go to Reports'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMedicationCard(MedicationScheduleModel schedule) {
    final bool isToggling = _togglingIds.contains(schedule.id);
    final theme = Theme.of(context);

    return Opacity(
      opacity: schedule.isActive ? 1.0 : 0.6,
      child: GlassmorphismCard(
        margin: const EdgeInsets.only(bottom: 16),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(16),
          child: Container(
            decoration: BoxDecoration(
              border: const Border(
                left: BorderSide(color: Color(0xFFE8183C), width: 6),
              ),
            ),
            padding: const EdgeInsets.all(16),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Name & Dosage
                      Wrap(
                        crossAxisAlignment: WrapCrossAlignment.center,
                        spacing: 8,
                        children: [
                          Text(
                            schedule.medicationName,
                            style: theme.textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.bold,
                              decoration: schedule.isActive ? null : TextDecoration.lineThrough,
                            ),
                          ),
                          if (schedule.dosage != null)
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: const Color(0xFFE8183C).withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                schedule.dosage!,
                                style: TextStyle(
                                  color: const Color(0xFFE8183C),
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                  decoration: schedule.isActive ? null : TextDecoration.lineThrough,
                                ),
                              ),
                            ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      
                      // Frequency & Times
                      if (schedule.frequency != null || schedule.timesOfDay.isNotEmpty)
                        Row(
                          children: [
                            const Icon(Icons.access_time, size: 16, color: Colors.grey),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                '${schedule.frequency ?? 'Scheduled'} (${schedule.timesOfDay.join(', ')})',
                                style: theme.textTheme.bodyMedium?.copyWith(
                                  color: Colors.grey.shade700,
                                  decoration: schedule.isActive ? null : TextDecoration.lineThrough,
                                ),
                              ),
                            ),
                          ],
                        ),
                      
                      // Duration
                      if (schedule.durationDays != null)
                        Padding(
                          padding: const EdgeInsets.only(top: 8.0),
                          child: Row(
                            children: [
                              const Icon(Icons.calendar_today, size: 16, color: Colors.grey),
                              const SizedBox(width: 8),
                              Text(
                                'For ${schedule.durationDays} days',
                                style: theme.textTheme.bodyMedium?.copyWith(
                                  color: Colors.grey.shade700,
                                  decoration: schedule.isActive ? null : TextDecoration.lineThrough,
                                ),
                              ),
                            ],
                          ),
                        ),
                      
                      // Notes
                      if (schedule.notes != null)
                        Padding(
                          padding: const EdgeInsets.only(top: 8.0),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Icon(Icons.info_outline, size: 16, color: Colors.grey),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  schedule.notes!,
                                  style: theme.textTheme.bodyMedium?.copyWith(
                                    color: Colors.grey.shade700,
                                    fontStyle: FontStyle.italic,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                    ],
                  ),
                ),
                
                // Toggle Switch
                isToggling
                    ? const Padding(
                        padding: EdgeInsets.all(12.0),
                        child: SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFFE8183C)),
                        ),
                      )
                    : Switch(
                        value: schedule.isActive,
                        activeThumbColor: const Color(0xFFE8183C),
                        onChanged: (val) => _toggleSchedule(schedule.id, schedule.isActive),
                      ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
