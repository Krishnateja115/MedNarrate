import 'dart:developer' as developer;

void main() {
  try {
    test();
  } catch (e) {
    developer.log("Caught in main: $e");
  }
}

void test() {
  try {
    developer.log("In try");
    throw Exception("Test");
  } catch (e) {
    developer.log("In catch");
    rethrow;
  } finally {
    developer.log("In finally");
  }
}
