def make_error(message, error: bool = False):
    return f"```{'css' if error else 'fix'}\n[ERROR: {message}]\n```"


def make_success(message):
    return f'```diff\n+ {message}\n```'


class InfactumException(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class ExternalImportError(InfactumException):
    def __init__(self, msg):
        super().__init__(msg)


class UserDatabaseError(InfactumException):
    def __init__(self, msg):
        super().__init__(msg)


class InputMatchError(InfactumException):
    def __init__(self, msg):
        super().__init__(msg)


class GuildPermissionError(InfactumException):
    def __init__(self, msg):
        super().__init__(msg)


class ArgumentError(InfactumException):
    def __init__(self, msg):
        super().__init__(msg)
