import 'dart:io';

void main() async {
  try {
    final client = HttpClient();
    final req = await client.getUrl(Uri.parse('http://localhost:8000/health'));
    final res = await req.close();
    print('Status: ${res.statusCode}');
  } catch (e) {
    print('Error: $e');
  }
}
