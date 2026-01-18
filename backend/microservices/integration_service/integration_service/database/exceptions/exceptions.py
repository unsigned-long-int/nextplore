class IntegrationUpdateFailed(Exception):
    pass


class IntegrationDeleteFailed(Exception):
    pass


class IntegrationNotFound(Exception):
    pass


class IntegrationCreateFailed(Exception):
    pass


class IntegrationGetFailed(Exception):
    pass


class SecretsCreateFailed(Exception):
    pass


class SecretsGetFailed(Exception):
    pass


class SecretsVersionGetFailed(Exception):
    pass


class CertCreateFailed(Exception):
    pass


class CertGetFailed(Exception):
    pass
