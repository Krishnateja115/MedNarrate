import 'package:mednarrate/l10n/app_localizations.dart';

/// Display-only translation of values the app stores in English.
///
/// The stored value (what is sent to the server and saved) never changes; only
/// the words shown on screen follow the user's language. Anything not
/// recognised is shown exactly as it was stored (for example a free-text
/// frequency typed by a doctor or produced by report analysis).
String frequencyLabel(AppLocalizations l10n, String stored) {
  switch (stored.trim().toLowerCase()) {
    case 'once daily':
      return l10n.freqOnceDaily;
    case 'twice daily':
      return l10n.freqTwiceDaily;
    case 'three times daily':
      return l10n.freqThreeTimesDaily;
    case 'four times daily':
      return l10n.freqFourTimesDaily;
    case 'as needed':
      return l10n.freqAsNeeded;
    case 'custom':
      return l10n.freqCustom;
    default:
      return stored;
  }
}

/// Support-ticket categories are fixed English values on the server.
String supportCategoryLabel(AppLocalizations l10n, String stored) {
  switch (stored) {
    case 'Login/Account':
      return l10n.catLoginAccount;
    case 'Report Processing':
      return l10n.catReportProcessing;
    case 'AI/Analysis':
      return l10n.catAiAnalysis;
    case 'Chat':
      return l10n.catChat;
    case 'Translation':
      return l10n.catTranslation;
    case 'Notifications':
      return l10n.catNotifications;
    case 'Medication Reminder':
      return l10n.catMedicationReminder;
    case 'Performance':
      return l10n.catPerformance;
    case 'Security':
      return l10n.catSecurity;
    case 'Privacy':
      return l10n.catPrivacy;
    case 'Other':
      return l10n.catOther;
    default:
      return stored;
  }
}

/// Support-ticket status values are fixed English values on the server.
String supportStatusLabel(AppLocalizations l10n, String stored) {
  switch (stored) {
    case 'New':
      return l10n.ticketNew;
    case 'Triaged':
      return l10n.ticketTriaged;
    case 'Investigating':
      return l10n.ticketInvestigating;
    case 'Waiting for User':
      return l10n.ticketWaitingUser;
    case 'Waiting for Engineering':
      return l10n.ticketWaitingEng;
    case 'Resolved':
      return l10n.ticketResolved;
    case 'Closed':
      return l10n.ticketClosed;
    default:
      return stored;
  }
}
