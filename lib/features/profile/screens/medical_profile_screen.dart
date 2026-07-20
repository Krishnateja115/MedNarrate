import 'package:flutter/material.dart';
import 'emergency_contact_screen.dart';
import '../../../core/constants/app_colors.dart';
import '../../../shared/widgets/custom_textfield.dart';
import '../../../shared/widgets/primary_button.dart';

class MedicalProfileScreen extends StatefulWidget {

  const MedicalProfileScreen({super.key});

  @override
  State<MedicalProfileScreen> createState() =>
      _MedicalProfileScreenState();
}

class _MedicalProfileScreenState
    extends State<MedicalProfileScreen> {

  final ageController = TextEditingController();

  final bloodController = TextEditingController();

  final heightController = TextEditingController();

  final weightController = TextEditingController();

  final allergyController = TextEditingController();

  final diseaseController = TextEditingController();

  final medicineController = TextEditingController();

  String gender = "Male";

  @override
  Widget build(BuildContext context) {

    return Scaffold(

      backgroundColor: AppColors.background,

      appBar: AppBar(
        title: const Text("Medical Profile"),
      ),

      body: SingleChildScrollView(

        padding: const EdgeInsets.all(24),

        child: Column(

          crossAxisAlignment: CrossAxisAlignment.start,

          children: [

            const SizedBox(height: 10),

            const Text(

              "Let's personalize your experience.",

              style: TextStyle(
                color: Colors.white70,
                fontSize: 17,
              ),

            ),

            const SizedBox(height: 35),

            CustomTextField(
              controller: ageController,
              label: "Age",
              icon: Icons.cake_outlined,
              keyboardType: TextInputType.number,
            ),

            const SizedBox(height: 20),

            DropdownButtonFormField(

              dropdownColor: AppColors.card,

              initialValue: gender,

              decoration: InputDecoration(

                filled: true,

                fillColor: AppColors.card,

                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(18),
                ),

              ),

              items: const [

                DropdownMenuItem(
                  value: "Male",
                  child: Text("Male"),
                ),

                DropdownMenuItem(
                  value: "Female",
                  child: Text("Female"),
                ),

                DropdownMenuItem(
                  value: "Other",
                  child: Text("Other"),
                ),

              ],

              onChanged: (value) {

                setState(() {

                  gender = value!;

                });

              },

            ),

            const SizedBox(height: 20),

            CustomTextField(
              controller: bloodController,
              label: "Blood Group",
              icon: Icons.bloodtype_outlined,
            ),

            const SizedBox(height: 20),

            CustomTextField(
              controller: heightController,
              label: "Height (cm)",
              icon: Icons.height,
            ),

            const SizedBox(height: 20),

            CustomTextField(
              controller: weightController,
              label: "Weight (kg)",
              icon: Icons.monitor_weight_outlined,
            ),

            const SizedBox(height: 20),

            CustomTextField(
              controller: allergyController,
              label: "Allergies",
              icon: Icons.warning_amber_outlined,
            ),

            const SizedBox(height: 20),

            CustomTextField(
              controller: diseaseController,
              label: "Existing Diseases",
              icon: Icons.local_hospital_outlined,
            ),

            const SizedBox(height: 20),

            CustomTextField(
              controller: medicineController,
              label: "Current Medicines",
              icon: Icons.medication_outlined,
            ),

            const SizedBox(height: 40),

            PrimaryButton(

              text: "Continue",

              onPressed: () {

                Navigator.push(

                  context,

                  MaterialPageRoute(

                    builder: (_) => const EmergencyContactScreen(),

                  ),

                );

              },

            ),

            const SizedBox(height: 30),

          ],

        ),

      ),

    );

  }

}