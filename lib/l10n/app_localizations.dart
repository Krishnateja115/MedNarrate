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
    Locale('te'),
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
    'te',
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
    'that was used.',
  );
}
