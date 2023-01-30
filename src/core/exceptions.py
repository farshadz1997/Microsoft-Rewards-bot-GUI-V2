
class AccountSuspendedException(Exception):
    """Exception raised when an account gets suspended."""


class AccountLockedException(Exception):
    """Exception raised when an account gets locked."""


class RegionException(Exception):
    """Exception raised when Microsoft Rewards not available in a region."""
    
    
class UnusualActivityException(Exception):
    """Exception raised when Microsoft returns unusual activity detected"""
    

class UnhandledException(Exception):
    """Exception raised when Microsoft returns unhandled error"""