
import win32api
import win32security
import win32con
from datetime import datetime
from typing import Dict
from executor.BaseTest import BaseTest


class SeImpersonatePrivilegeTest(BaseTest):
    TEST_NAME = "se_impersonate_privilege"
    CATEGORY  = "privilege-escalation"

    def run(self, _config: Dict) -> Dict:
        """
        Checks whether the current process token has SeImpersonatePrivilege enabled.
        """
        # The literal privilege name
        PRIV_NAME = "SeImpersonatePrivilege"

        @self.log_command(name="Lookup LUID for SeImpersonatePrivilege")
        def lookup_luid():
            start = datetime.utcnow().isoformat()
            luid = win32security.LookupPrivilegeValue(None, PRIV_NAME)
            end = datetime.utcnow().isoformat()
            return {
                "stdout":      str(luid),
                "stderr":      "",
                "return_code": 0,
                "start":       start,
                "end":         end,
                "duration":    0
            }
        luid_res = lookup_luid()
        se_luid = int(luid_res["stdout"])

        @self.log_command(name="Check SeImpersonatePrivilege")
        def check_priv():
            start = datetime.utcnow().isoformat()
            token = win32security.OpenProcessToken(
                win32api.GetCurrentProcess(),
                win32con.TOKEN_QUERY
            )
            privs = win32security.GetTokenInformation(token, win32security.TokenPrivileges)
            has_it = any(luid == se_luid for luid, _ in privs)
            stdout = "enabled" if has_it else "not enabled"
            end = datetime.utcnow().isoformat()
            return {
                "stdout":      stdout,
                "stderr":      "",
                "return_code": 0 if has_it else 1,
                "start":       start,
                "end":         end,
                "duration":    0
            }
        check_res = check_priv()

        status  = "success" if check_res["return_code"] == 0 else "failure"
        comment = (
            "SeImpersonatePrivilege is enabled"
            if status == "success"
            else "SeImpersonatePrivilege is not enabled"
        )

        return {
            "status": status,
            "executed_command": "OpenProcessToken→GetTokenInformation",
            "comment": comment
        }
