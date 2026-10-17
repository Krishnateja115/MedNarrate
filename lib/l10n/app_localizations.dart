import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_bn.dart';
import 'app_localizations_en.dart';
import 'app_localizations_hi.dart';
import 'app_localizations_kn.dart';
import 'app_localizations_ml.dart';
import 'app_localizations_mr.dart';
import 'app_localizations_ta.dart';
import 'app_localizations_te.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
      : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations? of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations);
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
    delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
  ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('bn'),
    Locale('en'),
    Locale('hi'),
    Locale('kn'),
    Locale('ml'),
    Locale('mr'),
    Locale('ta'),
    Locale('te')
  ];

  /// Application name
  ///
  /// In en, this message translates to:
  /// **'MedNarrate'**
  String get appTitle;

  /// Login screen greeting
  ///
  /// In en, this message translates to:
  /// **'Welcome Back'**
  String get welcomeBack;

  /// Login screen subtitle
  ///
  /// In en, this message translates to:
  /// **'Sign in to continue'**
  String get signInToContinue;

  /// Email field label
  ///
  /// In en, this message translates to:
  /// **'Email'**
  String get email;

  /// Email address field label
  ///
  /// In en, this message translates to:
  /// **'Email Address'**
  String get emailAddress;

  /// Password field label
  ///
  /// In en, this message translates to:
  /// **'Password'**
  String get password;

  /// Confirm password field label
  ///
  /// In en, this message translates to:
  /// **'Confirm Password'**
  String get confirmPassword;

  /// Forgot password link
  ///
  /// In en, this message translates to:
  /// **'Forgot Password?'**
  String get forgotPassword;

  /// Login button
  ///
  /// In en, this message translates to:
  /// **'Login'**
  String get login;

  /// Login loading state
  ///
  /// In en, this message translates to:
  /// **'Signing in…'**
  String get signingIn;

  /// Signup link prompt
  ///
  /// In en, this message translates to:
  /// **'Don\'t have an account?'**
  String get dontHaveAccount;

  /// Sign up button
  ///
  /// In en, this message translates to:
  /// **'Sign Up'**
  String get signUp;

  /// Signup screen heading
  ///
  /// In en, this message translates to:
  /// **'Create Account'**
  String get createAccount;

  /// Signup screen subtitle
  ///
  /// In en, this message translates to:
  /// **'Let\'s personalize your health journey.'**
  String get personalizeHealthJourney;

  /// Full name field label
  ///
  /// In en, this message translates to:
  /// **'Full Name'**
  String get fullName;

  /// Signup loading state
  ///
  /// In en, this message translates to:
  /// **'Creating Account…'**
  String get creatingAccount;

  /// Login link on signup page
  ///
  /// In en, this message translates to:
  /// **'Already have an account? Login'**
  String get alreadyHaveAccount;

  /// Reset password screen title
  ///
  /// In en, this message translates to:
  /// **'Reset Password'**
  String get resetPassword;

  /// Send reset token button
  ///
  /// In en, this message translates to:
  /// **'Send Reset Token'**
  String get sendResetToken;

  /// Back to email button on reset
  ///
  /// In en, this message translates to:
  /// **'Back to Email'**
  String get backToEmail;

  /// Dashboard tab label
  ///
  /// In en, this message translates to:
  /// **'Dashboard'**
  String get dashboard;

  /// Journal/Reports tab label
  ///
  /// In en, this message translates to:
  /// **'Journal'**
  String get journal;

  /// Settings tab label
  ///
  /// In en, this message translates to:
  /// **'Settings'**
  String get settings;

  /// Profile tab label
  ///
  /// In en, this message translates to:
  /// **'Profile'**
  String get profile;

  /// Dashboard section heading
  ///
  /// In en, this message translates to:
  /// **'Quick Actions'**
  String get quickActions;

  /// Dashboard section heading
  ///
  /// In en, this message translates to:
  /// **'Recent Reports'**
  String get recentReports;

  /// Empty state on dashboard
  ///
  /// In en, this message translates to:
  /// **'No recent reports.'**
  String get noRecentReports;

  /// Reports title
  ///
  /// In en, this message translates to:
  /// **'Reports'**
  String get reports;

  /// All reports quick action
  ///
  /// In en, this message translates to:
  /// **'All Reports'**
  String get allReports;

  /// AI Chat quick action
  ///
  /// In en, this message translates to:
  /// **'AI Chat'**
  String get aiChat;

  /// Insights quick action
  ///
  /// In en, this message translates to:
  /// **'Insights'**
  String get insights;

  /// Statistics card: reports count
  ///
  /// In en, this message translates to:
  /// **'Reports'**
  String get statReports;

  /// Statistics card: reminders count
  ///
  /// In en, this message translates to:
  /// **'Reminders'**
  String get statReminders;

  /// Statistics card: favourites count
  ///
  /// In en, this message translates to:
  /// **'Favourites'**
  String get statFavourites;

  /// Empty state in reports screen
  ///
  /// In en, this message translates to:
  /// **'No reports found'**
  String get noReportsFound;

  /// Empty state subtitle in reports screen
  ///
  /// In en, this message translates to:
  /// **'Upload your first medical report to get started'**
  String get uploadFirstReport;

  /// Upload report app bar title
  ///
  /// In en, this message translates to:
  /// **'Upload Report'**
  String get uploadReport;

  /// Upload screen heading
  ///
  /// In en, this message translates to:
  /// **'Upload Medical Report'**
  String get uploadMedicalReport;

  /// Upload file type hint
  ///
  /// In en, this message translates to:
  /// **'PDF, JPG, JPEG, or PNG · max 25 MB'**
  String get pdfJpgPngMax;

  /// File picker button
  ///
  /// In en, this message translates to:
  /// **'Choose File'**
  String get chooseFile;

  /// Upload & analyze button
  ///
  /// In en, this message translates to:
  /// **'Upload & Analyze'**
  String get uploadAndAnalyze;

  /// Upload in-progress label
  ///
  /// In en, this message translates to:
  /// **'Uploading…'**
  String get uploading;

  /// Analysis in progress message on upload
  ///
  /// In en, this message translates to:
  /// **'Analyzing your report with AI…'**
  String get analyzingReport;

  /// Analysis wait time hint
  ///
  /// In en, this message translates to:
  /// **'This may take a minute.'**
  String get thisMayTakeAMinute;

  /// Report title field label
  ///
  /// In en, this message translates to:
  /// **'Title'**
  String get title;

  /// Hospital field label
  ///
  /// In en, this message translates to:
  /// **'Hospital (optional)'**
  String get hospital;

  /// Report type dropdown label
  ///
  /// In en, this message translates to:
  /// **'Report Type'**
  String get reportType;

  /// Report details screen title
  ///
  /// In en, this message translates to:
  /// **'Report Details'**
  String get reportDetails;

  /// Tab label: Summary
  ///
  /// In en, this message translates to:
  /// **'Summary'**
  String get summaryTab;

  /// Tab label: Lab Results
  ///
  /// In en, this message translates to:
  /// **'Lab Results'**
  String get labResultsTab;

  /// Tab label: AI Chat
  ///
  /// In en, this message translates to:
  /// **'AI Chat'**
  String get aiChatTab;

  /// Success message after deleting report
  ///
  /// In en, this message translates to:
  /// **'Report deleted.'**
  String get reportDeleted;

  /// Delete report menu item
  ///
  /// In en, this message translates to:
  /// **'Delete Report'**
  String get deleteReport;

  /// Delete report dialog title
  ///
  /// In en, this message translates to:
  /// **'Delete Report?'**
  String get deleteReportTitle;

  /// Delete report confirmation message
  ///
  /// In en, this message translates to:
  /// **'This will permanently delete this report and all its analysis. This cannot be undone.'**
  String get deleteReportConfirm;

  /// Cancel button
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancel;

  /// Delete button
  ///
  /// In en, this message translates to:
  /// **'Delete'**
  String get delete;

  /// AI analysis screen title
  ///
  /// In en, this message translates to:
  /// **'AI Analysis'**
  String get aiAnalysis;

  /// Analysis in progress heading
  ///
  /// In en, this message translates to:
  /// **'Analyzing your report…'**
  String get analyzingYourReport;

  /// Analysis wait description
  ///
  /// In en, this message translates to:
  /// **'AI is reading your document. This may take a minute.'**
  String get aiReadingDocument;

  /// Analysis failure heading
  ///
  /// In en, this message translates to:
  /// **'Analysis Failed'**
  String get analysisFailed;

  /// Retry analysis button
  ///
  /// In en, this message translates to:
  /// **'Retry Analysis'**
  String get retryAnalysis;

  /// Patient summary mode tab
  ///
  /// In en, this message translates to:
  /// **'For You'**
  String get forYou;

  /// Clinician summary mode tab
  ///
  /// In en, this message translates to:
  /// **'Clinical View'**
  String get clinicalView;

  /// Summary section heading
  ///
  /// In en, this message translates to:
  /// **'Summary'**
  String get summary;

  /// Lab values section heading
  ///
  /// In en, this message translates to:
  /// **'Lab Values'**
  String get labValues;

  /// Abnormal findings section heading
  ///
  /// In en, this message translates to:
  /// **'Abnormal Findings'**
  String get abnormalFindings;

  /// Abnormal alert title
  ///
  /// In en, this message translates to:
  /// **'Abnormal Values Detected'**
  String get abnormalValuesDetected;

  /// Abnormal alert body
  ///
  /// In en, this message translates to:
  /// **'Some parameters are outside the normal reference range.'**
  String get someParametersOutOfRange;

  /// Medical advice note
  ///
  /// In en, this message translates to:
  /// **'Consult your doctor about these findings.'**
  String get consultYourDoctor;

  /// Key findings section
  ///
  /// In en, this message translates to:
  /// **'Key Findings'**
  String get keyFindings;

  /// Empty state for key findings
  ///
  /// In en, this message translates to:
  /// **'No key findings available for this report.'**
  String get noKeyFindings;

  /// Empty state for lab values
  ///
  /// In en, this message translates to:
  /// **'No lab values found.'**
  String get noLabValues;

  /// Export PDF button
  ///
  /// In en, this message translates to:
  /// **'Export PDF'**
  String get exportPdf;

  /// Exporting in progress
  ///
  /// In en, this message translates to:
  /// **'Exporting…'**
  String get exporting;

  /// Print button
  ///
  /// In en, this message translates to:
  /// **'Print / Preview'**
  String get printPreview;

  /// Translate button
  ///
  /// In en, this message translates to:
  /// **'Translate'**
  String get translate;

  /// Retranslate button
  ///
  /// In en, this message translates to:
  /// **'Retranslate'**
  String get retranslate;

  /// Translate bottom sheet title
  ///
  /// In en, this message translates to:
  /// **'Translate Summary'**
  String get translateSummary;

  /// Translation error message
  ///
  /// In en, this message translates to:
  /// **'Translation failed. Please try again.'**
  String get translationFailed;

  /// Translated version available hint
  ///
  /// In en, this message translates to:
  /// **'Translated version available'**
  String get translatedVersionAvailable;

  /// Load button
  ///
  /// In en, this message translates to:
  /// **'Load'**
  String get load;

  /// Insights screen title
  ///
  /// In en, this message translates to:
  /// **'Health Insights'**
  String get healthInsights;

  /// Compare button in insights
  ///
  /// In en, this message translates to:
  /// **'Compare Selected'**
  String get compareSelected;

  /// Comparison section heading
  ///
  /// In en, this message translates to:
  /// **'Compared to Previous Report'**
  String get comparedToPreviousReport;

  /// No earlier report empty state
  ///
  /// In en, this message translates to:
  /// **'No earlier report available for comparison.'**
  String get noEarlierReport;

  /// Trend graph minimum reports message
  ///
  /// In en, this message translates to:
  /// **'Need at least 2 reports to show a trend graph.'**
  String get needTwoReports;

  /// No trend data empty state
  ///
  /// In en, this message translates to:
  /// **'No historical data for this test.'**
  String get noHistoricalData;

  /// Test trend section heading
  ///
  /// In en, this message translates to:
  /// **'Test Trend'**
  String get testTrend;

  /// Historical trend section heading
  ///
  /// In en, this message translates to:
  /// **'Historical Trend'**
  String get historicalTrend;

  /// Medicine reminders card title
  ///
  /// In en, this message translates to:
  /// **'Medicine Reminders'**
  String get medicineReminders;

  /// Medication reminders screen title
  ///
  /// In en, this message translates to:
  /// **'Medication Reminders'**
  String get medicationReminders;

  /// Medicine reminders subtitle
  ///
  /// In en, this message translates to:
  /// **'Set daily reminders for your medications'**
  String get setDailyReminders;

  /// Empty state for reminders
  ///
  /// In en, this message translates to:
  /// **'No reminders set'**
  String get noRemindersSet;

  /// Empty reminder prompt
  ///
  /// In en, this message translates to:
  /// **'Add your first reminder'**
  String get addFirstReminder;

  /// Repeat daily reminder option
  ///
  /// In en, this message translates to:
  /// **'Repeat Daily'**
  String get repeatDaily;

  /// Daily frequency label
  ///
  /// In en, this message translates to:
  /// **'Daily'**
  String get daily;

  /// Delete reminder title
  ///
  /// In en, this message translates to:
  /// **'Delete Reminder'**
  String get deleteReminder;

  /// Delete reminder confirmation
  ///
  /// In en, this message translates to:
  /// **'Are you sure you want to delete this reminder?'**
  String get deleteReminderConfirm;

  /// Medical profile screen title
  ///
  /// In en, this message translates to:
  /// **'Medical Information'**
  String get medicalProfile;

  /// Medical profile subtitle
  ///
  /// In en, this message translates to:
  /// **'Keep your medical history up to date for better analysis.'**
  String get keepMedicalHistoryUpdated;

  /// Blood group field
  ///
  /// In en, this message translates to:
  /// **'Blood Group'**
  String get bloodGroup;

  /// Known allergies field
  ///
  /// In en, this message translates to:
  /// **'Known Allergies'**
  String get knownAllergies;

  /// Chronic conditions field
  ///
  /// In en, this message translates to:
  /// **'Chronic Conditions'**
  String get chronicConditions;

  /// Save button
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get save;

  /// Saving in progress
  ///
  /// In en, this message translates to:
  /// **'Saving...'**
  String get saving;

  /// Emergency contact screen title
  ///
  /// In en, this message translates to:
  /// **'Emergency Contact'**
  String get emergencyContact;

  /// Emergency contact subtitle
  ///
  /// In en, this message translates to:
  /// **'We\'ll use this only during emergencies.'**
  String get emergencyContactSubtitle;

  /// Phone number field
  ///
  /// In en, this message translates to:
  /// **'Phone Number'**
  String get phoneNumber;

  /// Profile account section title
  ///
  /// In en, this message translates to:
  /// **'Account'**
  String get account;

  /// Personal info profile tile
  ///
  /// In en, this message translates to:
  /// **'Personal Information'**
  String get personalInformation;

  /// Personal info tile subtitle
  ///
  /// In en, this message translates to:
  /// **'View and edit your personal details'**
  String get viewEditPersonalDetails;

  /// Medical info tile subtitle
  ///
  /// In en, this message translates to:
  /// **'Blood group, allergies and history'**
  String get bloodGroupAllergiesHistory;

  /// Emergency contact tile subtitle
  ///
  /// In en, this message translates to:
  /// **'Emergency contact information'**
  String get emergencyContactInfo;

  /// Profile appearance section
  ///
  /// In en, this message translates to:
  /// **'Application & Appearance'**
  String get appAndAppearance;

  /// Theme mode tile
  ///
  /// In en, this message translates to:
  /// **'Theme Mode'**
  String get themeMode;

  /// Dark mode label
  ///
  /// In en, this message translates to:
  /// **'Dark Mode (OLED)'**
  String get darkMode;

  /// Light mode label
  ///
  /// In en, this message translates to:
  /// **'Light Mode'**
  String get lightMode;

  /// Settings tile subtitle
  ///
  /// In en, this message translates to:
  /// **'Language & Advanced Preferences'**
  String get languageAndPreferences;

  /// Logout button
  ///
  /// In en, this message translates to:
  /// **'Logout'**
  String get logout;

  /// Log out confirm button
  ///
  /// In en, this message translates to:
  /// **'Log Out'**
  String get logOut;

  /// Log out dialog title
  ///
  /// In en, this message translates to:
  /// **'Log Out?'**
  String get logOutTitle;

  /// Log out confirmation message
  ///
  /// In en, this message translates to:
  /// **'Are you sure you want to log out of MedNarrate?'**
  String get logOutConfirm;

  /// Profile load error
  ///
  /// In en, this message translates to:
  /// **'Failed to load profile'**
  String get failedToLoadProfile;

  /// Role update in progress
  ///
  /// In en, this message translates to:
  /// **'Updating role...'**
  String get updatingRole;

  /// Edit personal info dialog title
  ///
  /// In en, this message translates to:
  /// **'Edit Personal Info'**
  String get editPersonalInfo;

  /// Date of birth field
  ///
  /// In en, this message translates to:
  /// **'Date of Birth (YYYY-MM-DD)'**
  String get dateOfBirth;

  /// Settings section header
  ///
  /// In en, this message translates to:
  /// **'ACCOUNT & PROFILE'**
  String get accountAndProfile;

  /// Settings section header
  ///
  /// In en, this message translates to:
  /// **'PREFERENCES'**
  String get preferencesSection;

  /// Settings section header
  ///
  /// In en, this message translates to:
  /// **'SECURITY'**
  String get securitySection;

  /// Settings section header
  ///
  /// In en, this message translates to:
  /// **'NOTIFICATIONS'**
  String get notificationsSection;

  /// Settings section header
  ///
  /// In en, this message translates to:
  /// **'INTEGRATIONS'**
  String get integrationsSection;

  /// Settings section header
  ///
  /// In en, this message translates to:
  /// **'SUPPORT & ABOUT'**
  String get supportAboutSection;

  /// Language setting tile
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get language;

  /// Language picker title
  ///
  /// In en, this message translates to:
  /// **'Select Language'**
  String get selectLanguage;

  /// Medical units tile
  ///
  /// In en, this message translates to:
  /// **'Medical Units'**
  String get medicalUnits;

  /// Medical units picker title
  ///
  /// In en, this message translates to:
  /// **'Select Medical Units'**
  String get selectMedicalUnits;

  /// Metric units option
  ///
  /// In en, this message translates to:
  /// **'Metric (kg, cm, mmol/L)'**
  String get metricUnits;

  /// Imperial units option
  ///
  /// In en, this message translates to:
  /// **'Imperial (lb, in, mg/dL)'**
  String get imperialUnits;

  /// Theme mode picker title
  ///
  /// In en, this message translates to:
  /// **'Select Theme Mode'**
  String get selectThemeMode;

  /// Professional mode toggle tile
  ///
  /// In en, this message translates to:
  /// **'Professional Mode'**
  String get professionalMode;

  /// Professional mode subtitle
  ///
  /// In en, this message translates to:
  /// **'Show clinical summaries by default'**
  String get professionalModeSubtitle;

  /// App lock tile
  ///
  /// In en, this message translates to:
  /// **'App Lock'**
  String get appLock;

  /// App lock subtitle
  ///
  /// In en, this message translates to:
  /// **'Require biometrics to open app'**
  String get appLockSubtitle;

  /// Disable biometric dialog title
  ///
  /// In en, this message translates to:
  /// **'Disable App Lock?'**
  String get disableAppLock;

  /// Disable biometric warning
  ///
  /// In en, this message translates to:
  /// **'Your reports will be accessible without biometrics.'**
  String get appLockReportsAccessible;

  /// Disable button
  ///
  /// In en, this message translates to:
  /// **'Disable'**
  String get disable;

  /// Notifications toggle tile
  ///
  /// In en, this message translates to:
  /// **'Notifications'**
  String get notifications;

  /// Notifications subtitle
  ///
  /// In en, this message translates to:
  /// **'Enable medicine reminders & alerts'**
  String get notificationsSubtitle;

  /// Medication schedules tile
  ///
  /// In en, this message translates to:
  /// **'Medication Schedules'**
  String get medicationSchedules;

  /// Medication schedules subtitle
  ///
  /// In en, this message translates to:
  /// **'Manage your automated pill reminders'**
  String get managePillReminders;

  /// Reminder sound tile
  ///
  /// In en, this message translates to:
  /// **'Reminder Sound'**
  String get reminderSound;

  /// Health app sync tile
  ///
  /// In en, this message translates to:
  /// **'Health App Sync'**
  String get healthAppSync;

  /// Connected devices tile
  ///
  /// In en, this message translates to:
  /// **'Connected Devices'**
  String get connectedDevices;

  /// Help center tile
  ///
  /// In en, this message translates to:
  /// **'Help Center'**
  String get helpCenter;

  /// About tile
  ///
  /// In en, this message translates to:
  /// **'About MedNarrate'**
  String get aboutMedNarrate;

  /// App version subtitle
  ///
  /// In en, this message translates to:
  /// **'Version 1.0.0'**
  String get version;

  /// Terms of service link
  ///
  /// In en, this message translates to:
  /// **'Terms of Service'**
  String get termsOfService;

  /// Privacy policy link
  ///
  /// In en, this message translates to:
  /// **'Privacy Policy'**
  String get privacyPolicy;

  /// Contact support link
  ///
  /// In en, this message translates to:
  /// **'Contact Support'**
  String get contactSupport;

  /// Coming soon badge
  ///
  /// In en, this message translates to:
  /// **'Coming Soon'**
  String get comingSoon;

  /// Processing status label
  ///
  /// In en, this message translates to:
  /// **'Processing'**
  String get processing;

  /// Retry button
  ///
  /// In en, this message translates to:
  /// **'Retry'**
  String get retry;

  /// Go to reports button
  ///
  /// In en, this message translates to:
  /// **'Go to Reports'**
  String get goToReports;

  /// Empty state for medication schedules
  ///
  /// In en, this message translates to:
  /// **'No medication schedules found in your reports yet. Upload a report that contains prescriptions to start tracking.'**
  String get noMedicationSchedules;

  /// Chat message copy toast
  ///
  /// In en, this message translates to:
  /// **'Message copied'**
  String get messageCopied;

  /// Ask AI button label
  ///
  /// In en, this message translates to:
  /// **'Ask AI about this'**
  String get askAiAboutThis;

  /// Lab results search hint
  ///
  /// In en, this message translates to:
  /// **'Search parameters...'**
  String get searchParameters;

  /// Timeline screen title
  ///
  /// In en, this message translates to:
  /// **'Timeline'**
  String get timeline;

  /// Export button
  ///
  /// In en, this message translates to:
  /// **'Export'**
  String get export;

  /// Export data tile
  ///
  /// In en, this message translates to:
  /// **'Export Data'**
  String get exportData;

  /// Export data confirmation
  ///
  /// In en, this message translates to:
  /// **'Request an archive of your medical history?'**
  String get requestArchive;

  /// Language update success toast
  ///
  /// In en, this message translates to:
  /// **'Language updated successfully'**
  String get languageUpdated;

  /// Medical units update success toast
  ///
  /// In en, this message translates to:
  /// **'Medical units updated'**
  String get medicalUnitsUpdated;

  /// Notifications enabled toast
  ///
  /// In en, this message translates to:
  /// **'Notifications enabled'**
  String get notificationsEnabled;

  /// Notifications disabled toast
  ///
  /// In en, this message translates to:
  /// **'Notifications disabled'**
  String get notificationsDisabled;

  /// Pro mode enabled toast
  ///
  /// In en, this message translates to:
  /// **'Professional Mode enabled'**
  String get professionalModeEnabled;

  /// Pro mode disabled toast
  ///
  /// In en, this message translates to:
  /// **'Professional Mode disabled'**
  String get professionalModeDisabled;

  /// Upload success toast
  ///
  /// In en, this message translates to:
  /// **'Report analyzed successfully!'**
  String get reportAnalyzedSuccessfully;

  /// statusHigh text
  ///
  /// In en, this message translates to:
  /// **'HIGH'**
  String get statusHigh;

  /// statusLow text
  ///
  /// In en, this message translates to:
  /// **'LOW'**
  String get statusLow;

  /// statusNormal text
  ///
  /// In en, this message translates to:
  /// **'NORMAL'**
  String get statusNormal;

  /// statusCritical text
  ///
  /// In en, this message translates to:
  /// **'CRITICAL'**
  String get statusCritical;

  /// statusNotClassified text
  ///
  /// In en, this message translates to:
  /// **'Not classified'**
  String get statusNotClassified;

  /// hospitalUnspecified text
  ///
  /// In en, this message translates to:
  /// **'Unspecified'**
  String get hospitalUnspecified;

  /// validationPassed text
  ///
  /// In en, this message translates to:
  /// **'PASSED'**
  String get validationPassed;

  /// statusCompleted text
  ///
  /// In en, this message translates to:
  /// **'COMPLETED'**
  String get statusCompleted;

  /// sectionLaboratoryResults text
  ///
  /// In en, this message translates to:
  /// **'Laboratory Results'**
  String get sectionLaboratoryResults;

  /// sectionReportedMedications text
  ///
  /// In en, this message translates to:
  /// **'Reported Medications'**
  String get sectionReportedMedications;

  /// sectionDiagnosesAndFindings text
  ///
  /// In en, this message translates to:
  /// **'Diagnoses & Findings'**
  String get sectionDiagnosesAndFindings;

  /// sectionHistoricalComparison text
  ///
  /// In en, this message translates to:
  /// **'Historical Comparison'**
  String get sectionHistoricalComparison;

  /// sectionSourceAndValidation text
  ///
  /// In en, this message translates to:
  /// **'Source & Validation'**
  String get sectionSourceAndValidation;

  /// sectionClinicalExecutiveSummary text
  ///
  /// In en, this message translates to:
  /// **'Clinical Executive Summary'**
  String get sectionClinicalExecutiveSummary;

  /// translationUnavailable text
  ///
  /// In en, this message translates to:
  /// **'Translation unavailable, showing original.'**
  String get translationUnavailable;

  /// translationFailedRetry text
  ///
  /// In en, this message translates to:
  /// **'Translation failed. Please try again.'**
  String get translationFailedRetry;

  /// disclaimerPatient text
  ///
  /// In en, this message translates to:
  /// **'Disclaimer: MedNarrate patient summaries provide educational context only and do not constitute a medical diagnosis or prescription. Always consult your doctor for personalized advice.'**
  String get disclaimerPatient;

  /// disclaimerSummary text
  ///
  /// In en, this message translates to:
  /// **'Disclaimer: MedNarrate AI summary is for informational purposes only and does not replace medical advice. Always consult a qualified physician for clinical decisions.'**
  String get disclaimerSummary;

  /// disclaimerEmergency text
  ///
  /// In en, this message translates to:
  /// **'This sounds like a medical emergency. Please call your local emergency services (like 112 or 911) or go to the nearest emergency room immediately.'**
  String get disclaimerEmergency;

  /// disclaimerNoFindings text
  ///
  /// In en, this message translates to:
  /// **'No key findings identified.'**
  String get disclaimerNoFindings;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Health Progress'**
  String get healthProgress;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'No health progress yet'**
  String get noHealthProgressYet;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Upload a medical report to start tracking your health progress.'**
  String get uploadToTrackProgress;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Latest report analyzed'**
  String get latestReportAnalyzed;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Historical trend tracking will become available when additional comparable reports are uploaded.'**
  String get historicalTrendPending;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Upload Another Report'**
  String get uploadAnotherReport;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Stable'**
  String get trendStable;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Increased since previous report'**
  String get trendIncreased;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Decreased since previous report'**
  String get trendDecreased;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Reports Compared: {count}'**
  String reportsComparedCount(int count);

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Previous'**
  String get previous;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Current'**
  String get current;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Today\'s Medicine'**
  String get todaysMedicine;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Add Medicine'**
  String get addMedicine;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'No medicines added yet'**
  String get noMedicinesYet;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Add a medication or upload a report containing medication information.'**
  String get addMedicationHint;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Medications from Latest Report'**
  String get medicationsFromLatestReport;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Reported'**
  String get reportedBadge;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Medication'**
  String get medicationLabel;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Timing: Not specified'**
  String get timingNotSpecified;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Confirm to Schedule'**
  String get confirmToSchedule;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'My Confirmed Schedule'**
  String get myConfirmedSchedule;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Dark mode enabled'**
  String get darkModeEnabled;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Light mode enabled'**
  String get lightModeEnabled;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Good Morning ☀️'**
  String get goodMorning;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Good Afternoon 🌤️'**
  String get goodAfternoon;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Good Evening 🌙'**
  String get goodEvening;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Switch to Light Mode'**
  String get switchToLightMode;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Switch to Dark Mode'**
  String get switchToDarkMode;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Disable Notifications'**
  String get disableNotifications;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Enable Notifications'**
  String get enableNotifications;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'No lab data yet'**
  String get noLabDataYet;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Looking Good'**
  String get scoreLookingGood;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Some Attention Needed'**
  String get scoreAttentionNeeded;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Consult Your Doctor'**
  String get scoreConsultDoctor;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Health Score'**
  String get healthScore;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'{abnormalCount} abnormal / {totalLabValues} total values'**
  String abnormalOfTotal(int abnormalCount, int totalLabValues);

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'User'**
  String get defaultUserName;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Unable to load your dashboard. Please try again.'**
  String get dashboardLoadError;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Try again'**
  String get tryAgain;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'No reports yet'**
  String get noReportsYet;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Your recent medical reports will appear here once you add them.'**
  String get recentReportsEmptyHint;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Today\'s Health Tip'**
  String get todaysHealthTip;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'All'**
  String get reportsFilterAll;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Upload your first report'**
  String get uploadFirstReportButton;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Starting report analysis...'**
  String get startingReportAnalysis;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Analysis request failed: {error}'**
  String analysisRequestFailed(String error);

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Unable to delete report: {message}'**
  String unableToDeleteReportWithMessage(String message);

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Unable to delete report. Please try again.'**
  String get unableToDeleteReport;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Search reports...'**
  String get searchReportsHint;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Analyze'**
  String get analyze;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Share'**
  String get share;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Sharing report details...'**
  String get sharingReportDetails;

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'MedNarrate Medical Report: {title}\nHospital: {hospital}\nDate: {date}\nType: {kind}'**
  String shareReportText(
      String title, String hospital, String date, String kind);

  /// dashboard screen text
  ///
  /// In en, this message translates to:
  /// **'Tap here to upload a new medical report for analysis'**
  String get uploadCardHint;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Biometric App Lock is available on the mobile app (Android / iOS)'**
  String get biometricMobileOnly;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Protected with device biometric authentication'**
  String get biometricProtected;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Use fingerprint or Face ID to protect the app'**
  String get biometricUseFingerprint;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Set up fingerprint or Face ID in device settings first'**
  String get biometricSetUpFirst;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Biometric authentication is not available on this device'**
  String get biometricNotAvailable;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Biometric authentication is not available on this device.'**
  String get biometricNotAvailableMsg;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Please set up fingerprint or Face ID in your device settings first.'**
  String get biometricSetUpFirstMsg;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Biometric App Lock enabled successfully.'**
  String get biometricEnabledOk;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Biometric App Lock disabled.'**
  String get biometricDisabledOk;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Authentication cancelled.'**
  String get authCancelled;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Biometric authentication failed. Please try again.'**
  String get biometricFailedRetry;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Biometric management requires a physical Android or iOS mobile device.'**
  String get biometricManageNeedsDevice;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Biometric change cancelled.'**
  String get biometricChangeCancelled;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Authentication failed. Your biometric settings have not been changed.'**
  String get biometricAuthFailedUnchanged;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Biometric App Lock requires a physical Android or iOS mobile device. It is not available in the web browser environment.'**
  String get biometricWebNotSupported;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Change Device Biometrics'**
  String get changeDeviceBiometrics;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Current biometric verified successfully!\n\nTo add or update your fingerprint or Face ID, manage your biometrics in your mobile device settings:'**
  String get biometricVerifiedBody;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Open Device Security Settings'**
  String get openDeviceSecuritySettings;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Done'**
  String get done;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Close'**
  String get close;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Allow notifications in your phone settings to receive medicine alerts.'**
  String get notificationsAllowInSettings;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'System Default'**
  String get themeSystemDefault;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Crystal Chime'**
  String get soundCrystalChime;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Warm Chord'**
  String get soundWarmChord;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Nature Drop'**
  String get soundNatureDrop;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Could not save the archive. Please try again.'**
  String get archiveCouldNotSave;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Your MedNarrate account archive'**
  String get archiveShareSubject;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Delete account and medical data?'**
  String get deleteAccountTitle;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'This permanently removes your reports, medical profile, reminders, and chat history. Export your data first if needed. Enter your password to confirm.'**
  String get deleteAccountBody;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Delete Account'**
  String get deleteAccount;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Enter your password to confirm deletion.'**
  String get passwordRequiredForDeletion;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Could not delete the account. Please try again.'**
  String get deleteAccountFailed;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'© 2026 MedNarrate\nAll rights reserved.'**
  String get copyrightNotice;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'View Licenses'**
  String get viewLicenses;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Update your basic profile details'**
  String get updateBasicProfile;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Biometric App Lock'**
  String get biometricAppLock;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Biometric App Lock is available when running on a mobile device (Android / iOS).'**
  String get biometricMobileOnlyDot;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Change Biometric'**
  String get changeBiometric;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Re-verify & manage device biometric settings'**
  String get reverifyBiometric;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Save an archive of your medical data'**
  String get saveArchive;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Permanently remove your account and medical data'**
  String get deleteAccountSubtitle;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'APP PREFERENCES'**
  String get appPreferencesSection;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Theme'**
  String get theme;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Dark Mode'**
  String get themeDark;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Show clinical summaries instead of patient-friendly ones'**
  String get professionalModeHint;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Metric (kg, cm, °C)'**
  String get metricUnitsShort;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Imperial (lbs, in, °F)'**
  String get imperialUnitsShort;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Push Notifications'**
  String get pushNotifications;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'SOON'**
  String get soonBadge;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Sync with Apple Health and Google Fit to automatically pull your vitals and activity data.'**
  String get healthAppSyncDesc;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Connect your wearables, glucometers, and blood pressure monitors to track readings automatically.'**
  String get connectedDevicesDesc;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Ask for help or report a problem'**
  String get askHelpReport;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'How do I upload a medical report?'**
  String get faqUploadQ;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'You can upload a report from the Home screen by tapping the \"+\" button. We support PDF documents and images (JPG/PNG).'**
  String get faqUploadA;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Is my medical data secure?'**
  String get faqSecureQ;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Yes. MedNarrate encrypts your data both in transit and at rest. We also provide biometric app lock capabilities to protect your medical history locally on your device.'**
  String get faqSecureA;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'How does the AI analysis work?'**
  String get faqAiQ;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'MedNarrate uses advanced clinical AI models to extract, summarize, and explain complex medical jargon in a patient-friendly format.'**
  String get faqAiA;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Can I share my reports?'**
  String get faqShareQ;

  /// settings screen text
  ///
  /// In en, this message translates to:
  /// **'Yes, you can export your data from the Settings screen or share individual reports directly using the share button on the report details screen.'**
  String get faqShareA;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Patient'**
  String get rolePatient;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Doctor'**
  String get roleDoctor;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Daughter'**
  String get relDaughter;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Son'**
  String get relSon;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Spouse'**
  String get relSpouse;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Parent'**
  String get relParent;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Guardian'**
  String get relGuardian;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Sibling'**
  String get relSibling;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Relative'**
  String get relRelative;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Professional Caregiver'**
  String get relProfessionalCaregiver;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Could not switch profile. Please try again.'**
  String get couldNotSwitchProfile;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Full name is required.'**
  String get fullNameRequired;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Full name must contain valid letters.'**
  String get fullNameInvalidLetters;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Name can only contain letters and spaces.'**
  String get nameLettersSpacesOnly;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Invalid format. Use YYYY-MM-DD (e.g., 2006-05-20)'**
  String get dobInvalidFormat;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Year must be 1900 or later'**
  String get dobYearMin;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Invalid month ({month}). Must be between 01 and 12'**
  String dobInvalidMonth(int month);

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'February {year} (leap year) has only 29 days'**
  String dobFebLeap(int year);

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'February {year} has only 28 days'**
  String dobFebDays(int year);

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Month {month} has only {maxDays} days'**
  String dobMonthDays(int month, int maxDays);

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Date of Birth cannot be in the future'**
  String get dobFuture;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Doctor Personal Details'**
  String get doctorPersonalDetails;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Doctor Full Name *'**
  String get doctorFullNameReq;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Professional Information'**
  String get professionalInformation;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Medical Specialty *'**
  String get medicalSpecialtyReq;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Qualifications (e.g. MBBS, MD) *'**
  String get qualificationsLabel;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Medical License / Registration No. *'**
  String get licenseLabel;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Years of Experience *'**
  String get yearsExperienceLabel;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Hospital / Clinic / Organization'**
  String get hospitalOrgLabel;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Professional Address'**
  String get professionalAddressLabel;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Medical specialty is required.'**
  String get specialtyRequired;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Qualifications are required.'**
  String get qualificationsRequired;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Medical license / registration number is required.'**
  String get licenseRequired;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Please enter valid years of experience (0 - 70).'**
  String get yearsExperienceInvalid;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Caregiver Personal Details'**
  String get caregiverPersonalDetails;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Caregiver Full Name *'**
  String get caregiverFullNameReq;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Caregiver Information'**
  String get caregiverInformation;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Relationship to Patient *'**
  String get relationshipToPatientReq;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Caregiving Role (e.g. Primary Caregiver)'**
  String get caregivingRoleLabel;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Supported Patient Name (Optional)'**
  String get supportedPatientNameOpt;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Employer / Organization (Optional)'**
  String get employerOrgOpt;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Relationship to patient is required.'**
  String get relationshipRequired;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Doctor Account'**
  String get doctorAccount;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Caregiver Account'**
  String get caregiverAccount;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'View and edit your professional/personal details'**
  String get viewEditProfessionalDetails;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Specialty, qualifications and registration details'**
  String get professionalInfoSubtitle;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Caregiving role and supported patient information'**
  String get caregiverInfoSubtitle;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'No professional information added yet. Tap Professional Information to complete your doctor profile.'**
  String get noProfessionalInfo;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Doctor Profile Summary'**
  String get doctorProfileSummary;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Specialty: {value}'**
  String specialtyLine(String value);

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Qualifications: {value}'**
  String qualificationsLine(String value);

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Registration No.: {value}'**
  String registrationLine(String value);

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Experience: {years} years'**
  String experienceLine(String years);

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Hospital: {value}'**
  String hospitalLine(String value);

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'No caregiver information added yet. Tap Caregiver Information to complete your profile.'**
  String get noCaregiverInfo;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Caregiver Profile Summary'**
  String get caregiverProfileSummary;

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Relationship to Patient: {value}'**
  String relationshipLine(String value);

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Caregiving Role: {value}'**
  String caregivingRoleLine(String value);

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Supporting Patient: {value}'**
  String supportingPatientLine(String value);

  /// profile screen text
  ///
  /// In en, this message translates to:
  /// **'Organization: {value}'**
  String organizationLine(String value);

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Invalid blood group. Valid options: A+, A-, B+, B-, AB+, AB-, O+, O-'**
  String get invalidBloodGroup;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'{fieldName} cannot consist only of special characters.'**
  String fieldOnlySpecialChars(String fieldName);

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'{field} has not been provided.'**
  String fieldNotProvided(String field);

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Some medical information is incomplete. You can update it later.'**
  String get medicalInfoIncomplete;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Medical information saved successfully.'**
  String get medicalInfoSaved;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Failed to save medical information'**
  String get medicalInfoSaveFailed;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Please enter the emergency contact\'s full name.'**
  String get emergencyNameRequired;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Please enter a valid name containing letters.'**
  String get emergencyNameInvalid;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Please enter a valid 10-digit Indian mobile number.'**
  String get invalidIndianMobile;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Emergency contact saved successfully.'**
  String get emergencyContactSaved;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Failed to save emergency contact.'**
  String get emergencyContactSaveFailed;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Please enter your email address.'**
  String get enterEmailAddress;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Please fill in all fields.'**
  String get fillAllFields;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Password must be at least 8 characters and include an uppercase letter, a lowercase letter, a number and a special character.'**
  String get passwordRules;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Password reset successfully! Please log in.'**
  String get passwordResetSuccess;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Set New Password'**
  String get setNewPassword;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Enter the reset token and your new password below.'**
  String get enterResetTokenAndPassword;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Enter your email and we\'ll e-mail you a reset code.'**
  String get enterEmailForResetCode;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Reset Token'**
  String get resetToken;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'New Password'**
  String get newPassword;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Passwords do not match'**
  String get passwordsDoNotMatch;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Confirm your password'**
  String get confirmYourPassword;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Password is required'**
  String get passwordIsRequired;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'MedNarrate explains reports but does not diagnose conditions or replace a clinician.'**
  String get medicalDisclaimerShort;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Email is required'**
  String get emailRequired;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Enter a valid email address'**
  String get emailInvalid;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Password must be at least 8 characters'**
  String get passwordMin8;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Password must contain a letter'**
  String get passwordNeedsLetter;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Password must contain a digit'**
  String get passwordNeedsDigit;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'This field'**
  String get thisField;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'{fieldName} is required'**
  String fieldRequired(String fieldName);

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Authenticate to unlock MedNarrate'**
  String get unlockReason;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Biometric authentication was cancelled.'**
  String get biometricCancelled;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Biometric authentication is not supported by this browser.'**
  String get biometricBrowserUnsupported;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Too many attempts. Please try again in 30 seconds.'**
  String get tooManyAttempts30;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Too many attempts. Please try again in {seconds} seconds.'**
  String tooManyAttemptsSeconds(int seconds);

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Your records are locked'**
  String get recordsLocked;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Authenticate to continue'**
  String get authenticateToContinue;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Unlock with Biometrics'**
  String get unlockWithBiometrics;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Forgot? '**
  String get forgotPrompt;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Unable to connect'**
  String get startupUnableToConnect;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Secure sign-in is unavailable'**
  String get startupSecureSignInUnavailable;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'MedNarrate cannot access the encrypted macOS Keychain. Quit the app, install the latest build, and then try again.'**
  String get startupKeychainMessage;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Understand\nMedical Reports'**
  String get onbTitle1;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Upload any medical report and let AI explain every medical term in simple language.'**
  String get onbBody1;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'AI Health\nAssistant'**
  String get onbTitle2;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Ask questions about your uploaded reports and receive clear, easy-to-understand explanations.'**
  String get onbBody2;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Medicine\nReminders'**
  String get onbTitle3;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Never miss your medicines. Receive intelligent reminders based on your prescriptions.'**
  String get onbBody3;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Track Your\nHealth'**
  String get onbTitle4;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Monitor health trends, compare reports and understand your progress over time.'**
  String get onbBody4;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Skip'**
  String get skip;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Get Started'**
  String get getStarted;

  /// forms screen text
  ///
  /// In en, this message translates to:
  /// **'Continue'**
  String get continueLabel;

  /// misc screen text
  ///
  /// In en, this message translates to:
  /// **'AI Medical Report Assistant'**
  String get appTagline;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Uploading report...'**
  String get uploadStatusUploadingReport;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Uploading medical report...'**
  String get uploadStatusUploadingMedical;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Extracting text and analyzing report...'**
  String get uploadStatusExtracting;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Still processing. Reconnecting to check your report...'**
  String get uploadStatusReconnecting;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Retrying AI analysis...'**
  String get uploadStatusRetrying;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Medical reports'**
  String get fileChooserTypeLabel;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Choose Report'**
  String get fileChooserConfirm;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Only PDF, JPG, JPEG, and PNG files are supported.'**
  String get uploadOnlyTypes;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'File must be smaller than {size}.'**
  String uploadFileTooLarge(String size);

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'The file chooser could not open. Close any open file dialog and try again.'**
  String get uploadChooserFailed;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'The selected file could not be read. Please choose it again from Finder.'**
  String get uploadFileUnreadable;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'The report was uploaded successfully, but text recognition is not available on this server.'**
  String get uploadErrOcrUnavailable;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'The image was uploaded successfully, but readable medical text could not be extracted from it. Please upload a clearer scan or image.'**
  String get uploadErrImageUnreadable;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Unable to extract text from this PDF document. The file may be scanned or unreadable.'**
  String get uploadErrPdfUnreadable;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'The uploaded file is empty or formatted improperly.'**
  String get uploadErrFileEmpty;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'This does not appear to be a medical report. Please upload a clearer report or clinical document.'**
  String get uploadErrNotMedical;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Your report was uploaded and text was extracted, but AI analysis could not be completed right now.'**
  String get uploadErrAiUnavailableExtracted;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Your report was uploaded successfully, but AI analysis could not be completed right now.'**
  String get uploadErrAiUnavailable;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Unable to connect to the server. Please check your network connection.'**
  String get uploadErrNetwork;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Your session has expired. Please sign in again.'**
  String get uploadErrSession;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Please select a report file first.'**
  String get selectReportFileFirst;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Report Title *'**
  String get reportTitleReq;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'e.g. Annual Blood Test'**
  String get reportTitleHint;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Title is required'**
  String get titleRequired;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Hospital / Clinic (optional)'**
  String get hospitalClinicOptional;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'e.g. City General Hospital'**
  String get hospitalHint;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Your document will be stored and its text processed by MedNarrate and configured AI services to create an explanation. Check important results against the original report.'**
  String get uploadDataNotice;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'How your data is used'**
  String get howDataIsUsed;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Processing report…'**
  String get processingReportEllipsis;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'PDF, JPG, JPEG, or PNG · Max 25 MB'**
  String get uploadFormatsHint;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Report Date'**
  String get reportDateLabel;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Auto-detect from document'**
  String get autoDetectFromDocument;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Choose a file to analyze'**
  String get chooseFileToAnalyze;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Opening file chooser…'**
  String get openingFileChooser;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Supports PDF, JPG, JPEG, PNG (up to 25 MB)'**
  String get supportsFormatsUpTo;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Report uploaded'**
  String get reportUploadedBadge;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'File Ready'**
  String get fileReadyBadge;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Remove file'**
  String get removeFile;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Step 1: Upload Completed'**
  String get step1UploadCompleted;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Step 2: Text Extraction Failed'**
  String get step2TextExtractionFailed;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Step 2: AI Analysis Unavailable'**
  String get step2AiUnavailable;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Step 2: Processing AI Analysis'**
  String get step2ProcessingAi;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'You can leave this page. Your report will appear in Reports when processing finishes.'**
  String get canLeavePageNotice;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Text Recognition Unavailable'**
  String get failTitleOcrUnavailable;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'This Is Not a Medical Report'**
  String get failTitleNotMedical;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Unable to Read This Image'**
  String get failTitleImage;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Unable to Read This Document'**
  String get failTitleDocument;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'AI Analysis Unavailable'**
  String get failTitleAi;

  /// upload screen text
  ///
  /// In en, this message translates to:
  /// **'Retry AI Analysis'**
  String get retryAiAnalysis;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Phone notifications are off. Enable them in device settings to receive medicine alerts.'**
  String get reminderNotificationsOff;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Failed to load reminders: {error}'**
  String failedToLoadReminders(String error);

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Failed to delete reminder: {error}'**
  String failedToDeleteReminder(String error);

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Failed to update status: {error}'**
  String failedToUpdateStatus(String error);

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Reminder on'**
  String get reminderOn;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Edit medication'**
  String get editMedication;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Delete medication'**
  String get deleteMedication;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Once daily'**
  String get freqOnceDaily;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Twice daily'**
  String get freqTwiceDaily;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Three times daily'**
  String get freqThreeTimesDaily;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Four times daily'**
  String get freqFourTimesDaily;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'As needed'**
  String get freqAsNeeded;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Custom'**
  String get freqCustom;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Scheduled'**
  String get freqScheduled;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Error saving reminder: {error}'**
  String errorSavingReminder(String error);

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'New Medication'**
  String get newMedication;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Edit Medication'**
  String get editMedicationTitle;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Medicine Name'**
  String get medicineNameLabel;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Medicine name is required'**
  String get medicineNameRequired;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Dosage (e.g. 500mg, 1 tablet)'**
  String get dosageLabel;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Frequency'**
  String get frequencyLabel;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Times of Day'**
  String get timesOfDay;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Add Time'**
  String get addTime;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Please add at least one time.'**
  String get addAtLeastOneTime;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Additional Notes (optional)'**
  String get additionalNotesOptional;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Save Medication'**
  String get saveMedication;

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Failed to update schedule: {error}'**
  String failedToUpdateSchedule(String error);

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'Failed to load schedules: {error}'**
  String failedToLoadSchedules(String error);

  /// reminders screen text
  ///
  /// In en, this message translates to:
  /// **'For {days} days'**
  String forDaysCount(int days);

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Support'**
  String get supportTitle;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'New request'**
  String get supportNewRequest;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Could not load support requests.'**
  String get supportCouldNotLoad;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'No support requests yet.'**
  String get supportNoRequests;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Request'**
  String get supportRequestFallback;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Support request'**
  String get supportRequestDialogTitle;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Contact support'**
  String get supportContactTitle;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Describe the problem without pasting your full medical report. We will attach the report ID when relevant.'**
  String get supportDescribeHint;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Subject'**
  String get supportSubject;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Enter a subject'**
  String get supportEnterSubject;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Category'**
  String get supportCategory;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'What went wrong?'**
  String get supportWhatWentWrong;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Please add a little more detail'**
  String get supportMoreDetail;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Support request sent'**
  String get supportRequestSent;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Sending…'**
  String get sendingEllipsis;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Send request'**
  String get sendRequest;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Status: {status}'**
  String supportStatusLine(String status);

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Reply to support'**
  String get replyToSupport;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Send reply'**
  String get sendReply;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Login/Account'**
  String get catLoginAccount;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Report Processing'**
  String get catReportProcessing;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'AI/Analysis'**
  String get catAiAnalysis;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Chat'**
  String get catChat;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Translation'**
  String get catTranslation;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Notifications'**
  String get catNotifications;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Medication Reminder'**
  String get catMedicationReminder;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Performance'**
  String get catPerformance;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Security'**
  String get catSecurity;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Privacy'**
  String get catPrivacy;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Other'**
  String get catOther;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'New'**
  String get ticketNew;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Triaged'**
  String get ticketTriaged;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Investigating'**
  String get ticketInvestigating;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Waiting for User'**
  String get ticketWaitingUser;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Waiting for Engineering'**
  String get ticketWaitingEng;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Resolved'**
  String get ticketResolved;

  /// support screen text
  ///
  /// In en, this message translates to:
  /// **'Closed'**
  String get ticketClosed;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'No clinical executive summary available for this report.'**
  String get noClinicalSummary;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'No patient-friendly summary available for this report.'**
  String get noPatientSummary;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'Translating your report. This can take up to a minute…'**
  String get translatingReportBanner;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'Metadata'**
  String get metadataFallback;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'Finding'**
  String get findingFallback;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'General comparison range'**
  String get generalComparisonRange;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'provisional'**
  String get provisionalWord;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'Based on a published general range, not this lab’s range. Confirm with your clinician. Source: {source}'**
  String provisionalNote(String source);

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'(general, provisional)'**
  String get refGeneralProvisional;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'(general)'**
  String get refGeneralShort;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'No ref range'**
  String get noRefRangeShort;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'This measures {parameter} in your medical document. Always consult your physician for interpretation.'**
  String labMeasuresDesc(String parameter);

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'Text detected in the uploaded report'**
  String get textDetectedInReport;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'Check this against the original document; OCR can make mistakes.'**
  String get checkAgainstOriginalOcr;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'View original report'**
  String get viewOriginalReport;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'Report an incorrect result'**
  String get reportAnIncorrectResult;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'Back'**
  String get backLabel;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'Unfavourite'**
  String get unfavourite;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'Favourite'**
  String get favourite;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'PDF downloaded successfully'**
  String get pdfDownloadedOk;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'Export failed: {error}'**
  String exportFailed(String error);

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'Preview failed: {error}'**
  String previewFailed(String error);

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'Report no longer available'**
  String get reportNoLongerAvailable;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'This report may have been deleted or is no longer accessible.'**
  String get reportMayBeDeleted;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'Back to Reports'**
  String get backToReports;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'Original report'**
  String get originalReportTitle;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'Unable to open the original document.'**
  String get unableToOpenOriginal;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'Compare AI findings with this uploaded document before making decisions.'**
  String get compareAiFindings;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'Could not open the chat. Please try again.'**
  String get chatCouldNotOpen;

  /// reportdetail screen text
  ///
  /// In en, this message translates to:
  /// **'Something went wrong. Please try again.'**
  String get somethingWentWrongRetry;

  /// helpers screen text
  ///
  /// In en, this message translates to:
  /// **'Blood Test'**
  String get reportTypeBlood;

  /// helpers screen text
  ///
  /// In en, this message translates to:
  /// **'Pathology'**
  String get reportTypePathology;

  /// helpers screen text
  ///
  /// In en, this message translates to:
  /// **'Health Check'**
  String get reportTypeHealthCheck;

  /// helpers screen text
  ///
  /// In en, this message translates to:
  /// **'Other'**
  String get reportTypeOther;

  /// helpers screen text
  ///
  /// In en, this message translates to:
  /// **'Uploaded'**
  String get procUploaded;

  /// helpers screen text
  ///
  /// In en, this message translates to:
  /// **'Analyzing…'**
  String get procAnalyzing;

  /// helpers screen text
  ///
  /// In en, this message translates to:
  /// **'Completed'**
  String get procCompleted;

  /// helpers screen text
  ///
  /// In en, this message translates to:
  /// **'Failed'**
  String get procFailed;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Summarize my results'**
  String get quickSummarize;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'What values are abnormal?'**
  String get quickAbnormal;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Is anything urgent?'**
  String get quickUrgent;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'What should I ask my doctor?'**
  String get quickAskDoctor;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Reference'**
  String get chatReference;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Source: {name}'**
  String chatSourceLine(String name);

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'AI answers are for information only and do not replace professional medical advice. Always consult your doctor.'**
  String get chatDisclaimer;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Ask about your report'**
  String get chatAskAboutReport;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Get plain-language answers about your results, medicines and what to ask your doctor.'**
  String get chatEmptyBody;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Ask about your report...'**
  String get chatHintAsk;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Your message was shortened to fit the {max}-character limit.'**
  String chatMessageShortened(int max);

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Could not load the conversation. Please try again.'**
  String get chatCouldNotLoad;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Online'**
  String get chatOnline;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Offline'**
  String get chatOffline;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Back online! Refreshing...'**
  String get offlineBackOnline;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'You\'re offline. Viewing cached data.'**
  String get offlineViewingCached;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Voice input'**
  String get voiceInputLabel;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Speak your message'**
  String get voiceSpeakYourMessage;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Cancel transcription'**
  String get voiceCancelTranscription;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Discard recording'**
  String get voiceDiscardRecording;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Discard'**
  String get voiceDiscard;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Converting speech to text…'**
  String get voiceConverting;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Finish and convert to text'**
  String get voiceFinishConvert;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Spoken language: {language}'**
  String voiceSpokenLanguage(String language);

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Speak in'**
  String get voiceSpeakIn;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Microphone access is turned off. Allow it for MedNarrate in your device settings to use voice input.'**
  String get voiceMicOff;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Could not start recording. Please try again.'**
  String get voiceCouldNotStart;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Nothing was recorded. Please try again.'**
  String get voiceNothingRecorded;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'That was too short. Tap the mic, speak, then tap the tick.'**
  String get voiceTooShort;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Couldn\'t hear anything. Try again, a little closer to the microphone.'**
  String get voiceNoSpeech;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Voice input is not available right now. You can type instead.'**
  String get voiceUnavailableType;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Voice input failed. Please try again or type your message.'**
  String get voiceFailed;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'The request timed out. Check your connection and try again.'**
  String get apiTimeout;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Unable to connect to MedNarrate. Check that the backend is running and try again.'**
  String get apiCannotConnect;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Something went wrong while contacting MedNarrate. Please try again.'**
  String get apiGenericError;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Session expired. Please log in again.'**
  String get apiSessionExpired;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Voice input needs an internet connection. You can still type.'**
  String get apiVoiceNeedsInternet;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'The selected file could not be read. Please select it again from Finder.'**
  String get apiFileUnreadable;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Incorrect email or password'**
  String get srvIncorrectCredentials;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'You already have an account'**
  String get srvAlreadyHaveAccount;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Account is temporarily locked due to multiple failed login attempts'**
  String get srvAccountLocked;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Account is inactive'**
  String get srvAccountInactive;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Invalid or expired refresh token'**
  String get srvInvalidRefresh;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Invalid password'**
  String get srvInvalidPassword;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Password is incorrect'**
  String get srvPasswordIncorrect;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Not authenticated'**
  String get srvNotAuthenticated;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Could not validate credentials'**
  String get srvCouldNotValidate;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Token has expired'**
  String get srvTokenExpired;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Invalid token'**
  String get srvInvalidToken;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'User not found'**
  String get srvUserNotFound;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Invalid or expired reset token'**
  String get srvResetInvalid;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Reset token has expired. Please request a new one.'**
  String get srvResetExpired;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Invalid or reused OTP code'**
  String get srvOtpInvalid;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Voice input is busy right now. Please try again in a minute, or type your message.'**
  String get srvVoiceBusy;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Voice input is not set up correctly on the server.'**
  String get srvVoiceMisconfigured;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Voice input is not set up on the server yet.'**
  String get srvVoiceNotSetUp;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Voice input took too long. Please try again.'**
  String get srvVoiceTooLong;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'The server could not reach the voice service. Please try again.'**
  String get srvVoiceNetwork;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Voice input is temporarily unavailable. You can still type your message.'**
  String get srvVoiceUnavailable;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'That recording could not be read. Please try again.'**
  String get srvVoiceUnreadable;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'That audio format is not supported.'**
  String get srvVoiceFormat;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'The recording is empty.'**
  String get srvVoiceEmpty;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Voice input is not enabled.'**
  String get srvVoiceDisabled;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Medicine Reminder: {name}'**
  String medAlertTitle(String name);

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Time to take your medicine'**
  String get medAlertBody;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Authenticate to access your medical records'**
  String get bioReasonAccessRecords;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Verify your current biometric to continue'**
  String get bioReasonVerifyCurrent;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Authenticate using fingerprint or Face ID to enable Biometric App Lock'**
  String get bioReasonEnable;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Authenticate using fingerprint or Face ID to disable Biometric App Lock'**
  String get bioReasonDisable;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Track your progress over time'**
  String get insightsTrackProgress;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'No reports available for comparison.'**
  String get insightsNoReports;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Select Reports (Max 5)'**
  String get insightsSelectReports;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'What changed since your last report?'**
  String get insightsWhatChanged;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Failed to load reports: {error}'**
  String insightsFailedToLoad(String error);

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Maximum 5 reports can be selected for comparison.'**
  String get insightsMax5;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Select at least 2 reports to compare.'**
  String get insightsSelectAtLeast2;

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Failed to generate comparison: {error}'**
  String insightsFailedCompare(String error);

  /// chat_services screen text
  ///
  /// In en, this message translates to:
  /// **'Normal: {range} {unit}'**
  String insightsNormalRange(String range, String unit);

  /// offline screen text
  ///
  /// In en, this message translates to:
  /// **'No saved chat is available offline.'**
  String get apiNoSavedChat;

  /// offline screen text
  ///
  /// In en, this message translates to:
  /// **'This file cannot be saved for offline upload. Select a local file.'**
  String get apiCannotSaveOffline;

  /// offline screen text
  ///
  /// In en, this message translates to:
  /// **'The report must be 25 MB or smaller.'**
  String get apiReportTooLarge;

  /// offline screen text
  ///
  /// In en, this message translates to:
  /// **'This report is not available offline.'**
  String get apiReportNotOffline;

  /// offline screen text
  ///
  /// In en, this message translates to:
  /// **'This analysis is not available offline.'**
  String get apiAnalysisNotOffline;

  /// offline screen text
  ///
  /// In en, this message translates to:
  /// **'Chat requires a connection. Saved messages remain available offline.'**
  String get apiChatNeedsConnection;

  /// offline screen text
  ///
  /// In en, this message translates to:
  /// **'Translation returned an unexpected language or empty report.'**
  String get apiTranslationUnexpected;

  /// licenses screen text
  ///
  /// In en, this message translates to:
  /// **'Open Source Licenses'**
  String get licensesTitle;

  /// licenses screen text
  ///
  /// In en, this message translates to:
  /// **'Search packages...'**
  String get licensesSearchHint;

  /// licenses screen text
  ///
  /// In en, this message translates to:
  /// **'No licenses match \"{query}\"'**
  String licensesNoMatch(String query);

  /// licenses screen text
  ///
  /// In en, this message translates to:
  /// **'1 license'**
  String get licensesCountOne;

  /// licenses screen text
  ///
  /// In en, this message translates to:
  /// **'{count} licenses'**
  String licensesCountMany(int count);

  /// licenses screen text
  ///
  /// In en, this message translates to:
  /// **'License {index} of {total}'**
  String licensesIndexOf(int index, int total);

  /// insights screen text
  ///
  /// In en, this message translates to:
  /// **'Nothing to compare yet'**
  String get insightsNoCommonTitle;

  /// insights screen text
  ///
  /// In en, this message translates to:
  /// **'The selected reports do not share a test with a number in both, such as hemoglobin or cholesterol. Pick reports of the same kind, for example two blood counts, to see how your results changed.'**
  String get insightsNoCommonBody;

  /// general_chat screen text
  ///
  /// In en, this message translates to:
  /// **'Ask me about your health'**
  String get chatAskHealthTitle;

  /// general_chat screen text
  ///
  /// In en, this message translates to:
  /// **'Get simple answers on fitness, food, sleep, common symptoms and what your test terms mean. For your own report, open it and use its Chat tab.'**
  String get chatAskHealthBody;

  /// general_chat screen text
  ///
  /// In en, this message translates to:
  /// **'Ask a health question...'**
  String get chatHintAskHealth;

  /// general_chat screen text
  ///
  /// In en, this message translates to:
  /// **'Give me a beginner workout plan'**
  String get chatSuggestWorkout;

  /// general_chat screen text
  ///
  /// In en, this message translates to:
  /// **'What does a balanced daily diet look like?'**
  String get chatSuggestDiet;

  /// general_chat screen text
  ///
  /// In en, this message translates to:
  /// **'How can I sleep better?'**
  String get chatSuggestSleep;

  /// general_chat screen text
  ///
  /// In en, this message translates to:
  /// **'What do common blood test terms mean?'**
  String get chatSuggestTerms;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) => <String>[
        'bn',
        'en',
        'hi',
        'kn',
        'ml',
        'mr',
        'ta',
        'te'
      ].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'bn':
      return AppLocalizationsBn();
    case 'en':
      return AppLocalizationsEn();
    case 'hi':
      return AppLocalizationsHi();
    case 'kn':
      return AppLocalizationsKn();
    case 'ml':
      return AppLocalizationsMl();
    case 'mr':
      return AppLocalizationsMr();
    case 'ta':
      return AppLocalizationsTa();
    case 'te':
      return AppLocalizationsTe();
  }

  throw FlutterError(
      'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
      'an issue with the localizations generation tool. Please file an issue '
      'on GitHub with a reproducible sample app and the gen-l10n configuration '
      'that was used.');
}
