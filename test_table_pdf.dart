import 'dart:io';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

void main() async {
  final doc = pw.Document();

  doc.addPage(
    pw.MultiPage(
      pageFormat: PdfPageFormat.a4,
      build: (context) => [
        pw.TableHelper.fromTextArray(
          headers: ['A', 'B'],
          data: List.generate(50, (i) => ['Row $i A', 'Row $i B']),
        ),
      ],
    ),
  );

  try {
    final bytes = await doc.save();
    File('test_output.pdf').writeAsBytesSync(bytes);
    print("Table span test: Success!");
  } catch (e) {
    print("Table span test Error: $e");
  }
}
