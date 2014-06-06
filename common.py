import os
import sys
import inspect
import StringIO
import getpass
import socket
import subprocess
import pickle

import configobj
import toopher
import validate

from config import *

TIMEOUT = 60

# Setup paths (autoconf helps populate these)
DEFAULT_FILENAME_SYSTEM_API_CREDENTIALS = os.path.join(SYSTEM_TOOPHER_CONFIG_DIR, "credentials")
DEFAULT_FILENAME_SYSTEM_CONFIG = os.path.join(SYSTEM_TOOPHER_CONFIG_DIR, "config")
DEFAULT_FILENAME_USER_CONFIG = ".toopher"

CREDENTIAL_SPEC = """\
key = string
secret = string
"""

SYSTEM_CONFIG_SPEC = """\
[API]
credential-file = string(default='%s')
base-url = string(default='https://api.toopher.com/v1/')

[Options]
failure-policy = option('allow', 'deny', default='allow')
availability = option('none', 'available', 'groups', 'required', default='available')
available-group = string(default='toopher-available')
required-group = string(default='toopher-required')
automation-allowed = boolean(default=false)
show-prompt = boolean(default=false)
""" % DEFAULT_FILENAME_SYSTEM_API_CREDENTIALS

USER_CONFIG_SPEC = """\
[Pairings]
shared-pairing-id = string(default=None)
__many__ = string
"""

HOSTNAME = socket.gethostname()


def get_config(filename, configspec=None, log=lambda message: None):
    if isinstance(configspec, basestring):
        configspec = StringIO.StringIO(configspec)

    try:
        config = configobj.ConfigObj(filename,
                                     configspec=configspec,
                                     file_error=True)
    except Exception, e:
        message = "Problem reading configuration file ('%s'): %s" % (filename, e)
        e.message = message
        log(message)
        raise

    # Validate if configspec provided
    if configspec:
        validation = config.validate(validate.Validator(), preserve_errors=True)

        if validation != True:
            messages = ["Problem validating configuration file ('%s')" % filename]

            for section_list, key, result in configobj.flatten_errors(config, validation):
                messages.append("The '%s' key in section '%s' failed to validate (%s)"
                                % (key,
                                   ','.join(section_list) if section_list else 'default',
                                   result if result else 'Missing'))

            map(log, messages)
            raise validate.ValidateError('\n'.join(messages))

    return config


def get_credentials_config(filename=DEFAULT_FILENAME_SYSTEM_API_CREDENTIALS, log=lambda message: None):
    credentials_config = get_config(filename, CREDENTIAL_SPEC, log)

    if not credentials_config[CREDENTIAL_KEY_KEY] or not credentials_config[CREDENTIAL_KEY_SECRET]:
        message = "Invalid key/secret in API credential file (%s)" % filename
        log(message)
        raise validate.ValidateError(message)

    return credentials_config

def get_system_config(filename=DEFAULT_FILENAME_SYSTEM_CONFIG, log=lambda message: None):
    system_config = get_config(filename, SYSTEM_CONFIG_SPEC, log)
    return system_config


def get_user_config_filename(username=None, filename=DEFAULT_FILENAME_USER_CONFIG):
    if not username:
        username = getpass.getuser()

    return os.path.join(os.path.expanduser("~%s" % username), filename)


def get_user_config(username=None, log=lambda message:None):
    user_config_filename = get_user_config_filename(username)
    user_config = get_config(user_config_filename, USER_CONFIG_SPEC, log)
    return user_config


def get_full_username(username=None, shared=False):
    if not username:
        username = getpass.getuser()

    if shared:
        return username
    else:
        return "%s@%s" % (username, HOSTNAME)


