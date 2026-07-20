import 'dart:io';

import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';

class OcrService {
  OcrService._();

  static final OcrService instance = OcrService._();

  final TextRecognizer _textRecognizer =
      TextRecognizer(
    script: TextRecognitionScript.latin,
  );

  Future<String> extractText(File image) async {
    try {
      final inputImage =
          InputImage.fromFile(image);

      final RecognizedText recognizedText =
          await _textRecognizer.processImage(
        inputImage,
      );

      return recognizedText.text;
    } catch (e) {
      return "";
    }
  }

  Future<List<String>> extractLines(
    File image,
  ) async {
    try {
      final inputImage =
          InputImage.fromFile(image);

      final RecognizedText recognizedText =
          await _textRecognizer.processImage(
        inputImage,
      );

      return recognizedText.blocks
          .expand((block) => block.lines)
          .map((line) => line.text)
          .toList();
    } catch (e) {
      return [];
    }
  }

  Future<void> dispose() async {
    await _textRecognizer.close();
  }
}