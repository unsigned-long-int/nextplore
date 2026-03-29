class DataStoreUpdateFailed(Exception):
    pass


class DataStoreDeleteFailed(Exception):
    pass


class DataStoreNotFound(Exception):
    pass


class DataStoreCreateFailed(Exception):
    pass


class DataStoreGetFailed(Exception):
    pass


class SecretsCreateFailed(Exception):
    pass


class SecretsGetFailed(Exception):
    pass


class KekKidGetFailed(Exception):
    pass


class CertCreateFailed(Exception):
    pass


class CertGetFailed(Exception):
    pass


class UserLlmCreateFailed(Exception):
    pass

class UserLlmGetFailed(Exception):
    pass
