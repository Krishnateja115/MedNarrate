import 'package:flutter/material.dart';

class PersonalInfoScreen extends StatelessWidget {
  const PersonalInfoScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF151B2F),

      appBar: AppBar(
        backgroundColor: const Color(0xFF151B2F),
        elevation: 0,
        title: const Text(
          "Personal Information",
          style: TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),

      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),

        child: Column(
          children: [

            const CircleAvatar(
              radius: 50,
              backgroundColor: Color(0xFF4F6BFF),
              child: Icon(
                Icons.person,
                size: 55,
                color: Colors.white,
              ),
            ),

            const SizedBox(height: 30),

            infoTile("Full Name", "Krishna", Icons.person),
            infoTile("Age", "21 Years", Icons.cake),
            infoTile("Gender", "Male", Icons.male),
            infoTile("Date of Birth", "01 Jan 2005", Icons.calendar_month),
            infoTile("Blood Group", "O+", Icons.bloodtype),
            infoTile("Height", "175 cm", Icons.height),
            infoTile("Weight", "68 kg", Icons.monitor_weight),
            infoTile("Phone", "+91 9876543210", Icons.phone),
            infoTile("Email", "krishna@email.com", Icons.email),
            infoTile("Address", "Coimbatore, Tamil Nadu", Icons.location_on),

            const SizedBox(height: 30),

            SizedBox(
              width: double.infinity,
              height: 55,
              child: ElevatedButton.icon(
                onPressed: () {
                  // Edit Profile screen later
                },
                icon: const Icon(Icons.edit),
                label: const Text(
                  "Edit Profile",
                  style: TextStyle(fontSize: 18),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget infoTile(String title, String value, IconData icon) {
    return Container(
      margin: const EdgeInsets.only(bottom: 15),
      padding: const EdgeInsets.all(18),

      decoration: BoxDecoration(
        color: const Color(0xFF252C42),
        borderRadius: BorderRadius.circular(18),
      ),

      child: Row(
        children: [

          Icon(
            icon,
            color: Colors.white,
          ),

          const SizedBox(width: 18),

          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [

                Text(
                  title,
                  style: const TextStyle(
                    color: Colors.white54,
                    fontSize: 13,
                  ),
                ),

                const SizedBox(height: 4),

                Text(
                  value,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 17,
                    fontWeight: FontWeight.bold,
                  ),
                ),

              ],
            ),
          ),

        ],
      ),
    );
  }
}