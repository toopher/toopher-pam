import configobj
import validate
import toopher
import syslog
import time
import grp

from common import *

try:
    SYSLOG_FACILITY = syslog.LOG_AUTHPRIV  # Specified in module writer's guide, but not available on all/most platforms
except Exception:
    SYSLOG_FACILITY = syslog.LOG_AUTH

ARG_CONFIG_FAIL_CLOSED = 'config_fail_closed'


def pam_sm_authenticate(pamh, flags, argv):
    config_fail_closed = ARG_CONFIG_FAIL_CLOSED in argv

    try:
        sys_config = get_system_config(filename=DEFAULT_FILENAME_SYSTEM_CONFIG,
                                       log=lambda msg: syslog.syslog(SYSLOG_FACILITY|syslog.LOG_ALERT, msg))
        api = get_api_object(sys_config)


    except Exception, e:
        if config_fail_closed:
            syslog.syslog(SYSLOG_FACILITY|syslog.LOG_ALERT,
                          "Denying request because module is configured to fail closed.")
            return pamh.PAM_AUTH_ERR
        else:
            syslog.syslog(SYSLOG_FACILITY|syslog.LOG_ALERT,
                          "Approving request because module is configured to fail open."
                          " Add '%s' as argument to toopher_pam module to deny requests when misconfigured."
                          % ARG_CONFIG_FAIL_CLOSED)
            return pamh.PAM_SUCCESS

    sys_config_options = sys_config[SYSTEM_CONFIG_OPTIONS_SECTION]
    availability = sys_config_options[SYSTEM_CONFIG_OPTIONS_KEY_AVAILABILITY]
    fail_closed = 'deny' == sys_config_options[SYSTEM_CONFIG_OPTIONS_KEY_FAILURE_POLICY]

    required_group = sys_config_options[SYSTEM_CONFIG_OPTIONS_KEY_REQUIRED_GROUP]
    available_group = sys_config_options[SYSTEM_CONFIG_OPTIONS_KEY_AVAILABLE_GROUP]

    username = pamh.get_user()
    users_groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
    user_in_required_group = required_group in users_groups
    user_in_available_group = available_group in users_groups

    required = (availability == 'required' or
                (availability == 'groups' and user_in_required_group))
    available = (required or
                 availability != 'none' or
                 availability == 'available' or
                 (availability == 'groups' and user_in_available_group))

    if not available:
        return pamh.PAM_IGNORE

    try:
        user_config = get_user_config(username)
        try:
            pairing_id = user_config[USER_CONFIG_PAIRINGS_SECTION][HOSTNAME]
        except KeyError:
            # No hostname pairing, try to find a shared key - if that doesn't exist fallback to outer exception handler
            pairing_id = user_config[USER_CONFIG_PAIRINGS_SECTION][USER_CONFIG_PAIRINGS_KEY_SHARED_PAIRING_ID]
            if not pairing_id:
                raise KeyError()
    except (IOError, KeyError):  # Does not exist or user has no pairing-id to use
        if required:
            syslog.syslog(SYSLOG_FACILITY|syslog.LOG_ALERT,
                          "Toopher is required, but no pairing information found for '%s' (run 'toopher-pair')."
                          % username)
            return pamh.PAM_AUTH_ERR
        else:
            return pamh.PAM_IGNORE
    except (configobj.ConfigObjError, validate.ValidateError), e:  # Could not parse
        syslog.syslog(SYSLOG_FACILITY|syslog.LOG_ALERT,
                      "Error reading user config file: %s." % e)
        if fail_closed:
            syslog.syslog(SYSLOG_FACILITY|syslog.LOG_ALERT,
                          "Denying request because module is configured to fail closed.")
            return pamh.PAM_AUTH_ERR
        else:
            syslog.syslog(SYSLOG_FACILITY|syslog.LOG_ALERT,
                          "Approving request because module is configured to fail open."
                          " Change failure policy in Toopher config to deny requests when misconfigured.")
            return pamh.PAM_SUCCESS

    automation_allowed = sys_config_options[SYSTEM_CONFIG_OPTIONS_KEY_AUTOMATION_ALLOWED]

    terminal_name = pamh.rhost
    action_name = pamh.service

    try:
        auth = api.authenticate(pairing_id=pairing_id,
                                terminal_name=terminal_name,
                                action_name=action_name,
                                automation_allowed=automation_allowed)

        start = time.time()
        while True:
            try:
                auth_status = api.get_authentication_status(auth.id)
            except Exception:
                pass  # Allow status errors to occur silently (up to the full timeout period)
            else:
                if not auth_status.pending:
                    message = "Toopher authentication request %s"
                    if auth_status.automated:
                        message += " automatically"

                    if auth_status.granted:
                        syslog.syslog(SYSLOG_FACILITY|syslog.LOG_INFO, message % "granted")
                        return pamh.PAM_SUCCESS
                    else:
                        syslog.syslog(SYSLOG_FACILITY|syslog.LOG_INFO, message % "denied")
                        return pamh.PAM_AUTH_ERR

            if time.time() - start > TIMEOUT:  # TODO: prefer to use a monotonic clock to avoid clock change errors
                syslog.syslog(SYSLOG_FACILITY|syslog.LOG_INFO, "Toopher authentication request timed out")
                return pamh.PAM_AUTH_ERR

            time.sleep(1)
    except Exception, e:
        syslog.syslog(SYSLOG_FACILITY|syslog.LOG_ERR, "Error performing Toopher authentication: %s" % e)
        if fail_closed:
            syslog.syslog(SYSLOG_FACILITY|syslog.LOG_ALERT,
                          "Denying request because module is configured to fail closed.")
            return pamh.PAM_AUTH_ERR
        else:
            syslog.syslog(SYSLOG_FACILITY|syslog.LOG_ALERT,
                          "Approving request because module is configured to fail open."
                          " Change failure policy in Toopher config to deny requests upon error conditions.")
            return pamh.PAM_SUCCESS


def pam_sm_setcred(pamh, flags, argv):
    return pamh.PAM_SUCCESS
