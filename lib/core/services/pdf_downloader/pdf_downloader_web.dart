// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'dart:typed_data';

Future<void> downloadPdfWeb(Uint8List bytes, String filename) async {
  print('[MEDNARRATE EXPORT] STARTING BROWSER DOWNLOAD');
  final blob = html.Blob([bytes], 'application/pdf');
  final url = html.Url.createObjectUrlFromBlob(blob);
  
  html.AnchorElement(href: url)
    ..setAttribute('download', filename)
    ..click();
    
  html.Url.revokeObjectUrl(url);
  print('[MEDNARRATE EXPORT] DOWNLOAD TRIGGERED');
}
