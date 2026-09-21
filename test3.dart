import 'dart:io';
void main() async {
  await Process.start('/bin/bash', ['-lc', 'cd "/Users/harsha/Downloads/Sem 5/NLP/MedNarrate-main/mednarrate-backend" && (export PATH="/opt/homebrew/bin:/opt/anaconda3/bin:/usr/local/bin:\$PATH"; python3 -c "import sys, os; print(os.getcwd()); print(sys.path); import app") > /tmp/env2.log 2>&1']);
}
