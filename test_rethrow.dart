void main() {
  try {
    test();
  } catch (e) {
    print("Caught in main: $e");
  }
}

void test() {
  try {
    print("In try");
    throw Exception("Test");
  } catch (e) {
    print("In catch");
    rethrow;
  } finally {
    print("In finally");
  }
}
