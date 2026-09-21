import 'dart:io';
void main() async {
  await Process.start('/bin/bash', ['-lc', 'env > /tmp/env.log']);
}
