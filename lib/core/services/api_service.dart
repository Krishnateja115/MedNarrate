import 'dart:convert';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'api_exception.dart';
import 'api_models.dart';
import 'storage_service.dart';
import '../../../features/reports/models/report_model.dart';

/// ApiService — singleton HTTP client that handles auth headers, 401 retry with token
/// refresh, and uniform ApiException wrapping.
///
/// Base URL notes:
///   - Android emulator → 10.0.2.2:8000 (host loopback)
///   - iOS simulator   → localhost:8000
///   - Real device     → use your machine's LAN IP, e.g. 192.168.x.x:8000
class ApiService {
  ApiService._();
  static final ApiService instance = ApiService._();

  static String get _baseUrl {
    const envUrl = String.fromEnvironment('API_BASE_URL', defaultValue: '');
    if (envUrl.isNotEmpty) return envUrl;
    if (kIsWeb) return 'http://localhost:8000/api/v1';
    return 'http://10.0.2.2:8000/api/v1';
  }

  // ─────────────────────── internal HTTP helpers ───────────────────────

  Future<Map<String, String>> _authHeaders() async {
    final token = await StorageService.instance.getAccessToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  Future<http.Response> _get(String path) async {
    final resp = await http.get(
      Uri.parse('$_baseUrl$path'),
      headers: await _authHeaders(),
    );
    return _handleResponse(resp, () => _get(path));
  }

  Future<http.Response> _post(String path, {Object? body, bool isJson = true}) async {
    final headers = await _authHeaders();
    final resp = await http.post(
      Uri.parse('$_baseUrl$path'),
      headers: headers,
      body: isJson ? jsonEncode(body) : body,
    );
    return _handleResponse(resp, () => _post(path, body: body, isJson: isJson));
  }

  Future<http.Response> _patch(String path, {Object? body}) async {
    final headers = await _authHeaders();
    final resp = await http.patch(
      Uri.parse('$_baseUrl$path'),
      headers: headers,
      body: jsonEncode(body),
    );
    return _handleResponse(resp, () => _patch(path, body: body));
  }

  Future<http.Response> _delete(String path) async {
    final resp = await http.delete(
      Uri.parse('$_baseUrl$path'),
      headers: await _authHeaders(),
    );
    return _handleResponse(resp, () => _delete(path));
  }

  bool _retrying = false;

  /// If the response is 401 and we haven't already retried, attempt a token
  /// refresh and retry the original request once. On double-failure, clears
  /// tokens and throws [UnauthorizedException].
  Future<http.Response> _handleResponse(
    http.Response resp,
    Future<http.Response> Function() retry,
  ) async {
    if (resp.statusCode == 401 && !_retrying) {
      _retrying = true;
      try {
        await refresh();
        final retried = await retry();
        _retrying = false;
        return retried;
      } catch (_) {
        _retrying = false;
        await StorageService.instance.clearTokens();
        throw const UnauthorizedException();
      }
    }
    _retrying = false;
    if (resp.statusCode >= 400) {
      String message = resp.reasonPhrase ?? 'Unknown error';
      try {
        final decoded = jsonDecode(resp.body) as Map<String, dynamic>;
        message = decoded['detail']?.toString() ?? message;
      } catch (_) {}
      throw ApiException(resp.statusCode, message);
    }
    return resp;
  }

  // ─────────────────────────── Auth ────────────────────────────────────

  Future<AuthTokens> signup(
      String email, String password, String fullName) async {
    await _post('/auth/signup', body: {
      'email': email,
      'password': password,
      'full_name': fullName,
    });
    // signup returns UserOut; then we log in to get tokens
    await login(email, password);
    return await login(email, password);
  }

  Future<AuthTokens> login(String email, String password) async {
    // OAuth2PasswordRequestForm requires form-encoded body
    final resp = await http.post(
      Uri.parse('$_baseUrl/auth/login'),
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: 'username=${Uri.encodeComponent(email)}&password=${Uri.encodeComponent(password)}',
    );
    if (resp.statusCode >= 400) {
      String message = resp.reasonPhrase ?? 'Login failed';
      try {
        final decoded = jsonDecode(resp.body) as Map<String, dynamic>;
        message = decoded['detail']?.toString() ?? message;
      } catch (_) {}
      throw ApiException(resp.statusCode, message);
    }
    final data = jsonDecode(resp.body) as Map<String, dynamic>;
    final tokens = AuthTokens.fromMap(data);
    await StorageService.instance.saveTokens(tokens.accessToken, tokens.refreshToken);
    return tokens;
  }

  Future<void> refresh() async {
    final refreshToken = await StorageService.instance.getRefreshToken();
    if (refreshToken == null) throw const UnauthorizedException();
    final resp = await http.post(
      Uri.parse('$_baseUrl/auth/refresh'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'refresh_token': refreshToken}),
    );
    if (resp.statusCode >= 400) throw const UnauthorizedException();
    final data = jsonDecode(resp.body) as Map<String, dynamic>;
    await StorageService.instance.saveTokens(
      data['access_token'] as String,
      data['refresh_token'] as String,
    );
  }