class ApiHelper(object):
    HELPER_BIN = "toopher-api-helper"

    def __init__(self, validate_config=True):
        if validate_config:
            self._validate_config()

    def __getattr__(self, item):
        raise toopher.ToopherApiError("Unsupported API method")

    def _invoke_helper(self, *pickle_args, **kwargs):
        args = [self.HELPER_BIN]
        invocation_args = kwargs.pop('invocation_args', None)
        if invocation_args:
            args.extend(invocation_args)

        helper =subprocess.Popen(args,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE)

        # Pickle args to stdin
        input_pickler = pickle.Pickler(helper.stdin)
        for pickle_arg in pickle_args:
            input_pickler.dump(pickle_arg)

        # Unpickle stdout
        result = pickle.load(helper.stdout)

        if isinstance(result, Exception):
            raise result
        else:
            return result

    def _validate_config(self):
        self._invoke_helper(invocation_args=["--validate-only"])

    def pair(self, *args, **kwargs):
        return self._invoke_helper("pair", args, kwargs)

    def get_pairing_status(self, *args, **kwargs):
        return self._invoke_helper("get_pairing_status", args, kwargs)

    def authenticate(self, *args, **kwargs):
        return self._invoke_helper("authenticate", args, kwargs)

    def get_authentication_status(self, *args, **kwargs):
        return self._invoke_helper("get_authentication_status", args, kwargs)


def get_api_object(system_config, log=lambda message: None):
    try:
        # Collect log messages (to be sent only if ApiHelper fallback fails)
        collected_log_messages = []
        def log_collector(message):
            collected_log_messages.append(message)

        credential_filename = system_config[SYSTEM_CONFIG_API_SECTION][SYSTEM_CONFIG_API_KEY_CREDENTIAL_FILE]
        credentials = get_credentials_config(credential_filename, log=log_collector)
        key = credentials[CREDENTIAL_KEY_KEY]
        secret = credentials[CREDENTIAL_KEY_SECRET]
        base_url = system_config[SYSTEM_CONFIG_API_SECTION][SYSTEM_CONFIG_API_KEY_BASE_URL]
        return toopher.ToopherApi(key, secret, base_url)
    except Exception:  # Could not create a real API object, try helper
        # Try helper utility to access credentials
        try:
            helper = ApiHelper()
            del collected_log_messages[:]  # drain collected log messages since helper was successful
            return helper
        except Exception, e:
            log_collector("Could not fallback to API helper: %s" % e)
            raise
    finally:
        for log_message in collected_log_messages:
            log(log_message)


# Stolen from python 2.7's inspect module source code
def getcallargs(func, *positional, **named):
    """Get the mapping of arguments to values.

    A dict is returned, with keys the function argument names (including the
    names of the * and ** arguments, if any), and values the respective bound
    values from 'positional' and 'named'."""
    args, varargs, varkw, defaults = inspect.getargspec(func)
    f_name = func.__name__
    arg2value = {}

    # The following closures are basically because of tuple parameter unpacking.
    assigned_tuple_params = []
    def assign(arg, value):
        if isinstance(arg, str):
            arg2value[arg] = value
        else:
            assigned_tuple_params.append(arg)
            value = iter(value)
            for i, subarg in enumerate(arg):
                try:
                    subvalue = next(value)
                except StopIteration:
                    raise ValueError('need more than %d %s to unpack' %
                                     (i, 'values' if i > 1 else 'value'))
                assign(subarg,subvalue)
            try:
                next(value)
            except StopIteration:
                pass
            else:
                raise ValueError('too many values to unpack')
    def is_assigned(arg):
        if isinstance(arg,str):
            return arg in arg2value
        return arg in assigned_tuple_params
    if inspect.ismethod(func) and func.im_self is not None:
        # implicit 'self' (or 'cls' for classmethods) argument
        positional = (func.im_self,) + positional
    num_pos = len(positional)
    num_total = num_pos + len(named)
    num_args = len(args)
    num_defaults = len(defaults) if defaults else 0
    for arg, value in zip(args, positional):
        assign(arg, value)
    if varargs:
        if num_pos > num_args:
            assign(varargs, positional[-(num_pos-num_args):])
        else:
            assign(varargs, ())
    elif 0 < num_args < num_pos:
        raise TypeError('%s() takes %s %d %s (%d given)' % (
            f_name, 'at most' if defaults else 'exactly', num_args,
            'arguments' if num_args > 1 else 'argument', num_total))
    elif num_args == 0 and num_total:
        if varkw:
            if num_pos:
                # XXX: We should use num_pos, but Python also uses num_total:
                raise TypeError('%s() takes exactly 0 arguments '
                                '(%d given)' % (f_name, num_total))
        else:
            raise TypeError('%s() takes no arguments (%d given)' %
                            (f_name, num_total))
    for arg in args:
        if isinstance(arg, str) and arg in named:
            if is_assigned(arg):
                raise TypeError("%s() got multiple values for keyword "
                                "argument '%s'" % (f_name, arg))
            else:
                assign(arg, named.pop(arg))
    if defaults:    # fill in any missing values with the defaults
        for arg, value in zip(args[-num_defaults:], defaults):
            if not is_assigned(arg):
                assign(arg, value)
    if varkw:
        assign(varkw, named)
    elif named:
        unexpected = next(iter(named))
        if isinstance(unexpected, unicode):
            unexpected = unexpected.encode(sys.getdefaultencoding(), 'replace')
        raise TypeError("%s() got an unexpected keyword argument '%s'" %
                        (f_name, unexpected))
    unassigned = num_args - len([arg for arg in args if is_assigned(arg)])
    if unassigned:
        num_required = num_args - num_defaults
        raise TypeError('%s() takes %s %d %s (%d given)' % (
            f_name, 'at least' if defaults else 'exactly', num_required,
            'arguments' if num_required > 1 else 'argument', num_total))
    return arg2value


