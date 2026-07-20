import 'package:file_picker/file_picker.dart';

class PdfService {
  PdfService._();

  static final PdfService instance = PdfService._();

  Future<PlatformFile?> pickPdf() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
      withData: false,
    );

    if (result == null) {
      return null;
    }

    return result.files.first;
  }

  bool validatePdf(PlatformFile file) {
    if (file.extension?.toLowerCase() != "pdf") {
      return false;
    }

    if (file.size > 25 * 1024 * 1024) {
      return false;
    }

    return true;
  }

  String fileName(PlatformFile file) {
    return file.name;
  }

  String filePath(PlatformFile file) {
    return file.path ?? "";
  }

  double fileSizeMB(PlatformFile file) {
    return file.size / (1024 * 1024);
  }

  String fileExtension(PlatformFile file) {
    return file.extension ?? "";
  }
}