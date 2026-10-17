import 'app_l10n.dart';

/// Turns the fixed English messages produced by the app and the backend into
/// the language the user picked. A message that is not in the table (a
/// validation detail, an unexpected server error) is returned unchanged, so
/// nothing is ever hidden or mistranslated.
String localizeApiMessage(String raw) {
  final l = appL10n;
  switch (raw.trim()) {
    case 'The request timed out. Check your connection and try again.':
      return l.apiTimeout;
    case 'Unable to connect to MedNarrate. Check that the backend is running and try again.':
      return l.apiCannotConnect;
    case 'Something went wrong while contacting MedNarrate. Please try again.':
      return l.apiGenericError;
    case 'Session expired. Please log in again.':
      return l.apiSessionExpired;
    case 'Voice input needs an internet connection. You can still type.':
      return l.apiVoiceNeedsInternet;
    case 'The selected file could not be read. Please select it again from Finder.':
      return l.apiFileUnreadable;
    case 'No saved chat is available offline.':
      return l.apiNoSavedChat;
    case 'This file cannot be saved for offline upload. Select a local file.':
      return l.apiCannotSaveOffline;
    case 'The report must be 25 MB or smaller.':
      return l.apiReportTooLarge;
    case 'This report is not available offline.':
      return l.apiReportNotOffline;
    case 'This analysis is not available offline.':
      return l.apiAnalysisNotOffline;
    case 'Chat requires a connection. Saved messages remain available offline.':
      return l.apiChatNeedsConnection;
    case 'Translation returned an unexpected language or empty report.':
      return l.apiTranslationUnexpected;
    // Backend (FastAPI "detail") messages
    case 'Incorrect email or password':
      return l.srvIncorrectCredentials;
    case 'You already have an account':
      return l.srvAlreadyHaveAccount;
    case 'Account is temporarily locked due to multiple failed login attempts':
      return l.srvAccountLocked;
    case 'Account is inactive':
      return l.srvAccountInactive;
    case 'Invalid or expired refresh token':
      return l.srvInvalidRefresh;
    case 'Invalid password':
      return l.srvInvalidPassword;
    case 'Password is incorrect':
      return l.srvPasswordIncorrect;
    case 'Not authenticated':
      return l.srvNotAuthenticated;
    case 'Could not validate credentials':
      return l.srvCouldNotValidate;
    case 'Token has expired':
      return l.srvTokenExpired;
    case 'Invalid token':
      return l.srvInvalidToken;
    case 'User not found':
      return l.srvUserNotFound;
    case 'Invalid or expired reset token':
      return l.srvResetInvalid;
    case 'Reset token has expired. Please request a new one.':
      return l.srvResetExpired;
    case 'Invalid or reused OTP code':
      return l.srvOtpInvalid;
    case 'Voice input is busy right now. Please try again in a minute, or type your message.':
      return l.srvVoiceBusy;
    case 'Voice input is not set up correctly on the server.':
      return l.srvVoiceMisconfigured;
    case 'Voice input is not set up on the server yet.':
      return l.srvVoiceNotSetUp;
    case 'Voice input took too long. Please try again.':
      return l.srvVoiceTooLong;
    case 'The server could not reach the voice service. Please try again.':
      return l.srvVoiceNetwork;
    case 'Voice input is temporarily unavailable. You can still type your message.':
      return l.srvVoiceUnavailable;
    case 'That recording could not be read. Please try again.':
      return l.srvVoiceUnreadable;
    case 'That audio format is not supported.':
      return l.srvVoiceFormat;
    case 'The recording is empty.':
      return l.srvVoiceEmpty;
    case 'Voice input is not enabled.':
      return l.srvVoiceDisabled;
    default:
      return raw;
  }
}
