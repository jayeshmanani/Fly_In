"""Custom exceptions for the Fly-in simulation."""


class ParseError(Exception):
    """Raised when a map file contains invalid syntax or structure."""

    def __init__(self, line_number: int, message: str) -> None:
        """Initialize with line number and error description."""
        self.line_number = line_number
        self.message = message
        super().__init__(f"Line {line_number}: {message}")
