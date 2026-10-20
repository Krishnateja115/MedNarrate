import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:printing/printing.dart';

import '../../../core/services/api_service.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

/// Displays the uploaded document, not an AI-generated export.
class OriginalReportScreen extends StatefulWidget {
  const OriginalReportScreen({
    super.key,
    required this.reportId,
    required this.fileName,
  });

  final String reportId;
  final String fileName;

  @override
  State<OriginalReportScreen> createState() => _OriginalReportScreenState();
}

class _OriginalReportScreenState extends State<OriginalReportScreen> {
  late Future<Uint8List> _document;

  @override
  void initState() {
    super.initState();
    _document = ApiService.instance.downloadOriginalReport(widget.reportId);
  }

  void _retry() {
    setState(() {
      _document = ApiService.instance.downloadOriginalReport(widget.reportId);
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final l10n = AppLocalizations.of(context)!;
    final isPdf = widget.fileName.toLowerCase().endsWith('.pdf');
    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(l10n.originalReportTitle),
            if (widget.fileName.isNotEmpty)
              Text(
                widget.fileName,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w400,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.60),
                ),
              ),
          ],
        ),
      ),
      body: FutureBuilder<Uint8List>(
        future: _document,
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 56,
                      height: 56,
                      decoration: BoxDecoration(
                        color: theme.colorScheme.error.withValues(alpha: 0.10),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(Icons.error_outline_rounded,
                          color: theme.colorScheme.error, size: 28),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      l10n.unableToOpenOriginal,
                      textAlign: TextAlign.center,
                      style: theme.textTheme.bodyMedium,
                    ),
                    const SizedBox(height: 16),
                    FilledButton.tonalIcon(
                      onPressed: _retry,
                      icon: const Icon(Icons.refresh_rounded, size: 18),
                      label: Text(l10n.retry),
                    ),
                  ],
                ),
              ),
            );
          }
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final bytes = snapshot.data!;
          return Column(
            children: [
              Container(
                margin: const EdgeInsets.fromLTRB(16, 4, 16, 12),
                padding:
                    const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                decoration: BoxDecoration(
                  color: theme.colorScheme.primary.withValues(alpha: 0.07),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.info_outline_rounded,
                        size: 18, color: theme.colorScheme.primary),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        l10n.compareAiFindings,
                        style: TextStyle(
                          fontSize: 13,
                          height: 1.4,
                          color: theme.colorScheme.onSurface
                              .withValues(alpha: 0.75),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: ClipRRect(
                  borderRadius:
                      const BorderRadius.vertical(top: Radius.circular(20)),
                  child: isPdf
                      ? PdfPreview(
                          build: (_) async => bytes,
                          pdfFileName: widget.fileName,
                          allowPrinting: true,
                          allowSharing: false,
                          canChangePageFormat: false,
                          canChangeOrientation: false,
                          canDebug: false,
                          maxPageWidth: 760,
                          previewPageMargin: const EdgeInsets.all(12),
                          scrollViewDecoration: BoxDecoration(
                            color: theme.colorScheme.onSurface
                                .withValues(alpha: 0.06),
                          ),
                          actionBarTheme: PdfActionBarTheme(
                            backgroundColor: theme.colorScheme.primary,
                            iconColor: Colors.white,
                            height: 52,
                          ),
                        )
                      : Container(
                          color: theme.colorScheme.onSurface
                              .withValues(alpha: 0.06),
                          child: InteractiveViewer(
                            minScale: 0.5,
                            maxScale: 5,
                            child: Center(child: Image.memory(bytes)),
                          ),
                        ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