if __name__ == '__main__':
    import collections
    import itertools

    AUTO_GENERATED_MARK = '# !!!! AUTOGENERATION MARK - DO NOT EDIT BELOW THIS LINE !!!\n'

    def make_valid_constant_name(name):
        return name.upper().replace('-','_')

    def extract_constants(section, prefix):
        constants = collections.OrderedDict()

        for scalar in section.scalars:
            if '__many__' in scalar:
                continue
            name = make_valid_constant_name("%s_%s_%s" % (prefix, "KEY", scalar))
            constants[name] = scalar

        for subsection in section.sections:
            name = make_valid_constant_name("%s_%s_%s" %(prefix, subsection, "SECTION"))
            constants[name] = subsection

            constants.update(extract_constants(section[subsection], "%s_%s" % (prefix, subsection)))

        return constants

    temp_file_name = __file__ + '~'
    with open(__file__, 'rb') as infile:
        with open(temp_file_name, 'wb') as outfile:
            for line in infile:
                if line == AUTO_GENERATED_MARK:
                    break

                outfile.write(line)

            outfile.write(AUTO_GENERATED_MARK)

            credential_constants = extract_constants(configobj.ConfigObj(CREDENTIAL_SPEC), "CREDENTIAL")
            system_config_constants = extract_constants(configobj.ConfigObj(SYSTEM_CONFIG_SPEC), "SYSTEM_CONFIG")
            user_config_constants = extract_constants(configobj.ConfigObj(USER_CONFIG_SPEC), "USER_CONFIG")

            for constant, value in itertools.chain(credential_constants.iteritems(),
                                                   system_config_constants.iteritems(),
                                                   user_config_constants.iteritems()):
                outfile.write("%s = '%s'\n" % (constant, value))

    os.rename(temp_file_name, __file__)

# The constants below are automatically generated by running this module (i.e., "python common.py")
# !!!! AUTOGENERATION MARK - DO NOT EDIT BELOW THIS LINE !!!
CREDENTIAL_KEY_KEY = 'key'
CREDENTIAL_KEY_SECRET = 'secret'
SYSTEM_CONFIG_API_SECTION = 'API'
SYSTEM_CONFIG_API_KEY_CREDENTIAL_FILE = 'credential-file'
SYSTEM_CONFIG_API_KEY_BASE_URL = 'base-url'
SYSTEM_CONFIG_OPTIONS_SECTION = 'Options'
SYSTEM_CONFIG_OPTIONS_KEY_FAILURE_POLICY = 'failure-policy'
SYSTEM_CONFIG_OPTIONS_KEY_AVAILABILITY = 'availability'
SYSTEM_CONFIG_OPTIONS_KEY_AVAILABLE_GROUP = 'available-group'
SYSTEM_CONFIG_OPTIONS_KEY_REQUIRED_GROUP = 'required-group'
SYSTEM_CONFIG_OPTIONS_KEY_AUTOMATION_ALLOWED = 'automation-allowed'
SYSTEM_CONFIG_OPTIONS_KEY_SHOW_PROMPT = 'show-prompt'
USER_CONFIG_PAIRINGS_SECTION = 'Pairings'
USER_CONFIG_PAIRINGS_KEY_SHARED_PAIRING_ID = 'shared-pairing-id'
