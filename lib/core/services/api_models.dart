// Models used by the API layer.
// Follows the exact same pattern as report_model.dart:
// const constructor, copyWith, toMap/fromMap, no external serialization package.

class AuthTokens {
  final String accessToken;
  final String refreshToken;

  const AuthTokens({required this.accessToken, required this.refreshToken});

  factory AuthTokens.fromMap(Map<String, dynamic> map) {
    return AuthTokens(
      accessToken: map['access_token'] as String,
      refreshToken: map['refresh_token'] as String,
    );
  }
}

class UserModel {
  final String id;
  final String email;
  final String fullName;
  final String role;
  final String preferredLanguage;
  final String? dateOfBirth;
  final String? gender;
  final bool isActive;
  final MedicalProfileModel? medicalProfile;

  const UserModel({
    required this.id,
    required this.email,
    required this.fullName,
    required this.role,
    required this.preferredLanguage,
    this.dateOfBirth,
    this.gender,
    required this.isActive,
    this.medicalProfile,
  });

  UserModel copyWith({
    String? id,
    String? email,
    String? fullName,
    String? role,
    String? preferredLanguage,
    String? dateOfBirth,
    String? gender,
    bool? isActive,
    MedicalProfileModel? medicalProfile,
  }) {
    return UserModel(
      id: id ?? this.id,
      email: email ?? this.email,
      fullName: fullName ?? this.fullName,
      role: role ?? this.role,
      preferredLanguage: preferredLanguage ?? this.preferredLanguage,
      dateOfBirth: dateOfBirth ?? this.dateOfBirth,
      gender: gender ?? this.gender,
      isActive: isActive ?? this.isActive,
      medicalProfile: medicalProfile ?? this.medicalProfile,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'email': email,
      'full_name': fullName,
      'role': role,
      'preferred_language': preferredLanguage,
      'date_of_birth': dateOfBirth,
      'gender': gender,
      'is_active': isActive,
    };
  }

  factory UserModel.fromMap(Map<String, dynamic> map) {
    return UserModel(
      id: map['id'] as String,
      email: map['email'] as String,
      fullName: map['full_name'] as String,
      role: map['role'] as String? ?? 'patient',
      preferredLanguage: map['preferred_language'] as String? ?? 'en',
      dateOfBirth: map['date_of_birth'] as String?,
      gender: map['gender'] as String?,
      isActive: map['is_active'] as bool? ?? true,
      medicalProfile: map['medical_profile'] != null
          ? MedicalProfileModel.fromMap(map['medical_profile'] as Map<String, dynamic>)
          : null,
    );
  }
}

class MedicalProfileModel {
  final String? bloodGroup;
  final String? knownAllergies;
  final String? chronicConditions;
  final String? emergencyContactName;
  final String? emergencyContactPhone;

  const MedicalProfileModel({
    this.bloodGroup,
    this.knownAllergies,
    this.chronicConditions,
    this.emergencyContactName,
    this.emergencyContactPhone,
  });

  MedicalProfileModel copyWith({
    String? bloodGroup,
    String? knownAllergies,
    String? chronicConditions,
    String? emergencyContactName,
    String? emergencyContactPhone,
  }) {
    return MedicalProfileModel(
      bloodGroup: bloodGroup ?? this.bloodGroup,
      knownAllergies: knownAllergies ?? this.knownAllergies,
      chronicConditions: chronicConditions ?? this.chronicConditions,
      emergencyContactName: emergencyContactName ?? this.emergencyContactName,
      emergencyContactPhone: emergencyContactPhone ?? this.emergencyContactPhone,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'blood_group': bloodGroup,
      'known_allergies': knownAllergies,
      'chronic_conditions': chronicConditions,
      'emergency_contact_name': emergencyContactName,
      'emergency_contact_phone': emergencyContactPhone,
    };
  }

  factory MedicalProfileModel.fromMap(Map<String, dynamic> map) {
    return MedicalProfileModel(
      bloodGroup: map['blood_group'] as String?,
      knownAllergies: map['known_allergies'] as String?,
      chronicConditions: map['chronic_conditions'] as String?,
      emergencyContactName: map['emergency_contact_name'] as String?,
      emergencyContactPhone: map['emergency_contact_phone'] as String?,
    );
  }
}

class ReportStatus {
  final String processingStatus;
  final String? errorReason;

  const ReportStatus({required this.processingStatus, this.errorReason});

  factory ReportStatus.fromMap(Map<String, dynamic> map) {
    return ReportStatus(
      processingStatus: map['processing_status'] as String,
      errorReason: map['error_reason'] as String?,
    );
  }
}

class LabValue {
  final String testName;
  final double value;
  final String unit;
  final double? refLow;
  final double? refHigh;
  final String flag;

  const LabValue({
    required this.testName,
    required this.value,
    required this.unit,
    this.refLow,
    this.refHigh,
    required this.flag,
  });

  factory LabValue.fromMap(Map<String, dynamic> map) {
    return LabValue(
      testName: map['test_name'] as String,
      value: (map['value'] as num).toDouble(),
      unit: map['unit'] as String? ?? '',
      refLow: map['ref_low'] != null ? (map['ref_low'] as num).toDouble() : null,
      refHigh: map['ref_high'] != null ? (map['ref_high'] as num).toDouble() : null,
      flag: map['flag'] as String? ?? 'normal',
    );
  }
}

class EvidenceSource {
  final String finding;
  final List<String> chunkIds;
  final List<String> sources;

  const EvidenceSource({
    required this.finding,
    required this.chunkIds,
    required this.sources,
  });

