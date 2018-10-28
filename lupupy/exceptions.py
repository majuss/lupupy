"""The exceptions used by Lupupy."""


class LupusecException(Exception):
    """Class to throw general lupusec exception."""

    def __init__(self, error, details=None):
        """Initialize LupusecException."""
        # Call the base class constructor with the parameters it needs
        super(LupusecException, self).__init__(error[1])

        self.errcode = error[0]
        self.message = error[1]
        self.details = details

# class LupusecAuthenticationException(LupusecException):
#     """Class to throw authentication exception."""

#     pass
