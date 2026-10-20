import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:path_provider/path_provider.dart';

/// The small set of operations MedNarrate needs from encrypted storage.
abstract class SecureStore {
  Future<String?> read({required String key});
  Future<void> write({required String key, required String? value});
  Future<void> delete({required String key});
}

/// Phones, tablets and release builds: the system Keychain / Keystore.
class _KeychainSecureStore implements SecureStore {
  const _KeychainSecureStore(this._storage);

  final FlutterSecureStorage _storage;

  @override
  Future<String?> read({required String key}) => _storage.read(key: key);

  @override
  Future<void> write({required String key, required String? value}) =>
      _storage.write(key: key, value: value);

  @override
  Future<void> delete({required String key}) => _storage.delete(key: key);
}

/// Mac builds that are run from the developer's machine (`flutter run`).
///
/// Those builds are signed with a new throw-away identity on every rebuild, so
/// the macOS login Keychain asks for the Mac password again for every stored
/// value, every time. To stop that, development runs on macOS keep these values
/// in a file inside the app's own container instead. Release builds, iOS and
/// Android never use this class.
class _DevFileSecureStore implements SecureStore {
  Map<String, String>? _cache;
  Future<void> _tail = Future<void>.value();

  Future<File> _file() async {
    final dir = await getApplicationSupportDirectory();
    return File('${dir.path}/mednarrate_dev_secure_store.json');
  }

  Future<Map<String, String>> _load() async {
    final cached = _cache;
    if (cached != null) return cached;
    var data = <String, String>{};
    try {
      final file = await _file();
      if (await file.exists()) {
        final decoded = jsonDecode(await file.readAsString());
        if (decoded is Map) {
          data = decoded.map((k, v) => MapEntry(k.toString(), v.toString()));
        }
      }
    } catch (error) {
      debugPrint('Dev secure store could not be read, starting empty: $error');
    }
    _cache = data;
    return data;
  }

  Future<void> _save(Map<String, String> data) async {
    final file = await _file();
    await file.parent.create(recursive: true);
    await file.writeAsString(jsonEncode(data));
    try {
      await Process.run('chmod', ['600', file.path]);
    } catch (_) {
      // Best effort: the file already lives in the app's private container.
    }
  }

  /// Runs [action] after every earlier call has finished, so two writes never
  /// overwrite each other.
  Future<T> _locked<T>(Future<T> Function() action) {
    final run = _tail.then((_) => action());
    _tail = run.then((_) {}, onError: (_) {});
    return run;
  }

  @override
  Future<String?> read({required String key}) =>
      _locked(() async => (await _load())[key]);

  @override
  Future<void> write({required String key, required String? value}) =>
      _locked(() async {
        final data = await _load();
        if (value == null) {
          data.remove(key);
        } else {
          data[key] = value;
        }
        await _save(data);
      });

  @override
  Future<void> delete({required String key}) => write(key: key, value: null);
}

bool get _isMacDevelopmentRun =>
    !kIsWeb &&
    Platform.isMacOS &&
    !kReleaseMode &&
    // `flutter test` keeps using the (mocked) Keychain path.
    !Platform.environment.containsKey('FLUTTER_TEST');

/// The encrypted storage shared by all native MedNarrate data.
///
/// One shared instance keeps a background service from silently using
/// different settings than the login service.
final SecureStore appSecureStorage = _isMacDevelopmentRun
    ? _DevFileSecureStore()
    : const _KeychainSecureStore(FlutterSecureStorage(
        aOptions: AndroidOptions(),
        iOptions: IOSOptions(accessibility: KeychainAccessibility.first_unlock),
        mOptions: MacOsOptions(usesDataProtectionKeychain: false),
      ));
