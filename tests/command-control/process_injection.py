import subprocess
import base64
from datetime import datetime
from typing import Dict
from executor.BaseTest import BaseTest


class ProcessInjectionTest(BaseTest):
    TEST_NAME = "process_injection"
    CATEGORY  = "command-control"

    def run(self, _config: Dict) -> Dict:
        """
        Reads a local raw shellcode file, base64-encodes it,
        then invokes a configurable ProcessInjection.exe with the specified technique/method.
        """
        # 1) load our simple per-test config section
        cfg = self.load_config()
        payload_path  = cfg["payload"]
        injector_path = cfg.get("injector_path", "ProcessInjection.exe")
        technique     = cfg.get("technique", 2)
        method        = cfg.get("method", "p")

        # 2) generate base64 shellcode
        @self.log_command(name="Generate Base64 Shellcode")
        def gen_shellcode():
            start = datetime.utcnow().isoformat()
            with open(payload_path, "rb") as f:
                raw = f.read()
            encoded = base64.b64encode(raw).decode("utf-8")
            end = datetime.utcnow().isoformat()
            return {
                "command":     f"read+base64 {payload_path}",
                "stdout":      encoded,
                "stderr":      "",
                "return_code": 0,
                "start":       start,
                "end":         end,
                "duration":    0
            }

        gen_res = gen_shellcode()
        encoded = gen_res["stdout"]

        # 3) build and execute the injector
        cmd = [
            injector_path,
            "/t", str(technique),
            "/m", method,
            "/f", "base64",
            "/s", encoded
        ]

        @self.log_command(name="Run ProcessInjection")
        def run_injection():
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

        inj_res = run_injection()

        # 4) decide pass/fail
        status  = "success" if inj_res["return_code"] == 0 else "failure"
        comment = inj_res["stderr"] or inj_res["stdout"] or ""

        return {
            "status":           status,
            "executed_command": inj_res["command"],
            "comment":          comment
        }
