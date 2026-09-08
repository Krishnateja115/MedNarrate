// ignore_for_file: avoid_web_libraries_in_flutter, uri_does_not_exist
import 'dart:js_util' as js_util;
import 'biometric_service.dart';

Future<BiometricAvailability> checkWebAuthnAvailability() async {
  try {
    final jsObj = js_util.getProperty(js_util.globalThis, 'MedNarrateWebAuthn');
    if (jsObj == null) return BiometricAvailability.unsupported;

    final String status = await js_util.promiseToFuture(
      js_util.callMethod(jsObj, 'checkAvailability', [])
    );

    if (status == 'AVAILABLE') {
      return BiometricAvailability.available;
    } else if (status == 'NO_PLATFORM_AUTHENTICATOR') {
      return BiometricAvailability.noPlatformAuthenticator;
    } else {
      return BiometricAvailability.unsupported;
    }
  } catch (_) {
    return BiometricAvailability.unsupported;
  }
}

Future<BiometricResult> authenticateWebAuthn(String reason) async {
  try {
    final jsObj = js_util.getProperty(js_util.globalThis, 'MedNarrateWebAuthn');
    if (jsObj == null) return BiometricResult.unsupported;

    final resObj = await js_util.promiseToFuture(
      js_util.callMethod(jsObj, 'authenticate', [reason])
    );

    final String status = js_util.getProperty(resObj, 'status');

    if (status == 'SUCCESS') {
      return BiometricResult.success;
    } else if (status == 'CANCELLED') {
      return BiometricResult.cancelled;
    } else if (status == 'NOT_CONFIGURED') {
      return BiometricResult.notConfigured;
    } else if (status == 'UNSUPPORTED') {
      return BiometricResult.unsupported;
    } else {
      return BiometricResult.failure;
    }
  } catch (_) {
    return BiometricResult.failure;
  }
}

Future<BiometricResult> verifyCurrentBiometricWebAuthn() async {
  try {
    final jsObj = js_util.getProperty(js_util.globalThis, 'MedNarrateWebAuthn');
    if (jsObj == null) return BiometricResult.unsupported;

    final resObj = await js_util.promiseToFuture(
      js_util.callMethod(jsObj, 'verifyCurrentBiometric', [])
    );

    final String status = js_util.getProperty(resObj, 'status');

    if (status == 'SUCCESS') {
      return BiometricResult.success;
    } else if (status == 'CANCELLED') {
      return BiometricResult.cancelled;
    } else if (status == 'NOT_CONFIGURED') {
      return BiometricResult.notConfigured;
    } else if (status == 'UNSUPPORTED') {
      return BiometricResult.unsupported;
    } else {
      return BiometricResult.failure;
    }
  } catch (_) {
    return BiometricResult.failure;
  }
}

Future<({BiometricResult status, String? credId})> registerNewCredentialWebAuthn() async {
  try {
    final jsObj = js_util.getProperty(js_util.globalThis, 'MedNarrateWebAuthn');
    if (jsObj == null) return (status: BiometricResult.unsupported, credId: null);

    final resObj = await js_util.promiseToFuture(
      js_util.callMethod(jsObj, 'registerNewCredential', [])
    );

    final String status = js_util.getProperty(resObj, 'status');
    final dynamic credId = js_util.getProperty(resObj, 'credId');

    if (status == 'SUCCESS') {
      return (status: BiometricResult.success, credId: credId is String ? credId : null);
    } else if (status == 'CANCELLED') {
      return (status: BiometricResult.cancelled, credId: null);
    } else if (status == 'NOT_CONFIGURED') {
      return (status: BiometricResult.notConfigured, credId: null);
    } else if (status == 'UNSUPPORTED') {
      return (status: BiometricResult.unsupported, credId: null);
    } else {
      return (status: BiometricResult.failure, credId: null);
    }
  } catch (_) {
    return (status: BiometricResult.failure, credId: null);
  }
}

Future<BiometricResult> verifyNewCredentialWebAuthn(String credId) async {
  try {
    final jsObj = js_util.getProperty(js_util.globalThis, 'MedNarrateWebAuthn');
    if (jsObj == null) return BiometricResult.unsupported;

    final resObj = await js_util.promiseToFuture(
      js_util.callMethod(jsObj, 'authenticateExisting', [credId])
    );

    final String status = js_util.getProperty(resObj, 'status');

    if (status == 'SUCCESS') {
      return BiometricResult.success;
    } else if (status == 'CANCELLED') {
      return BiometricResult.cancelled;
    } else {
      return BiometricResult.failure;
    }
  } catch (_) {
    return BiometricResult.failure;
  }
}

Future<bool> saveNewCredentialWebAuthn(String credId) async {
  try {
    final jsObj = js_util.getProperty(js_util.globalThis, 'MedNarrateWebAuthn');
    if (jsObj == null) return false;

    final resObj = await js_util.promiseToFuture(
      js_util.callMethod(jsObj, 'saveNewCredential', [credId])
    );

    final String status = js_util.getProperty(resObj, 'status');
    return status == 'SUCCESS';
  } catch (_) {
    return false;
  }
}

Future<BiometricResult> disableBiometricWebAuthn() async {
  try {
    final jsObj = js_util.getProperty(js_util.globalThis, 'MedNarrateWebAuthn');
    if (jsObj == null) return BiometricResult.unsupported;

    final resObj = await js_util.promiseToFuture(
      js_util.callMethod(jsObj, 'disableBiometric', [])
    );

    final String status = js_util.getProperty(resObj, 'status');

    if (status == 'SUCCESS') {
      return BiometricResult.success;
    } else if (status == 'CANCELLED') {
      return BiometricResult.cancelled;
    } else {
      return BiometricResult.failure;
    }
  } catch (_) {
    return BiometricResult.failure;
  }
}

Future<bool> openWindowsSettingsWeb() async {
  try {
    final jsObj = js_util.getProperty(js_util.globalThis, 'MedNarrateWebAuthn');
    if (jsObj == null) return false;
    js_util.callMethod(jsObj, 'openWindowsSettings', []);
    return true;
  } catch (_) {
    return false;
  }
}
