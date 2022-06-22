class InfactumException(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class ExternalImportError(InfactumException):
    def __init__(self, msg):
        super().__init__(msg)


class GuildPermissionError(InfactumException):
    def __init__(self, msg):
        super().__init__(msg)


class ArgumentError(InfactumException):
    def __init__(self, msg):
        super().__init__(msg)
