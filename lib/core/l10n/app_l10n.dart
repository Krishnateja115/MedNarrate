import 'package:flutter/widgets.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

import 'locale_notifier.dart';

/// Strings in the language the user chose, for code that has no [BuildContext]
/// (form validators, services, enum labels, error messages).
///
/// Inside a widget prefer `AppLocalizations.of(context)!`. Everywhere else use
/// `appL10n.someKey`. Falls back to English for a language the app does not
/// ship.
AppLocalizations get appL10n {
  final locale = localeModeNotifier.value;
  try {
    return lookupAppLocalizations(locale);
  } catch (_) {
    return lookupAppLocalizations(const Locale('en'));
  }
}

/// Same lookup for an explicit language code such as `hi`.
AppLocalizations l10nFor(String languageCode) {
  try {
    return lookupAppLocalizations(Locale(languageCode));
  } catch (_) {
    return lookupAppLocalizations(const Locale('en'));
  }
}

/// Language code the user picked (e.g. `hi`), for date and number formatting.
String get appLanguageCode => localeModeNotifier.value.languageCode;
