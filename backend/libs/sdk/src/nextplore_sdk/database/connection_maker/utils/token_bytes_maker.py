import struct


def make_token_bytes(token: str) -> bytes:
    exp_token = b'';
    for i in bytes(token, 'UTF-8'):
        exp_token += bytes({i});
        exp_token += bytes(1);

    token_struct = struct.pack('=i', len(exp_token)) + exp_token;
    return token_struct
