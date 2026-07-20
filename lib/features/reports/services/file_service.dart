import 'dart:io';

import 'package:flutter/material.dart';

class FileService {
  FileService._();

  static final FileService instance = FileService._();

  Future<bool> exists(String path) async {
    return File(path).exists();
  }

  Future<File?> getFile(String path) async {
    final file = File(path);

    if (await file.exists()) {
      return file;
    }

    return null;
  }

  Future<void> deleteFile(String path) async {
    final file = File(path);

    if (await file.exists()) {
      await file.delete();
    }
  }

  Future<int> fileSize(String path) async {
    final file = File(path);

    return file.length();
  }

  String readableSize(int bytes) {
    if (bytes < 1024) {
      return "$bytes B";
    }

    if (bytes < 1024 * 1024) {
      return "${(bytes / 1024).toStringAsFixed(1)} KB";
    }

    return "${(bytes / (1024 * 1024)).toStringAsFixed(2)} MB";
  }

  Future<void> showFileNotFound(
    BuildContext context,
  ) async {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          "PDF file not found.",
        ),
      ),
    );
  }
}