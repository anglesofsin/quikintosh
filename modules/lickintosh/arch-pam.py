#!/usr/bin/env python3
"""Authenticate the current Arch user through the host's complete PAM stack.

Run with /usr/bin/python3 and a clean loader environment, never with sudo.
Credentials arrive on stdin, never argv, environment, files or diagnostics.
"""
import ctypes as C
import json
import os
import pwd
import sys
from pathlib import Path


def authenticate(password, service='lickintosh-lock', library='/usr/lib/libpam.so.0', confdir=None):
    if os.getuid() == 0:
        raise RuntimeError('The lock authenticator must run as the desktop user.')
    if confdir is None and not (Path('/etc/pam.d') / service).is_file():
        raise RuntimeError('The Quickintosh host PAM policy is missing.')
    username = pwd.getpwuid(os.getuid()).pw_name
    pam = C.CDLL(library)
    libc = C.CDLL(None)
    libc.calloc.argtypes = [C.c_size_t, C.c_size_t]
    libc.calloc.restype = C.c_void_p
    libc.strdup.argtypes = [C.c_char_p]
    libc.strdup.restype = C.c_void_p
    libc.free.argtypes = [C.c_void_p]
    class Message(C.Structure):
        _fields_ = [('style', C.c_int), ('message', C.c_char_p)]
    class Response(C.Structure):
        _fields_ = [('response', C.c_void_p), ('code', C.c_int)]
    callback_type = C.CFUNCTYPE(C.c_int, C.c_int, C.POINTER(C.POINTER(Message)), C.POINTER(C.POINTER(Response)), C.c_void_p)
    messages = []
    prompted = False

    @callback_type
    def conversation(count, prompts, responses, _):
        nonlocal prompted
        if count < 1 or count > 32:
            return 19  # PAM_CONV_ERR: fail closed
        memory = libc.calloc(count, C.sizeof(Response))
        if not memory:
            return 5
        result = C.cast(memory, C.POINTER(Response))
        try:
            for index in range(count):
                prompt = prompts[index].contents
                if prompt.style == 1:  # PAM_PROMPT_ECHO_OFF
                    if prompted:
                        raise ValueError('Additional authentication prompt required.')
                    prompted = True
                    result[index].response = libc.strdup(password.encode())
                elif prompt.style == 2:  # PAM_PROMPT_ECHO_ON (username, never password)
                    result[index].response = libc.strdup(username.encode())
                elif prompt.style in (3, 4):
                    messages.append((prompt.message or b'').decode(errors='replace'))
                else:
                    raise ValueError('Unsupported PAM conversation.')
            responses[0] = result
            return 0  # Ownership transferred to PAM.
        except Exception:
            for index in range(count):
                if result[index].response:
                    libc.free(result[index].response)
            libc.free(memory)
            return 19

    class Conversation(C.Structure):
        _fields_ = [('function', callback_type), ('data', C.c_void_p)]
    conv = Conversation(conversation, None)
    handle = C.c_void_p()
    pam.pam_start.argtypes = [C.c_char_p, C.c_char_p, C.POINTER(Conversation), C.POINTER(C.c_void_p)]
    pam.pam_authenticate.argtypes = [C.c_void_p, C.c_int]
    pam.pam_end.argtypes = [C.c_void_p, C.c_int]
    if confdir is None:
        status = pam.pam_start(service.encode(), username.encode(), C.byref(conv), C.byref(handle))
    else:  # Isolated permit/deny policies used by the non-interactive tests only.
        pam.pam_start_confdir.argtypes = [C.c_char_p, C.c_char_p, C.POINTER(Conversation), C.c_char_p, C.POINTER(C.c_void_p)]
        status = pam.pam_start_confdir(service.encode(), username.encode(), C.byref(conv), str(confdir).encode(), C.byref(handle))
    try:
        if status == 0:
            status = pam.pam_authenticate(handle, 0)
        return {'success': status == 0, 'status': status,
                'kind': 'success' if status == 0 else 'rejected' if status in (7, 9, 10, 11) else 'service-error',
                'message': '\n'.join(messages)[-1500:]}
    finally:
        if handle:
            pam.pam_end(handle, status)


def main():
    try:
        request = json.loads(sys.stdin.buffer.readline(65536))
        password = request.get('password')
        if not isinstance(password, str) or '\0' in password:
            raise ValueError('Invalid authentication request.')
        result = authenticate(password)
        password = None
        request.clear()
    except Exception:
        result = {'success': False, 'kind': 'service-error', 'message': '', 'status': -1}
    print(json.dumps(result), flush=True)
    return 0 if result['success'] else 1


if __name__ == '__main__':
    sys.exit(main())
