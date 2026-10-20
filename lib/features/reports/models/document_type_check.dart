/// Answer of `GET /reports/{id}/document-type`: an experimental hint about
/// which kind of record the report's wording resembles. The server only sends a
/// hint when an admin has turned the feature on and the model is reasonably
/// sure, so a missing or unavailable answer simply means "show nothing".
class DocumentTypeCheck {
  final bool enabled;
  final bool available;
  final String? label; // Blood | Health | TCGA
  final double? confidence; // 0..1

  const DocumentTypeCheck({
    required this.enabled,
    required this.available,
    this.label,
    this.confidence,
  });

  factory DocumentTypeCheck.fromMap(Map<String, dynamic> m) => DocumentTypeCheck(
        enabled: m['enabled'] == true,
        available: m['available'] == true,
        label: m['label'] as String?,
        confidence: (m['confidence'] as num?)?.toDouble(),
      );

  static const hidden = DocumentTypeCheck(enabled: false, available: false);

  bool get isShown =>
      enabled &&
      available &&
      (label == 'Blood' || label == 'Health' || label == 'TCGA') &&
      confidence != null;

  int get percent => ((confidence ?? 0) * 100).round().clamp(0, 100);
}
