import 'package:flutter/material.dart';
import '../../profile/screens/medical_profile_screen.dart';
import '../../../core/constants/app_colors.dart';
import '../../../shared/widgets/custom_textfield.dart';
import '../../../shared/widgets/primary_button.dart';

class SignupScreen extends StatefulWidget {
  const SignupScreen({super.key});

  @override
  State<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends State<SignupScreen> {

  final nameController = TextEditingController();

  final emailController = TextEditingController();

  final phoneController = TextEditingController();

  final passwordController = TextEditingController();

  final confirmPasswordController = TextEditingController();

  bool obscurePassword = true;

  bool obscureConfirmPassword = true;

  @override
  Widget build(BuildContext context) {

    return Scaffold(

      backgroundColor: AppColors.background,

      body: SafeArea(

        child: SingleChildScrollView(

          padding: const EdgeInsets.all(24),

          child: Column(

            crossAxisAlignment: CrossAxisAlignment.start,

            children: [

              const SizedBox(height: 30),

              const Text(
                "Create Account",
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 34,
                  fontWeight: FontWeight.bold,
                ),
              ),

              const SizedBox(height: 10),

              const Text(
                "Let's personalize your health journey.",
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 17,
                ),
              ),

              const SizedBox(height: 40),

              CustomTextField(
                controller: nameController,
                label: "Full Name",
                icon: Icons.person_outline,
              ),

              const SizedBox(height: 20),

              CustomTextField(
                controller: emailController,
                label: "Email Address",
                icon: Icons.email_outlined,
              ),

              const SizedBox(height: 20),

              CustomTextField(
                controller: phoneController,
                label: "Phone Number",
                icon: Icons.phone_outlined,
              ),

              const SizedBox(height: 20),

              TextField(

                controller: passwordController,

                obscureText: obscurePassword,

                style: const TextStyle(
                  color: Colors.white,
                ),

                decoration: InputDecoration(

                  labelText: "Password",

                  labelStyle: const TextStyle(
                    color: Colors.white70,
                  ),

                  prefixIcon: const Icon(
                    Icons.lock_outline,
                  ),

                  suffixIcon: IconButton(

                    onPressed: () {

                      setState(() {

                        obscurePassword = !obscurePassword;

                      });

                    },

                    icon: Icon(
                      obscurePassword
                          ? Icons.visibility_off
                          : Icons.visibility,
                    ),
                  ),

                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(18),
                  ),

                ),

              ),

              const SizedBox(height: 20),

              TextField(

                controller: confirmPasswordController,

                obscureText: obscureConfirmPassword,

                style: const TextStyle(
                  color: Colors.white,
                ),

                decoration: InputDecoration(

                  labelText: "Confirm Password",

                  labelStyle: const TextStyle(
                    color: Colors.white70,
                  ),

                  prefixIcon: const Icon(
                    Icons.lock_outline,
                  ),

                  suffixIcon: IconButton(

                    onPressed: () {

                      setState(() {

                        obscureConfirmPassword =
                            !obscureConfirmPassword;

                      });

                    },

                    icon: Icon(
                      obscureConfirmPassword
                          ? Icons.visibility_off
                          : Icons.visibility,
                    ),
                  ),

                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(18),
                  ),

                ),

              ),

              const SizedBox(height: 35),

              PrimaryButton(

                text: "Continue",

                onPressed: () {

                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => const MedicalProfileScreen(),
                    ),
                  );

                },

              ),

              const SizedBox(height: 35),

              Center(

                child: TextButton(

                  onPressed: () {

                  },

                  child: const Text(

                    "Already have an account? Login",

                    style: TextStyle(
                      fontSize: 16,
                    ),

                  ),

                ),

              )

            ],

          ),

        ),

      ),

    );

  }

}