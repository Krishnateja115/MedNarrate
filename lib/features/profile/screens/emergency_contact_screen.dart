import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../shared/widgets/custom_textfield.dart';
import '../../../shared/widgets/primary_button.dart';
import '../../navigation/screens/main_navigation_screen.dart';
class EmergencyContactScreen extends StatefulWidget {
  const EmergencyContactScreen({super.key});

  @override
  State<EmergencyContactScreen> createState() =>
      _EmergencyContactScreenState();
}

class _EmergencyContactScreenState
    extends State<EmergencyContactScreen> {

  final contactName = TextEditingController();

  final relationship = TextEditingController();

  final phone = TextEditingController();

  @override
  Widget build(BuildContext context) {

    return Scaffold(

      backgroundColor: AppColors.background,

      appBar: AppBar(
        title: const Text("Emergency Contact"),
      ),

      body: SafeArea(

        child: SingleChildScrollView(

          padding: const EdgeInsets.all(24),

          child: Column(

            crossAxisAlignment: CrossAxisAlignment.start,

            children: [

              const SizedBox(height: 15),

              const Text(
                "Emergency Contact",
                style: TextStyle(
                  fontSize: 30,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),

              const SizedBox(height: 10),

              const Text(
                "We'll use this only during emergencies.",
                style: TextStyle(
                  color: Colors.white70,
                ),
              ),

              const SizedBox(height: 35),

              CustomTextField(
                controller: contactName,
                label: "Full Name",
                icon: Icons.person_outline,
              ),

              const SizedBox(height: 20),

              CustomTextField(
                controller: relationship,
                label: "Relationship",
                icon: Icons.people_outline,
              ),

              const SizedBox(height: 20),

              CustomTextField(
                controller: phone,
                label: "Phone Number",
                icon: Icons.phone_outlined,
                keyboardType: TextInputType.phone,
              ),

              const SizedBox(height: 40),

              PrimaryButton(

                text: "Finish Setup",

                onPressed: () {

                  Navigator.pushAndRemoveUntil(

                    context,

                    MaterialPageRoute(
                      builder: (_) => const MainNavigationScreen(),
                    ),

                    (route) => false,

                  );

                },

              )

            ],

          ),

        ),

      ),

    );

  }

}