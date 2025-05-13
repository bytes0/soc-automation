import os
import csv
import time
from typing import Dict
from executor.BaseTest import BaseTest


class LOLBASTest(BaseTest):
    TEST_NAME = "lolbas"
    CATEGORY = "privilege-escalation"

    def run(self, config: Dict) -> Dict:
        # Print current working directory for console debugging
        cwd = os.getcwd()
        print(f"DEBUG: Current Working Directory: {cwd}")
        log_msgs = [f"CWD: {cwd}"]

        # Merge config and defaults
        cfg = {**self.load_config(), **config}
        csv_path = cfg.get(
            "lolbas_csv_path",
            os.path.join("tests", "privilege-escalation", "utilities", "lolbas.csv")
        )
        delay = float(cfg.get("delay", 1))

        # Validate CSV path existence
        if not os.path.exists(csv_path):
            msg = f"LOLBAS CSV not found at {csv_path}"
            print(f"ERROR: {msg}")
            log_msgs.append(msg)
            result = {
                "status": "error",
                "output": "\n".join(log_msgs),
                "comment": msg,
                "executed_command": "N/A",
                "dest_ip": None,
                "dest_port": None,
                "Proxy": cfg.get("proxy")
            }
            self.log_result(result)
            return result

        # Read LOLBAS CSV entries
        entries = []
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("Filename")
                raw_paths = row.get("Paths", "")
                paths = [
                    p.strip().format(SystemRoot=os.environ.get("SystemRoot", "C:\\Windows"))
                    for p in raw_paths.split(",") if p.strip()
                ]
                if name and paths:
                    entries.append((name, paths))

        found_count = 0
        total = len(entries)

        # Existence check only
        for name, paths in entries:
            found = False
            for p in paths:
                @self.log_command(name=f"Check existence: {name} at {p}")
                def check():
                    exists = os.path.exists(p)
                    return {
                        'stdout': f"{name} exists at {p}" if exists else "",
                        'stderr': '' if exists else f"{name} not found at {p}",
                        'return_code': 0 if exists else 1
                    }

                res = check()
                msg = res.get('stdout') or res.get('stderr')
                print(f"DEBUG: {msg}")
                log_msgs.append(msg)
                time.sleep(delay)
                if res['return_code'] == 0:
                    found = True
                    break

            if found:
                found_count += 1
            else:
                msg = f"{name}: no valid path found"
                print(f"DEBUG: {msg}")
                log_msgs.append(msg)

        # Final summary
        summary = f"Found {found_count}/{total} LOLBAS binaries"
        print(f"DEBUG: {summary}")
        log_msgs.append(summary)

        result = {
            'status': 'success' if found_count > 0 else 'failure',
            'output': "\n".join(log_msgs),
            'comment': summary,
            'executed_command': "; ".join([f"Checked {name}" for name, _ in entries]),
            'dest_ip': None,
            'dest_port': None,
            'Proxy': cfg.get('proxy')
        }
        self.log_result(result)
        return result
