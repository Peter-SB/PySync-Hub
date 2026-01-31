# Testing

Unit test library with AAA style loosely in mind 

## Unit Tests
Unit tests that just tests deterministic code. Functions, my endpoint, sqlite_temporaty database interactions

## Mocking 

Mocking should be kept to a minimum and mostly just for external services. Responses should be saved in advance in `mock_data/` and can be injected in for testing

- Each platform service should have a mock classes
- dlp too

## Integration 
Tests that are only run locally and will test full flows and interactions with live services such as live platforms and downloading.

- Each service should have a sync integration test