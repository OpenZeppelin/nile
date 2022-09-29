"""HTTP response object mock."""


class MockResponse:
    """Mock class."""

    def __init__(self, json_data, status_code):
        """Initialize instance."""
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        """Return JSON data."""
        return self.json_data
