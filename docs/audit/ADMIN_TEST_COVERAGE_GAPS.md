# Admin Test Coverage Gaps

1. **Fake Asserts / Placeholders**: Tests for features like Feature Flags and Announcements may not actually test end-to-end functionality since those features are functionally disconnected.
2. **Notifications**: Tests pass for notifications because the backend mocks the dispatch internally, hiding the lack of real delivery.
