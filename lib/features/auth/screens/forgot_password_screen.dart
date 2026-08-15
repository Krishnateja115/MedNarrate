import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/api_exception.dart';
import '../../../core/routing/routes.dart';
import '../../../shared/widgets/custom_textfield.dart';

/// ForgotPasswordScreen — two-step flow:
/// Step 1: Enter email → get reset token (in dev mode shown on screen)
/// Step 2: Enter token + new password → reset
class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _emailCtrl = TextEditingController();
  final _tokenCtrl = TextEditingController();
  final _newPassCtrl = TextEditingController();

  bool _loading = false;
  String? _error;
  String? _devToken;
  bool _step2 = false;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _tokenCtrl.dispose();
    _newPassCtrl.dispose();
    super.dispose();
  }

  Future<void> _requestReset() async {
    final email = _emailCtrl.text.trim();
    if (email.isEmpty) {
      setState(() => _error = 'Please enter your email address.');
      return;
    }
    setState(() { _loading = true; _error = null; });
    try {
      final result = await ApiService.instance.forgotPassword(email);
      if (mounted) {
        setState(() {
          _devToken = result['dev_token'];
          _step2 = true;
          _loading = false;
        });
      }
    } on ApiException catch (e) {
      if (mounted) setState(() { _error = e.message; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _loading = false; });
    }
  }

  Future<void> _resetPassword() async {
    final token = _tokenCtrl.text.trim();
    final newPass = _newPassCtrl.text.trim();
    if (token.isEmpty || newPass.isEmpty) {
      setState(() => _error = 'Please fill in all fields.');
      return;
    }
    if (newPass.length < 8) {
      setState(() => _error = 'Password must be at least 8 characters.');
      return;
    }
    setState(() { _loading = true; _error = null; });
    try {
      await ApiService.instance.resetPassword(token: token, newPassword: newPass);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Password reset successfully! Please log in.'),
          backgroundColor: Color(0xFF00C48C),
        ),
      );
      context.go(Routes.login);
    } on ApiException catch (e) {
      if (mounted) setState(() { _error = e.message; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        elevation: 0,
        title: Text('Reset Password'),
        leading: IconButton(
          icon: Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(height: 24),
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Icon(Icons.lock_reset, color: AppColors.primary, size: 48),
              ),
              SizedBox(height: 28),
              Text(
                _step2 ? 'Set New Password' : 'Forgot Password?',
                style: TextStyle(color: Theme.of(context).colorScheme.onSurface, fontSize: 28, fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 10),
              Text(
                _step2
                    ? 'Enter the reset token and your new password below.'
                    : "Enter your email and we'll send you a reset token.",
                style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.60), fontSize: 15, height: 1.5),
              ),
              SizedBox(height: 32),

              if (!_step2) ...[
              CustomTextField(
                  controller: _emailCtrl,
                  label: 'Email Address',
                  icon: Icons.email_outlined,
                  keyboardType: TextInputType.emailAddress,
                ),
                SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  height: 54,
                  child: FilledButton(
                    onPressed: _loading ? null : _requestReset,
                    style: FilledButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    ),
                    child: _loading
                        ? SizedBox(width: 22, height: 22, child: CircularProgressIndicator(color: Theme.of(context).colorScheme.onSurface, strokeWidth: 2))
                        : Text('Send Reset Token', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  ),
                ),
              ] else ...[
                if (_devToken != null)
                  Container(
                    padding: const EdgeInsets.all(14),
                    margin: const EdgeInsets.only(bottom: 20),
                    decoration: BoxDecoration(
                      color: Color(0xFF1C2128),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.tealAccent.shade400.withValues(alpha: 0.4)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(children: [
                          Icon(Icons.developer_mode, color: Colors.tealAccent.shade400, size: 16),
                          SizedBox(width: 8),
                          Text('Dev Mode — Reset Token:', style: TextStyle(color: Colors.tealAccent.shade400, fontSize: 12, fontWeight: FontWeight.bold)),
                        ]),
                        SizedBox(height: 8),
                        SelectableText(
                          _devToken!,
                          style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.70), fontSize: 12, fontFamily: 'monospace'),
                        ),
                      ],
                    ),
                  ),
                CustomTextField(
                  controller: _tokenCtrl,
                  label: 'Reset Token',
                  icon: Icons.key_outlined,
                ),
                SizedBox(height: 16),
                CustomTextField(
                  controller: _newPassCtrl,
                  label: 'New Password',
                  icon: Icons.lock_outline,
                  obscureText: true,
                ),
                SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  height: 54,
                  child: FilledButton(
                    onPressed: _loading ? null : _resetPassword,
                    style: FilledButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    ),
                    child: _loading
                        ? SizedBox(width: 22, height: 22, child: CircularProgressIndicator(color: Theme.of(context).colorScheme.onSurface, strokeWidth: 2))
                        : Text('Reset Password', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  ),
                ),
                SizedBox(height: 16),
                Center(
                  child: TextButton(
                    onPressed: () => setState(() { _step2 = false; _devToken = null; _error = null; }),
                    child: Text('Back to Email', style: TextStyle(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.54))),
                  ),
                ),
              ],

              if (_error != null) ...[
                SizedBox(height: 16),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.red.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: Colors.red.withValues(alpha: 0.3)),
                  ),
                  child: Row(children: [
                    Icon(Icons.error_outline, color: Colors.red, size: 18),
                    SizedBox(width: 10),
                    Expanded(child: Text(_error!, style: TextStyle(color: Colors.red, fontSize: 13))),
                  ]),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}