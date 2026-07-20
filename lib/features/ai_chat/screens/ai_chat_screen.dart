import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';

class AIChatScreen extends StatefulWidget {
  const AIChatScreen({super.key});

  @override
  State<AIChatScreen> createState() => _AIChatScreenState();
}

class _AIChatScreenState extends State<AIChatScreen> {
  final TextEditingController messageController =
      TextEditingController();

  final List<Map<String, dynamic>> messages = [
    {
      "isUser": false,
      "message":
          "Hello Krishna 👋\n\nI'm MedNarrate AI.\n\nUpload a medical report or ask me any health-related question regarding your reports.",
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,

      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        centerTitle: false,

        title: const Row(
          children: [

            CircleAvatar(
              radius: 20,
              child: Icon(Icons.smart_toy),
            ),

            SizedBox(width: 12),

            Column(
              crossAxisAlignment:
                  CrossAxisAlignment.start,

              children: [

                Text(
                  "MedNarrate AI",
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),

                Text(
                  "Online",
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.green,
                  ),
                ),

              ],
            ),

          ],
        ),
      ),

      body: Column(
        children: [

          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(18),
              itemCount: messages.length,

              itemBuilder: (context, index) {

                final msg = messages[index];

                return Align(
                  alignment: msg["isUser"]
                      ? Alignment.centerRight
                      : Alignment.centerLeft,

                  child: Container(
                    margin:
                        const EdgeInsets.only(bottom: 18),

                    padding:
                        const EdgeInsets.all(18),

                    constraints:
                        const BoxConstraints(
                      maxWidth: 320,
                    ),

                    decoration: BoxDecoration(
                      color: msg["isUser"]
                          ? AppColors.primary
                          : AppColors.card,

                      borderRadius:
                          BorderRadius.circular(20),
                    ),

                    child: Text(
                      msg["message"],
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        height: 1.5,
                      ),
                    ),
                  ),
                );
              },
            ),
          ),

          Container(
            padding: const EdgeInsets.all(15),

            decoration: BoxDecoration(
              color: AppColors.card,
              borderRadius: const BorderRadius.vertical(
                top: Radius.circular(25),
              ),
            ),

            child: Row(
              children: [

                Expanded(
                  child: TextField(
                    controller: messageController,

                    style: const TextStyle(
                      color: Colors.white,
                    ),

                    decoration: const InputDecoration(
                      hintText:
                          "Ask about your report...",
                      border: InputBorder.none,
                    ),
                  ),
                ),

                IconButton(
                  onPressed: () {

                    if (messageController.text.trim().isEmpty) {
                      return;
                    }

                    setState(() {

                      messages.add({

                        "isUser": true,

                        "message":
                            messageController.text,

                      });

                      messageController.clear();

                    });

                  },
                  icon: const Icon(
                    Icons.send_rounded,
                    color: Colors.blue,
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