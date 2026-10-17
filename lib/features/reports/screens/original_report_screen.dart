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
    final isPdf = widget.fileName.toLowerCase().endsWith('.pdf');
    return Scaffold(
      appBar: AppBar(title: Text(AppLocalizations.of(context)!.originalReportTitle)),
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
                    Text(AppLocalizations.of(context)!.unableToOpenOriginal),
                    const SizedBox(height: 12),
                    OutlinedButton(
                        onPressed: _retry, child: Text(AppLocalizations.of(context)!.retry)),
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
              Padding(
                padding: const EdgeInsets.all(12),
                child: Text(
                  AppLocalizations.of(context)!.compareAiFindings,
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ),
              Expanded(
                child: isPdf
                    ? PdfPreview(
                        build: (_) async => bytes,
                        pdfFileName: widget.fileName,
                        allowPrinting: true,
                        allowSharing: false,
                      )
                    : InteractiveViewer(
                        minScale: 0.5,
                        maxScale: 5,
                        child: Center(child: Image.memory(bytes)),
                      ),
              ),
            ],
          );
        },
      ),
    );
  }
}
