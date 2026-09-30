class TransientError(Exception):
    """An error that should be retried."""
    pass

class PermanentError(Exception):
    """An error that should not be retried."""
    pass
