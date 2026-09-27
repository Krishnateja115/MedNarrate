// Web implementation of the PDF download trigger. Uses package:web +
// dart:js_interop (Dart's supported successor to dart:html) so this stays
// compatible with modern Dart web output.
import 'dart:js_interop';

import 'package:flutter/foundation.dart';
import 'package:web/web.dart' as web;

Future<void> downloadPdfWeb(Uint8List bytes, String filename) async {
  debugPrint('[MEDNARRATE EXPORT] STARTING BROWSER DOWNLOAD');

  final blob = web.Blob(
    [bytes.toJS].toJS,
    web.BlobPropertyBag(type: 'application/pdf'),
  );
  final url = web.URL.createObjectURL(blob);

  // Same pattern the previous dart:html version used: trigger the download
  // via a detached anchor's click(), without ever attaching it to the DOM.
  web.HTMLAnchorElement()
    ..href = url
    ..download = filename
    ..click();

  web.URL.revokeObjectURL(url);
  debugPrint('[MEDNARRATE EXPORT] DOWNLOAD TRIGGERED');
}
