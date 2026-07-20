import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../shared/widgets/custom_textfield.dart';
import '../../../shared/widgets/primary_button.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() =>
      _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState
    extends State<ForgotPasswordScreen> {

  final emailController = TextEditingController();

  @override
  Widget build(BuildContext context) {

    return Scaffold(

      backgroundColor: AppColors.background,

      appBar: AppBar(),

      body: Padding(

        padding: const EdgeInsets.all(24),

        child: Column(

          crossAxisAlignment: CrossAxisAlignment.start,

          children: [

            const SizedBox(height: 30),

            const Text(
              "Reset Password",
              style: TextStyle(
                fontSize: 32,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),

            const SizedBox(height: 12),

            const Text(
              "Enter your email address.",
              style: TextStyle(
                color: Colors.white70,
              ),
            ),

            const SizedBox(height: 35),

            CustomTextField(
              controller: emailController,
              label: "Email",
              icon: Icons.email_outlined,
            ),

            const SizedBox(height: 35),

            PrimaryButton(
              text: "Send Reset Link",
              onPressed: () {},
            ),

          ],

        ),

      ),

    );

  }

}