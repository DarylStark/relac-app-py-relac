"""Module with exceptions for the library."""


class RelacError(BaseException):
    """Base class for all Relac Errors."""


class YamlRepoLoaderError(RelacError):
    """Base class for all YamlRepoLoader errors."""


class YamlLoadingError(YamlRepoLoaderError):
    """Errors that occur while loading a Yaml file."""

    def __init__(self, filename: str, error: str) -> None:
        """Call the baseclass."""
        super().__init__(f'{filename}: {error}')