  Future<void> logout() async {
    final refreshToken = await StorageService.instance.getRefreshToken();
    if (refreshToken != null) {
      try {
        await _post('/auth/logout', body: {'refresh_token': refreshToken});
      } catch (_) {}
    }
    await StorageService.instance.clearTokens();
  }

  Future<Map<String, dynamic>> forgotPassword(String email) async {
    final resp = await http.post(
      Uri.parse('$_baseUrl/auth/forgot-password'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email}),
    );
    if (resp.statusCode >= 400) {
      String message = resp.reasonPhrase ?? 'Error';
      try {
        final d = jsonDecode(resp.body) as Map<String, dynamic>;
        message = d['detail']?.toString() ?? message;
      } catch (_) {}
      throw ApiException(resp.statusCode, message);
    }
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  Future<void> resetPassword({required String token, required String newPassword}) async {
    final resp = await http.post(
      Uri.parse('$_baseUrl/auth/reset-password'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'token': token, 'new_password': newPassword}),
    );
    if (resp.statusCode >= 400) {
      String message = resp.reasonPhrase ?? 'Error';
      try {
        final d = jsonDecode(resp.body) as Map<String, dynamic>;
        message = d['detail']?.toString() ?? message;
      } catch (_) {}
      throw ApiException(resp.statusCode, message);
    }
  }

  Future<UserModel> getMe() async {
    final resp = await _get('/auth/me');
    return UserModel.fromMap(jsonDecode(resp.body) as Map<String, dynamic>);
  }

  Future<UserModel> updateMe({
    String? fullName,
    String? preferredLanguage,
    String? dateOfBirth,
    String? gender,
    String? role,
    String? bloodGroup,
    String? knownAllergies,
    String? chronicConditions,
    String? emergencyContactName,
    String? emergencyContactPhone,
  }) async {
    final body = <String, dynamic>{};
    if (fullName != null) body['full_name'] = fullName;
    if (preferredLanguage != null) body['preferred_language'] = preferredLanguage;
    if (dateOfBirth != null) body['date_of_birth'] = dateOfBirth;
    if (gender != null) body['gender'] = gender;
    if (role != null) body['role'] = role;
    if (bloodGroup != null || knownAllergies != null || chronicConditions != null ||
        emergencyContactName != null || emergencyContactPhone != null) {
      final medicalProfile = <String, dynamic>{};
      if (bloodGroup != null) medicalProfile['blood_group'] = bloodGroup;
      if (knownAllergies != null) medicalProfile['known_allergies'] = knownAllergies;
      if (chronicConditions != null) medicalProfile['chronic_conditions'] = chronicConditions;
      if (emergencyContactName != null) medicalProfile['emergency_contact_name'] = emergencyContactName;
      if (emergencyContactPhone != null) medicalProfile['emergency_contact_phone'] = emergencyContactPhone;
      body['medical_profile'] = medicalProfile;
    }
    final resp = await _patch('/users/me', body: body);
    return UserModel.fromMap(jsonDecode(resp.body) as Map<String, dynamic>);
  }

  // ─────────────────────────── Reports ─────────────────────────────────

  Future<ReportModel> uploadReport({
    required PlatformFile file,
    required String title,
    String? hospital,
    required String reportDate,
    required String reportType,
  }) async {
    final token = await StorageService.instance.getAccessToken();
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$_baseUrl/reports/upload'),
    );
    request.headers['Authorization'] = 'Bearer $token';
    request.fields['title'] = title;
    request.fields['report_date'] = reportDate;
    request.fields['report_type'] = reportType;
    if (hospital != null) request.fields['hospital'] = hospital;
    
    if (kIsWeb) {
      request.files.add(http.MultipartFile.fromBytes('file', file.bytes!, filename: file.name));
    } else {
      request.files.add(await http.MultipartFile.fromPath('file', file.path!));
    }
    final streamedResponse = await request.send();
    final resp = await http.Response.fromStream(streamedResponse);
    if (resp.statusCode >= 400) {
      String message = 'Upload failed';
      try {
        final decoded = jsonDecode(resp.body) as Map<String, dynamic>;
        message = decoded['detail']?.toString() ?? message;
      } catch (_) {}
      throw ApiException(resp.statusCode, message);
    }
    return ReportModel.fromMap(_remapReport(
        jsonDecode(resp.body) as Map<String, dynamic>));
  }

  Future<List<ReportModel>> listReports({
    int limit = 10,
    int offset = 0,
    String? reportType,
    bool? isFavourite,
    String? search,
  }) async {
    final params = <String, String>{
      'limit': limit.toString(),
      'offset': offset.toString(),
    };
    if (reportType != null) params['report_type'] = reportType;
    if (isFavourite != null) params['is_favourite'] = isFavourite.toString();
    if (search != null) params['search'] = search;
    final uri = Uri.parse('$_baseUrl/reports').replace(queryParameters: params);
    final resp = await http.get(uri, headers: await _authHeaders());
    await _handleResponse(resp, () => listReports(
        limit: limit, offset: offset, reportType: reportType,
        isFavourite: isFavourite, search: search)
        .then((_) => throw const UnauthorizedException()));
    final list = jsonDecode(resp.body) as List<dynamic>;
    return list
        .map((e) => ReportModel.fromMap(_remapReport(e as Map<String, dynamic>)))
        .toList();
  }

  Future<ReportModel> getReport(String id) async {
    final resp = await _get('/reports/$id');
    return ReportModel.fromMap(
        _remapReport(jsonDecode(resp.body) as Map<String, dynamic>));
  }

  Future<ReportModel> patchReport(String id,
      {String? title, bool? isFavourite}) async {
    final body = <String, dynamic>{};
    if (title != null) body['title'] = title;
    if (isFavourite != null) body['is_favourite'] = isFavourite;
    final resp = await _patch('/reports/$id', body: body);
    return ReportModel.fromMap(
        _remapReport(jsonDecode(resp.body) as Map<String, dynamic>));
  }

  Future<void> deleteReport(String id) async {
    await _delete('/reports/$id');
  }

  Future<void> processReport(String id, {bool force = false}) async {
    await _post('/reports/$id/process${force ? '?force=true' : ''}');
  }

  Future<ReportStatus> getReportStatus(String id) async {
    final resp = await _get('/reports/$id/status');
    return ReportStatus.fromMap(jsonDecode(resp.body) as Map<String, dynamic>);
  }

  Future<ReportAnalysisModel> getReportAnalysis(String id) async {
    final resp = await _get('/reports/$id/analysis');
    return ReportAnalysisModel.fromMap(
        jsonDecode(resp.body) as Map<String, dynamic>);
  }

  Future<TranslationModel> translateAnalysis(
      String id, String language) async {
    final resp = await _post('/reports/$id/analysis/translate',
        body: {'language': language});
    return TranslationModel.fromMap(
        jsonDecode(resp.body) as Map<String, dynamic>);
  }

  Future<List<ComparePoint>> compareReports(String testName,
      {int limit = 10}) async {
    final resp = await _get('/reports/compare?test_name=${Uri.encodeComponent(testName)}&limit=$limit');
    final list = jsonDecode(resp.body) as List<dynamic>;
    return list
        .map((e) => ComparePoint.fromMap(e as Map<String, dynamic>))
        .toList();
  }

  Future<ComparePreviousResult> comparePrevious(String id) async {
    final resp = await _get('/reports/$id/compare-previous');
    return ComparePreviousResult.fromMap(
        jsonDecode(resp.body) as Map<String, dynamic>);
  }

  // ─────────────────────────── Chat ────────────────────────────────────

  Future<ChatSessionModel> createChatSession(
      {String? reportId, String? title}) async {
    final sessionBody = <String, dynamic>{};
    if (reportId != null) sessionBody['report_id'] = reportId;
    if (title != null) sessionBody['title'] = title;
    final resp = await _post('/chat/sessions', body: sessionBody);
    return ChatSessionModel.fromMap(
        jsonDecode(resp.body) as Map<String, dynamic>);
  }

  Future<List<ChatSessionModel>> listChatSessions() async {
    final resp = await _get('/chat/sessions');
    final list = jsonDecode(resp.body) as List<dynamic>;
    return list
        .map((e) => ChatSessionModel.fromMap(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<ChatMessageModel>> getChatMessages(String sessionId,
      {int limit = 20, int offset = 0}) async {
    final resp =
        await _get('/chat/sessions/$sessionId/messages?limit=$limit&offset=$offset');
    final list = jsonDecode(resp.body) as List<dynamic>;
    return list
        .map((e) => ChatMessageModel.fromMap(e as Map<String, dynamic>))
        .toList();
  }

  Future<ChatMessageModel> sendChatMessage(
      String sessionId, String content) async {
    final resp = await _post('/chat/sessions/$sessionId/messages',
        body: {'content': content});
    final data = jsonDecode(resp.body) as Map<String, dynamic>;
    // Response is {message: {...}, sources: [...]}
    final msgMap = data['message'] as Map<String, dynamic>;
    msgMap['sources'] = data['sources'] ?? [];
    return ChatMessageModel.fromMap(msgMap);
  }

  // ─────────────────────── Key mapping helper ──────────────────────────

  /// The backend uses snake_case. ReportModel.fromMap uses camelCase keys.
  /// This helper remaps the snake_case JSON from the API to the camelCase
  /// keys expected by ReportModel.fromMap.
  ///
  /// snake_case <-> camelCase mapping:
  ///   report_date      <-> reportDate
  ///   file_name        <-> fileName
  ///   file_path        <-> filePath
  ///   file_type        <-> fileType
  ///   report_type      <-> reportType
  ///   extracted_text   <-> extractedText
  ///   is_favourite     <-> isFavourite
  ///   uploaded_at      <-> uploadedAt
  Map<String, dynamic> _remapReport(Map<String, dynamic> m) {
    return {
      'id': m['id'],
      'title': m['title'],
      'hospital': m['hospital'] ?? '',
      'reportDate': m['report_date'],
      'fileName': m['file_name'],
      'filePath': m['file_path'],
      'fileType': m['file_type'],
      'reportType': m['report_type'],
      'extractedText': m['extracted_text'] ?? '',
      'isFavourite': m['is_favourite'] ?? false,
      'uploadedAt': m['uploaded_at'],
    };
  }
}
