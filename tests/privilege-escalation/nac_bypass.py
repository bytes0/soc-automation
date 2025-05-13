import os
import re
import platform
import random
from typing import Dict
from executor.BaseTest import BaseTest


class MACSpoofTest(BaseTest):
    TEST_NAME = "mac_spoof"
    CATEGORY = "privilege-escalation"

    def run(self, config: Dict) -> Dict:
        interface = config.get("interface")
        new_mac = config.get("mac_address", self._generate_random_mac())

        if not interface:
            return self._finalize({
                "status": "error",
                "output": "Missing 'interface' in config"
            })

        try:
            if self.is_windows:
                result = self._spoof_windows(interface, new_mac)
            else:
                result = self._spoof_linux(interface, new_mac)
        except Exception as e:
            result = {
                "status": "error",
                "output": str(e)
            }

        self.log_result(result)
        return result

    def _spoof_linux(self, interface: str, new_mac: str) -> Dict:
        cmds = [
            ["ip", "link", "set", interface, "down"],
            ["ip", "link", "set", interface, "address", new_mac],
            ["ip", "link", "set", interface, "up"]
        ]
        for cmd in cmds:
            result = self.execute_command(cmd)
            if result["return_code"] != 0:
                return {
                    "status": "failed",
                    "output": result["stderr"] or "Error executing: " + " ".join(cmd)
                }

        return {
            "status": "success",
            "output": f"MAC address changed to {new_mac} on {interface}"
        }

    def _spoof_windows(self, interface: str, new_mac: str) -> Dict:
        reg_base = r"HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}"
        new_mac_nocolon = new_mac.replace(":", "")

        disable_cmd = f'netsh interface set interface "{interface}" admin=disable'
        result = self.execute_command(disable_cmd)
        if result["return_code"] != 0:
            return {"status": "failed", "output": result["stderr"]}

        query_cmd = f'reg query "{reg_base}" /s /f "{interface}"'
        result = self.execute_command(query_cmd)
        if result["return_code"] != 0:
            return {"status": "failed", "output": result["stderr"]}

        keys = re.findall(rf'{reg_base}\\\\\d+', result["stdout"])
        if not keys:
            return {"status": "failed", "output": "Registry key not found for interface"}

        for key in keys:
            reg_cmd = f'reg add "{key}" /v NetworkAddress /d {new_mac_nocolon} /f'
            result = self.execute_command(reg_cmd)
            if result["return_code"] != 0:
                return {"status": "failed", "output": result["stderr"]}

        enable_cmd = f'netsh interface set interface "{interface}" admin=enable'
        result = self.execute_command(enable_cmd)
        if result["return_code"] != 0:
            return {"status": "warning", "output": "MAC changed, but failed to re-enable interface"}

        return {
            "status": "success",
            "output": f"MAC address spoofed to {new_mac} for interface {interface}. Reboot may be needed."
        }

    def _generate_random_mac(self) -> str:
        return "02:" + ":".join(f"{random.randint(0, 255):02x}" for _ in range(5))

    def _finalize(self, result: Dict) -> Dict:
        self.log_result(result)
        return result
