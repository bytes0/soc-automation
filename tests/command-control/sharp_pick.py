import subprocess
from datetime import datetime
from typing import Dict
from executor.BaseTest import BaseTest


class SharpPickTest(BaseTest):
    TEST_NAME = "sharp-pick"
    CATEGORY  = "command-control"

    def run(self, _config: Dict) -> Dict:
        """
        Invokes sharppick.exe with the configured flag and argument.
        """
        cfg          = self.load_config()
        exe_path     = cfg.get("executable", "sharppick.exe")
        flag         = cfg.get("flag")       # e.g. "-f", "-r", "-d", or "-a"
        argument     = cfg.get("argument")   # file path, resource name, URL, or delimiter

        cmd = [exe_path, flag, argument]

        @self.log_command(name="Run SharpPick")
        def invoke_sharppick():
            start = datetime.utcnow().isoformat()
            proc = subprocess.run(cmd, capture_output=True, text=True)
            end = datetime.utcnow().isoformat()
            return {
                "command":     " ".join(cmd),
                "stdout":      proc.stdout,
                "stderr":      proc.stderr,
                "return_code": proc.returncode,
                "start":       start,
                "end":         end,
                "duration":    0
            }

        result = invoke_sharppick()
        status = "success" if result["return_code"] == 0 else "failure"
        comment = result["stderr"] or result["stdout"] or ""

        return {
            "status":           status,
            "executed_command": result["command"],
            "comment":          comment
        }
