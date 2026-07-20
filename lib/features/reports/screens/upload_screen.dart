import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';

import '../models/report_model.dart';
import '../services/pdf_service.dart';
import '../services/report_service.dart';

class UploadScreen extends StatefulWidget {
  const UploadScreen({super.key});

  @override
  State<UploadScreen> createState() =>
      _UploadScreenState();
}

class _UploadScreenState
    extends State<UploadScreen> {
  PlatformFile? selectedFile;

  bool isLoading = false;

  String? errorMessage;

  final ReportService reportService =
      ReportService.instance;

  Future<void> pickPdf() async {
    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    final file =
        await PdfService.instance.pickPdf();

    if (file == null) {
      setState(() {
        isLoading = false;
      });

      return;
    }

    if (!PdfService.instance.validatePdf(file)) {
      setState(() {
        errorMessage =
            "Please select a valid PDF smaller than 25 MB.";
        isLoading = false;
      });

      return;
    }

    setState(() {
      selectedFile = file;
      isLoading = false;
    });
  }

  Future<void> saveReport() async {
    if (selectedFile == null) return;

    final report = ReportModel(
      id: const Uuid().v4(),
      title: selectedFile!.name.replaceAll(
        ".pdf",
        "",
      ),
      hospital: "Unknown Hospital",
      reportDate: DateTime.now(),
      fileName: selectedFile!.name,
      filePath: selectedFile!.path ?? "",
      fileType: "pdf",
      reportType: "Medical Report",
      extractedText: "",
      isFavourite: false,
      uploadedAt: DateTime.now(),
    );

    reportService.addReport(report);

    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          "Report uploaded successfully.",
        ),
      ),
    );

    Navigator.pop(context, true);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Upload Report"),
      ),

      body: Padding(
        padding: const EdgeInsets.all(20),

        child: Column(
          children: [           
             Container(
              width: 140,
              height: 140,
              decoration: BoxDecoration(
                color: Colors.red.withValues(
                  alpha: .12,
                ),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.picture_as_pdf,
                color: Colors.red,
                size: 70,
              ),
            ),

            const SizedBox(height: 30),

            const Text(
              "Upload Medical Report",
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 8),

            const Text(
              "Choose a PDF report from your device.",
              textAlign: TextAlign.center,
            ),

            const SizedBox(height: 30),

            SizedBox(
              width: double.infinity,
              height: 55,
              child: FilledButton.icon(
                onPressed:
                    isLoading ? null : pickPdf,
                icon:
                    const Icon(Icons.upload_file),
                label: Text(
                  isLoading
                      ? "Opening..."
                      : "Choose PDF",
                ),
              ),
            ),

            const SizedBox(height: 25),

            if (selectedFile != null)
              Card(
                child: ListTile(
                  leading: const Icon(
                    Icons.picture_as_pdf,
                    color: Colors.red,
                  ),

                  title: Text(
                    selectedFile!.name,
                  ),

                  subtitle: Text(
                    "${PdfService.instance.fileSizeMB(selectedFile!).toStringAsFixed(2)} MB",
                  ),
                ),
              ),

            if (errorMessage != null)
              Padding(
                padding:
                    const EdgeInsets.only(top: 20),
                child: Text(
                  errorMessage!,
                  style: const TextStyle(
                    color: Colors.red,
                  ),
                ),
              ),

            const Spacer(),

            SizedBox(
              width: double.infinity,
              height: 55,
              child: FilledButton(
                onPressed:
                    selectedFile == null
                        ? null
                        : saveReport,
                child: const Text(
                  "Continue",
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}