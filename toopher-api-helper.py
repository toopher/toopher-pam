import sys
import signal
import pickle

import argparse

import toopher

from common import *


def sigint_handler(sig, frame):
    sys.exit("Cancelled by user (Ctrl-C)")

signal.signal(signal.SIGINT, sigint_handler)


def send_pickled_output(output):
    pickle.dump(output, sys.stdout)


def success(ret_val=None):
    send_pickled_output(ret_val)
    sys.exit()


def error(ret_val):
    if not isinstance(ret_val, toopher.ToopherApiError):
        ret_val = toopher.ToopherApiError(ret_val)

    pickle.dump(ret_val, sys.stdout)
    sys.exit(-1)


def main():
    argparser = argparse.ArgumentParser(description="Used to perform Toopher API calls which may require privileged access to API credentials. This tool is not typically required by end users.")
    argparser.add_argument("--validate-only", "-v", action="store_true",
                           help="Validate that the necessary configuration information can be loaded")

    invocation_args = argparser.parse_args()

    # Retrieve API credentials from system configuration file
    try:
        system_config = get_system_config()
        credentials_file = system_config[SYSTEM_CONFIG_API_SECTION][SYSTEM_CONFIG_API_KEY_CREDENTIAL_FILE]
        api_url = system_config[SYSTEM_CONFIG_API_SECTION][SYSTEM_CONFIG_API_KEY_BASE_URL]

        credentials_config = get_credentials_config(credentials_file)
        api_key = credentials_config[CREDENTIAL_KEY_KEY]
        api_secret = credentials_config[CREDENTIAL_KEY_SECRET]

        api = toopher.ToopherApi(api_key, api_secret, api_url)
    except Exception, e:
        error("Helper could not load API configuration: %s" % e)

    if invocation_args.validate_only:
        success() # Validation succeeded - we are done

    unpickler = pickle.Unpickler(sys.stdin)
    method_name = unpickler.load()
    args = unpickler.load()
    kwargs = unpickler.load()

    if method_name == 'pair':
        try:
            result = api.pair(*args, **kwargs)
        except Exception, e:
            error(e)
        else:
            success(result)
    elif method_name == 'get_pairing_status':
        try:
            result = api.get_pairing_status(*args, **kwargs)
        except Exception, e:
            error(e)
        else:
            success(result)
    elif method_name == 'authenticate':
        if os.geteuid() != 0:
            # Only allow authentication request for pairings owned by the user
            callargs = getcallargs(api.authenticate, *args, **kwargs)
            pairing_id = callargs['pairing_id']
            try:
                user_config = get_user_config()
                valid_pairings_ids = user_config[USER_CONFIG_PAIRINGS_SECTION].values()
                if pairing_id not in valid_pairings_ids:
                    error("Helper will only authenticate against pairings for this user")
            except Exception:
                error("Helper could not determine which pairings are owned by this user")

        try:
            result = api.authenticate(*args, **kwargs)
        except Exception, e:
            error(e)
        else:
            success(result)
    elif method_name == 'get_authentication_status':
        try:
            result = api.get_authentication_status(*args, **kwargs)
        except Exception, e:
            error(e)
        else:
            success(result)
    else:
        error("Helper does not support the '%s' method" % method_name)


if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        error("Helper encountered an unexpected error: %s" % e)