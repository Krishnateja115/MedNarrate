import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/routing/routes.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/utils/validators.dart';
import '../../../core/utils/helpers.dart';
import '../../../shared/widgets/custom_textfield.dart';
import '../../../shared/widgets/primary_button.dart';

class SignupScreen extends StatefulWidget {
  const SignupScreen({super.key});

  @override
  State<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends State<SignupScreen> {
  final _formKey = GlobalKey<FormState>();
  final nameController = TextEditingController();
  final emailController = TextEditingController();
  final passwordController = TextEditingController();
  final confirmPasswordController = TextEditingController();
  bool obscurePassword = true;
  bool obscureConfirmPassword = true;
  bool _loading = false;

  @override
  void dispose() {
    nameController.dispose();
    emailController.dispose();
    passwordController.dispose();
    confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _signup() async {
    if (!_formKey.currentState!.validate()) return;
    if (passwordController.text != confirmPasswordController.text) {
      Helpers.showError(context, 'Passwords do not match');
      return;
    }
    setState(() => _loading = true);
    try {
      await ApiService.instance.signup(
        emailController.text.trim(),
        passwordController.text,
        nameController.text.trim(),
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
                SizedBox(height: 30),
                Text(
                  'Create Account',
                  style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontSize: 34, fontWeight: FontWeight.bold),
                ),
                SizedBox(height: 10),
                Text(
                  "Let's personalize your health journey.",
                  style: TextStyle(color: AppColors.textSecondary, fontSize: 17),
                ),
                SizedBox(height: 40),
                CustomTextField(
                  controller: nameController,
                  label: 'Full Name',
                  icon: Icons.person_outline,
                  validator: (v) => Validators.requiredField(v, fieldName: 'Full name'),
                ),
                SizedBox(height: 20),
                CustomTextField(
                  controller: emailController,
                  label: 'Email Address',
                  icon: Icons.email_outlined,
                  validator: Validators.isValidEmail,
                ),
                SizedBox(height: 20),
                TextFormField(
                  controller: passwordController,
                  obscureText: obscurePassword,
                  style: TextStyle(color: Theme.of(context).colorScheme.onSurface),
                  validator: Validators.passwordStrengthError,
                  decoration: InputDecoration(
                    labelText: 'Password',
                    labelStyle: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70)),
                    prefixIcon: Icon(Icons.lock_outline),
                    suffixIcon: IconButton(
                      onPressed: () => setState(() => obscurePassword = !obscurePassword),
                      icon: Icon(obscurePassword ? Icons.visibility_off : Icons.visibility),
                    ),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(18)),
                  ),
                ),
                SizedBox(height: 20),
                TextFormField(
                  controller: confirmPasswordController,
                  obscureText: obscureConfirmPassword,
                  style: TextStyle(color: Theme.of(context).colorScheme.onSurface),
                  validator: (v) => v == null || v.isEmpty ? 'Confirm your password' : null,
                  decoration: InputDecoration(
                    labelText: 'Confirm Password',
                    labelStyle: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70)),
                    prefixIcon: Icon(Icons.lock_outline),
                    suffixIcon: IconButton(
                      onPressed: () => setState(() => obscureConfirmPassword = !obscureConfirmPassword),
                      icon: Icon(obscureConfirmPassword ? Icons.visibility_off : Icons.visibility),
                    ),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(18)),
                  ),
                ),
                SizedBox(height: 35),
                PrimaryButton(
                  text: _loading ? 'Creating Account…' : 'Sign Up',
                  onPressed: _loading ? null : () { _signup(); },
                ),
                SizedBox(height: 35),
                Center(
                  child: TextButton(
                    onPressed: () => context.go(Routes.login),
                    child: Text(
                      'Already have an account? Login',
                      style: TextStyle(fontSize: 16),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}