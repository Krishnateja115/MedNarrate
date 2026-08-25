import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/routing/routes.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/utils/validators.dart';
import '../../../core/utils/helpers.dart';
import '../../../shared/widgets/custom_password_field.dart';
import '../../../shared/widgets/custom_textfield.dart';
import '../../../shared/widgets/primary_button.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final emailController = TextEditingController();
  final passwordController = TextEditingController();
  bool _loading = false;

  @override
  void dispose() {
    emailController.dispose();
    passwordController.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      await ApiService.instance.login(
        emailController.text.trim(),
        passwordController.text,
      );
      if (!mounted) return;
      context.go(Routes.dashboard);
    } on ApiException catch (e) {
      if (!mounted) return;
      Helpers.showError(context, e.message);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(height: 40),
                Text(AppLocalizations.of(context)!.welcomeBack,
                  style: TextStyle(fontSize: 34, color: Theme.of(context).colorScheme.onSurface, fontWeight: FontWeight.bold),
                ),
                SizedBox(height: 8),
                Text(AppLocalizations.of(context)!.signInToContinue,
                  style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70), fontSize: 17),
                ),
                SizedBox(height: 45),
                CustomTextField(
                  controller: emailController,
                  label: AppLocalizations.of(context)!.email,
                  icon: Icons.email_outlined,
                  validator: Validators.isValidEmail,
                ),
                SizedBox(height: 20),
                CustomPasswordField(
                  controller: passwordController,
                  label: AppLocalizations.of(context)!.password,
                  validator: (v) => v == null || v.isEmpty ? 'Password is required' : null,
                ),
                SizedBox(height: 15),
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton(
                    onPressed: () => context.push(Routes.forgotPassword),
                    child: Text(AppLocalizations.of(context)!.forgotPassword),
                  ),
                ),
                SizedBox(height: 25),
                PrimaryButton(
                  text: _loading ? 'Signing in…' : 'Login',
                  onPressed: _loading ? null : () { _login(); },
                ),
                SizedBox(height: 35),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(AppLocalizations.of(context)!.dontHaveAccount,
                        style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70))),
                    TextButton(
                      onPressed: () => context.go(Routes.signup),
                      child: Text(AppLocalizations.of(context)!.signUp),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}