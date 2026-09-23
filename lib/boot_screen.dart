import 'dart:io';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'core/config/app_config.dart';
import 'core/constants/app_colors.dart';
import 'core/constants/app_strings.dart';
class BootScreen extends StatelessWidget {
  final String status;
  const BootScreen({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              height: 110,
              width: 110,
              decoration: BoxDecoration(
                color: AppColors.primary,
                borderRadius: BorderRadius.circular(30),
              ),
              child: const Icon(Icons.medical_services_rounded, size: 60, color: Colors.white),
            ),
            const SizedBox(height: 28),
            const Text(AppStrings.appName, style: TextStyle(fontSize: 34, fontWeight: FontWeight.w700, color: Colors.black)),
            const SizedBox(height: 8),
            const Text(AppStrings.appTagline, style: TextStyle(fontSize: 16, color: AppColors.textSecondary)),
            const SizedBox(height: 50),
            const SizedBox(width: 28, height: 28, child: CircularProgressIndicator(strokeWidth: 3)),
            const SizedBox(height: 16),
            Text(status, style: const TextStyle(fontSize: 14, color: AppColors.textSecondary)),
          ],
        ),
      ),
    );
  }
}

class BootErrorScreen extends StatelessWidget {
  final String error;
  final VoidCallback onRetry;
  final VoidCallback? onChangeBackend;
  const BootErrorScreen({super.key, required this.error, required this.onRetry, this.onChangeBackend});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 60, color: Colors.red),
              const SizedBox(height: 16),
              const Text('Backend Connection Failed', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.black)),
              const SizedBox(height: 12),
              Text(error, textAlign: TextAlign.center, style: const TextStyle(fontSize: 14, color: AppColors.textSecondary)),
              const SizedBox(height: 32),
              ElevatedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
              ),
              if (onChangeBackend != null) ...[
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: onChangeBackend,
                  icon: const Icon(Icons.folder_open),
                  label: const Text('Change Backend Folder'),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class BootSetupScreen extends StatefulWidget {
  final String backendPath;
  final VoidCallback onComplete;

  const BootSetupScreen({
    super.key,
    required this.backendPath,
    required this.onComplete,
  });

  @override
  State<BootSetupScreen> createState() => _BootSetupScreenState();
}

class _BootSetupScreenState extends State<BootSetupScreen> {
  final List<String> _logs = [];
  bool _isSettingUp = false;
  bool _setupFailed = false;
  bool _needsApiKey = false;
  final TextEditingController _apiKeyController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _checkApiKey();
  }

  Future<void> _checkApiKey() async {
    if (kIsWeb) return;
    final envFile = File('${widget.backendPath}/.env');
    if (await envFile.exists()) {
      final content = await envFile.readAsString();
      if (!content.contains('GEMINI_API_KEY=') || 
          content.contains('GEMINI_API_KEY=""') || 
          content.contains("GEMINI_API_KEY=''")) {
        setState(() => _needsApiKey = true);
      }
    } else {
      setState(() => _needsApiKey = true);
    }
  }

  void _onOutput(String line) {
    if (!kIsWeb) {
      try {
        File('/tmp/mednarrate_setup.log').writeAsStringSync('$line\n', mode: FileMode.append);
      } catch (_) {}
    }
    if (mounted) {
      setState(() {
        _logs.add(line);
      });
      Future.delayed(const Duration(milliseconds: 50), () {
        if (_scrollController.hasClients) {
          _scrollController.animateTo(
            _scrollController.position.maxScrollExtent,
            duration: const Duration(milliseconds: 200),
            curve: Curves.easeOut,
          );
        }
      });
    }
  }

  Future<bool> _runFirstTimeBackendSetup(String backendPath) async {
    final pythonCheck = await Process.run('which', ['python3']);
    if (pythonCheck.exitCode != 0) {
      _onOutput('ERROR: python3 not found on this system. Please install Python 3.11+ from python.org and try again.');
      return false;
    }

    final venvPath = '$backendPath/venv';
    final venvDir = Directory(venvPath);
    if (!await venvDir.exists()) {
      _onOutput('Creating virtual environment...');
      final venvResult = await Process.run('python3', ['-m', 'venv', 'venv'], workingDirectory: backendPath);
      if (venvResult.exitCode != 0) {
        _onOutput('ERROR creating venv: ${venvResult.stderr}');
        return false;
      }
    } else {
      _onOutput('Virtual environment already exists, resuming setup...');
    }

    _onOutput('Installing dependencies (this may take several minutes)...');
    final pipProcess = await Process.start(
      '$venvPath/bin/pip',
      ['install', '-r', 'requirements.txt'],
      workingDirectory: backendPath,
    );
    
    pipProcess.stdout.transform(utf8.decoder).transform(const LineSplitter()).listen(_onOutput);
    pipProcess.stderr.transform(utf8.decoder).transform(const LineSplitter()).listen(_onOutput);
    
    final exitCode = await pipProcess.exitCode;
    if (exitCode != 0) {
      _onOutput('ERROR: dependency installation failed with exit code $exitCode.');
      return false;
    }

    _onOutput('Setup complete!');
    return true;
  }

  Future<void> _startSetup() async {
    setState(() {
      _isSettingUp = true;
      _setupFailed = false;
      _logs.clear();
    });

    if (!kIsWeb && _needsApiKey && _apiKeyController.text.isNotEmpty) {
      final envFile = File('${widget.backendPath}/.env');
      final exampleEnv = File('${widget.backendPath}/.env.example');
      String envContent = '';
      if (await exampleEnv.exists()) {
        envContent = await exampleEnv.readAsString();
      }
      
      if (envContent.contains('GEMINI_API_KEY=')) {
        envContent = envContent.replaceFirst(RegExp(r'GEMINI_API_KEY=.*'), 'GEMINI_API_KEY="${_apiKeyController.text.trim()}"');
      } else {
        envContent += '\nGEMINI_API_KEY="${_apiKeyController.text.trim()}"\n';
      }
      await envFile.writeAsString(envContent);
    }

    try {
      final success = await _runFirstTimeBackendSetup(widget.backendPath);
      if (success && mounted) {
        widget.onComplete();
      } else {
        if (mounted) setState(() => _setupFailed = true);
      }
    } catch (e) {
      _onOutput('Exception: $e');
      if (mounted) setState(() => _setupFailed = true);
    }
  }

  Future<void> _onChangeBackend() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('macos_backend_path');
    widget.onComplete(); // Triggers boot sequence retry which prompts for path
  }

  @override
  Widget build(BuildContext context) {
    if (!AppConfig.isLocalDevMode) {
      return const Scaffold(
        backgroundColor: Colors.white,
        body: Center(child: Text("ERROR: Setup screen is not available in production mode.", style: TextStyle(color: Colors.red))),
      );
    }

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text('First-Time Setup'),
        elevation: 0,
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'MedNarrate needs to set up its local AI backend the first time it runs on this computer. This installs some required components and may take several minutes. You only need to do this once.',
              style: TextStyle(fontSize: 16, color: Colors.black87),
            ),
            const SizedBox(height: 24),
            if (_needsApiKey && !_isSettingUp && !_setupFailed) ...[
              const Text('Gemini API Key (Optional but recommended)', style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              TextField(
                controller: _apiKeyController,
                decoration: InputDecoration(
                  hintText: 'Paste API key from aistudio.google.com/apikey',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                ),
                obscureText: true,
              ),
              const SizedBox(height: 24),
            ],
            if (!_isSettingUp && !_setupFailed)
              ElevatedButton(
                onPressed: _startSetup,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  backgroundColor: AppColors.primary,
                ),
                child: const Text('Set Up Now', style: TextStyle(fontSize: 16)),
              ),
            if (_setupFailed) ...[
              ElevatedButton.icon(
                onPressed: _startSetup,
                icon: const Icon(Icons.refresh),
                label: const Text('Retry Setup'),
                style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: _onChangeBackend,
                icon: const Icon(Icons.folder_open),
                label: const Text('Change Backend Folder'),
              ),
            ],
            if (_isSettingUp || _setupFailed) ...[
              const SizedBox(height: 24),
              const Text('Setup Progress:', style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.black87,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: ListView.builder(
                    controller: _scrollController,
                    itemCount: _logs.length,
                    itemBuilder: (context, index) {
                      return Text(
                        _logs[index],
                        style: const TextStyle(color: Colors.greenAccent, fontFamily: 'monospace', fontSize: 12),
                      );
                    },
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
