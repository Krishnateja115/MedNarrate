import 'package:flutter/widgets.dart';

/// The language the app is currently displayed in.
///
/// `main.dart` sets it from the saved language on start-up and the Settings
/// screen updates it when the user picks another language. It lives in its own
/// file so non-UI code (validators, services) can read it without importing
/// `main.dart`.
final localeModeNotifier = ValueNotifier<Locale>(const Locale('en'));
