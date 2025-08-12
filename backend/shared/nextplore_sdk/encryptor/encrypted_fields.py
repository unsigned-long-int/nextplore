from typing import Set


ENCRYPTED_FIELDS: Set[str] = {
    'encrypted_username', 
    'encrypted_password', 
    'encrypted_keberos_principal',
    'encrypted_windows_domain',
    'encrypted_extra_options'
}
