import 'package:flutter/material.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/services/api_service.dart';
import '../models/document_type_check.dart';

/// Small, optional hint under the report overview: which kind of record the
/// report's wording resembles, from the experimental MRAD-trained model.
///
/// It shows nothing at all unless the server says the feature is on and the
/// model is sure, and any error (offline, server problem) is silent. It never
/// affects the summary, the lab values or anything else on the screen.
class DocumentTypeBadge extends StatefulWidget {
  final String reportId;

  /// For tests; the app uses the API.
  final Future<DocumentTypeCheck> Function(String reportId)? loader;

  const DocumentTypeBadge({super.key, required this.reportId, this.loader});

  @override
  State<DocumentTypeBadge> createState() => _DocumentTypeBadgeState();
}

class _DocumentTypeBadgeState extends State<DocumentTypeBadge> {
  late Future<DocumentTypeCheck> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  @override
  void didUpdateWidget(covariant DocumentTypeBadge old) {
    super.didUpdateWidget(old);
    if (old.reportId != widget.reportId) _future = _load();
  }

  Future<DocumentTypeCheck> _load() async {
    try {
      final loader = widget.loader ?? ApiService.instance.getDocumentTypeCheck;
      return await loader(widget.reportId);
    } catch (_) {
      return DocumentTypeCheck.hidden;
    }
  }

  static String typeText(AppLocalizations l, String? label) {
    switch (label) {
      case 'Blood':
        return l.docTypeBlood;
      case 'Health':
        return l.docTypeHealth;
      default:
        return l.docTypeTcga;
    }
  }

  void _showAbout(BuildContext context, DocumentTypeCheck check) {
    final l = AppLocalizations.of(context)!;
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 4, 20, 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(l.docTypeCheckTitle,
                  style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
              const SizedBox(height: 10),
              Text(typeText(l, check.label),
                  style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
              const SizedBox(height: 4),
              Text(l.docTypeCheckScore(check.percent),
                  style: TextStyle(
                      fontSize: 13,
                      color: Theme.of(ctx).colorScheme.onSurface.withValues(alpha: 0.65))),
              const SizedBox(height: 12),
              Text(l.docTypeCheckAbout, style: const TextStyle(fontSize: 13, height: 1.45)),
              const SizedBox(height: 16),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: () => Navigator.of(ctx).pop(),
                  child: Text(l.close),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<DocumentTypeCheck>(
      future: _future,
      builder: (context, snap) {
        final check = snap.data;
        if (check == null || !check.isShown) return const SizedBox.shrink();
        final l = AppLocalizations.of(context)!;
        final theme = Theme.of(context);
        return Padding(
          padding: const EdgeInsets.only(top: 12),
          child: Material(
            color: AppColors.primary.withValues(alpha: 0.07),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
              side: BorderSide(color: theme.colorScheme.outlineVariant),
            ),
            clipBehavior: Clip.antiAlias,
            child: InkWell(
              key: const ValueKey('document-type-badge'),
              onTap: () => _showAbout(context, check),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                child: Row(
                  children: [
                    const Icon(Icons.fact_check_outlined, size: 20, color: AppColors.primary),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(typeText(l, check.label),
                              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                          const SizedBox(height: 2),
                          Text(l.docTypeCheckScore(check.percent),
                              style: TextStyle(
                                  fontSize: 11,
                                  color: theme.colorScheme.onSurface.withValues(alpha: 0.6))),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: Colors.amber.withValues(alpha: 0.18),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(l.docTypeCheckExperimental,
                          style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700)),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