  factory EvidenceSource.fromMap(Map<String, dynamic> map) {
    return EvidenceSource(
      finding: map['finding'] as String,
      chunkIds: List<String>.from(map['chunk_ids'] ?? []),
      sources: List<String>.from(map['sources'] ?? []),
    );
  }
}

class ReportAnalysisModel {
  final String id;
  final String reportId;
  final List<LabValue> structuredLabValues;
  final List<Map<String, dynamic>> entities;
  final List<Map<String, dynamic>> abnormalFindings;
  final List<EvidenceSource> evidenceSources;
  final String? clinicianSummary;
  final String? patientSummary;
  final String? translatedPatientSummary;
  final bool translationAvailable;
  final String? errorReason;
  final DateTime? processedAt;

  const ReportAnalysisModel({
    required this.id,
    required this.reportId,
    required this.structuredLabValues,
    required this.entities,
    required this.abnormalFindings,
    required this.evidenceSources,
    this.clinicianSummary,
    this.patientSummary,
    this.translatedPatientSummary,
    this.translationAvailable = false,
    this.errorReason,
    this.processedAt,
  });

  factory ReportAnalysisModel.fromMap(Map<String, dynamic> map) {
    return ReportAnalysisModel(
      id: map['id'] as String,
      reportId: map['report_id'] as String,
      structuredLabValues: (map['structured_lab_values'] as List<dynamic>? ?? [])
          .map((e) => LabValue.fromMap(e as Map<String, dynamic>))
          .toList(),
      entities: List<Map<String, dynamic>>.from(map['entities'] ?? []),
      abnormalFindings: List<Map<String, dynamic>>.from(map['abnormal_findings'] ?? []),
      evidenceSources: (map['evidence_sources'] as List<dynamic>? ?? [])
          .map((e) => EvidenceSource.fromMap(e as Map<String, dynamic>))
          .toList(),
      clinicianSummary: map['clinician_summary'] as String?,
      patientSummary: map['patient_summary'] as String?,
      translatedPatientSummary: map['translated_patient_summary'] as String?,
      translationAvailable: map['translation_available'] as bool? ?? false,
      errorReason: map['error_reason'] as String?,
      processedAt: map['processed_at'] != null
          ? DateTime.tryParse(map['processed_at'] as String)
          : null,
    );
  }
}

class TranslationModel {
  final String language;
  final String patientSummary;
  final List<Map<String, dynamic>> findingsJson;

  const TranslationModel({
    required this.language,
    required this.patientSummary,
    required this.findingsJson,
  });

  factory TranslationModel.fromMap(Map<String, dynamic> map) {
    return TranslationModel(
      language: map['language'] as String,
      patientSummary: map['patient_summary'] as String,
      findingsJson: List<Map<String, dynamic>>.from(map['findings_json'] ?? []),
    );
  }
}

class ComparePoint {
  final String reportId;
  final DateTime reportDate;
  final double value;
  final String unit;
  final String flag;

  const ComparePoint({
    required this.reportId,
    required this.reportDate,
    required this.value,
    required this.unit,
    required this.flag,
  });

  factory ComparePoint.fromMap(Map<String, dynamic> map) {
    return ComparePoint(
      reportId: map['report_id'] as String,
      reportDate: DateTime.parse(map['report_date'] as String),
      value: (map['value'] as num).toDouble(),
      unit: map['unit'] as String? ?? '',
      flag: map['flag'] as String? ?? 'normal',
    );
  }
}

class ComparePreviousResult {
  final bool comparable;
  final String? reason;
  final String? previousReportId;
  final List<Map<String, dynamic>> comparedFindings;
  final String? narrativeSummary;

  const ComparePreviousResult({
    required this.comparable,
    this.reason,
    this.previousReportId,
    required this.comparedFindings,
    this.narrativeSummary,
  });

  factory ComparePreviousResult.fromMap(Map<String, dynamic> map) {
    return ComparePreviousResult(
      comparable: map['comparable'] as bool,
      reason: map['reason'] as String?,
      previousReportId: map['previous_report_id'] as String?,
      comparedFindings: List<Map<String, dynamic>>.from(map['compared_findings'] ?? []),
      narrativeSummary: map['narrative_summary'] as String?,
    );
  }
}

class ChatSessionModel {
  final String id;
  final String userId;
  final String? reportId;
  final String? title;
  final DateTime createdAt;

  const ChatSessionModel({
    required this.id,
    required this.userId,
    this.reportId,
    this.title,
    required this.createdAt,
  });

  factory ChatSessionModel.fromMap(Map<String, dynamic> map) {
    return ChatSessionModel(
      id: map['id'] as String,
      userId: map['user_id'] as String,
      reportId: map['report_id'] as String?,
      title: map['title'] as String?,
      createdAt: DateTime.parse(map['created_at'] as String),
    );
  }
}

class ChatMessageModel {
  final String id;
  final String chatSessionId;
  final String role;
  final String content;
  final DateTime createdAt;
  final List<Map<String, dynamic>> sources;

  const ChatMessageModel({
    required this.id,
    required this.chatSessionId,
    required this.role,
    required this.content,
    required this.createdAt,
    this.sources = const [],
  });

  factory ChatMessageModel.fromMap(Map<String, dynamic> map) {
    return ChatMessageModel(
      id: map['id'] as String,
      chatSessionId: map['chat_session_id'] as String,
      role: map['role'] as String,
      content: map['content'] as String,
      createdAt: DateTime.parse(map['created_at'] as String),
      sources: List<Map<String, dynamic>>.from(map['sources'] ?? []),
    );
  }
}
