import os
import subprocess
import requests
from typing import Dict
from executor.BaseTest import BaseTest


class MultiDownloadTest(BaseTest):
    TEST_NAME = "exe_drop"
    CATEGORY = "exfiltration"

    def run(self, config: Dict) -> Dict:
        cfg = {**self.load_config(), **config}
        url = cfg.get("url", "https://github.com/notepad-plus-plus/notepad-plus-plus/releases/download/v8.5.6/npp.8.5.6.Installer.x64.exe")
        outdir = cfg.get("save_path", r"C:\Temp")
        outname = cfg.get("output_name", "testfile.exe")
        full_path = os.path.join(outdir, outname)

        os.makedirs(outdir, exist_ok=True)
        status = "failure"
        comment = ""

        # Method 1: Python requests
        @self.log_command(name="Download with requests")
        def method_requests():
            try:
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                with open(full_path, "wb") as f:
                    f.write(resp.content)
                return {"stdout": f"Saved to {full_path}", "stderr": "", "return_code": 0}
            except Exception as e:
                return {"stdout": "", "stderr": str(e), "return_code": 1}
        res1 = method_requests()

        # Method 2: PowerShell Invoke-WebRequest
        @self.log_command(name="Download with PowerShell")
        def method_powershell():
            ps = f"$url='{url}'; $out='{full_path}'; Invoke-WebRequest -Uri $url -OutFile $out"
            return self.execute_command(["powershell.exe", "-Command", ps])
        res2 = method_powershell()

        # Method 3: certutil
        @self.log_command(name="Download with certutil")
        def method_certutil():
            cmd = f"certutil.exe -urlcache -split -f {url} \"{full_path}\""
            return self.execute_command(cmd)
        res3 = method_certutil()

        # Method 4: bitsadmin
        @self.log_command(name="Download with bitsadmin")
        def method_bitsadmin():
            cmd = f"bitsadmin /transfer myjob /download /priority normal {url} \"{full_path}\""
            return self.execute_command(cmd)
        res4 = method_bitsadmin()

        # Check if any succeeded
        if any(r["return_code"] == 0 for r in [res1, res2, res3, res4]):
            status = "success"
        else:
            comment = "All methods failed"

        return {
            "status": status,
            "executed_command": f"Download {outname}",
            "comment": comment,
            "output": f"Saved to: {full_path if status == 'success' else 'N/A'}",
            "dest_ip": None,
            "dest_port": None,
            "Proxy": cfg.get("proxy")
        }
