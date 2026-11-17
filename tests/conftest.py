def pytest_configure(config):
    config.addinivalue_line("markers", "unit: fast offline tests, no network or LLM calls")
    config.addinivalue_line("markers", "integration: tests that touch real storage or processes")
    config.addinivalue_line("markers", "live: tests that call live LLM APIs; require env secrets")
