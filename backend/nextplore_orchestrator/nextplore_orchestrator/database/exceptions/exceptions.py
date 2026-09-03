class OrganizationCreateFailed(Exception):
    pass


class UserCreateFailed(Exception):
    pass


class OrganizationGetFailed(Exception):
    pass


class UserGetFailed(Exception):
    pass


class KekIdGetFailed(Exception):
    pass


class KekIdNotFound(Exception):
    pass


class OnboardingRequestGetFailed(Exception):
    pass


class OnboardingRequestCreateFailed(Exception):
    pass


class OnboardingRequestDeleteFailed(Exception):
    pass


class OnboardingRequestUpdateFailed(Exception):
    pass


class EmailOutboxCreateFailed(Exception):
    pass
