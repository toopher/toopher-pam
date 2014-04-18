import unittest
import StringIO

from mock import patch, sentinel, MagicMock
import toopher

import pam_toopher
import common


class ToopherPamAuthenticateTests(unittest.TestCase):
    def setUp(self):
        pamh = MagicMock()
        pamh.PAM_IGNORE = sentinel.PAM_IGNORE
        pamh.PAM_AUTH_ERR = sentinel.PAM_AUTH_ERR
        pamh.get_user.return_value = sentinel.PAM_USER

        self.pamh = pamh
        self.flags = None
        self.argv = []

        get_system_config_patcher = patch("pam_toopher.get_system_config")
        self.addCleanup(get_system_config_patcher.stop)

        self.get_system_config_mock = get_system_config_patcher.start()
        self.get_system_config_mock.return_value = common.get_system_config(StringIO.StringIO())

        get_api_object_patcher = patch("pam_toopher.get_api_object")
        self.addCleanup(get_api_object_patcher.stop)

        self.get_api_object_mock = get_api_object_patcher.start()
        self.get_api_object_mock.return_value = MagicMock(spec=toopher.ToopherApi)

        system_config_options = self.get_system_config_mock.return_value[common.SYSTEM_CONFIG_OPTIONS_SECTION]

        self.group_available = MagicMock()
        self.group_available.gr_name = system_config_options[common.SYSTEM_CONFIG_OPTIONS_KEY_AVAILABLE_GROUP]
        self.group_available.gr_mem = []

        self.group_required = MagicMock()
        self.group_required.gr_name = system_config_options[common.SYSTEM_CONFIG_OPTIONS_KEY_REQUIRED_GROUP]
        self.group_required.gr_mem = []

        grp_patcher = patch("pam_toopher.grp")
        self.addCleanup(grp_patcher.stop)

        grp_mock = grp_patcher.start()
        grp_mock.getgrall.return_value = [self.group_available,
                                          self.group_required]

    def set_availability_to_groups(self):
        self.get_system_config_mock.return_value[common.SYSTEM_CONFIG_OPTIONS_SECTION][common.SYSTEM_CONFIG_OPTIONS_KEY_AVAILABILITY] = "groups"

    def add_user_to_group_available(self):
        self.group_available.gr_mem.append(self.pamh.get_user.return_value)

    def add_user_to_group_required(self):
        self.group_required.gr_mem.append(self.pamh.get_user.return_value)

    def test_available_but_unpaired_returns_ignore(self):
        ret_val = pam_toopher.pam_sm_authenticate(self.pamh, self.flags, self.argv)
        self.assertEqual(ret_val, sentinel.PAM_IGNORE)

    def test_group_availability_for_unpaired_user(self):
        self.set_availability_to_groups()
        self.add_user_to_group_available()

        ret_val = pam_toopher.pam_sm_authenticate(self.pamh, self.flags, self.argv)

        self.assertEqual(ret_val, sentinel.PAM_IGNORE)

    def test_group_required_for_unpaired_user(self):
        self.set_availability_to_groups()
        self.add_user_to_group_required()

        ret_val = pam_toopher.pam_sm_authenticate(self.pamh, self.flags, self.argv)

        self.assertEqual(ret_val, sentinel.PAM_AUTH_ERR)


if __name__ == '__main__':
    unittest.main()
