from datetime import datetime
import os
import time
import csv
import logging
import functools
import subprocess
import platform
import socket
import json
from abc import ABC, abstractmethod
from typing import Dict, Callable, Any, Optional
from pythonjsonlogger import jsonlogger


class BaseTest(ABC):
    TEST_NAME = "BaseTest"
    CATEGORY = "general"

    def __init__(self, console_output: bool = False, live_cb=None):
        self._live_cb = live_cb
        csv_path = os.environ.get(
            'SESSION_CSV',
            os.path.join(os.getcwd(), f'live_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        )
        self.test_start_time = time.time()
        first_time = not os.path.exists(csv_path)
        self.csv_fp = open(csv_path, 'a', newline='')
        self.csv_writer = csv.writer(self.csv_fp)
        if first_time:
            self.csv_writer.writerow([
                'Start', 'End', 'Test_case_name', 'executed_command', 'source_ip', 'source_hostname',
                'dest_ip', 'dest_hostname', 'dest_port', 'Proxy', 'Result', 'comment'
            ])
            self.csv_fp.flush()

        self.logger = self._setup_json_logger(console_output)
        self.base_fields = {
            'source_ip': self.get_source_ip(),
            'source_hostname': self.get_source_hostname(),
            'dest_ip': None,
            'dest_hostname': None,
            'dest_port': None,
            'Proxy': None
        }

    @abstractmethod
    def run(self, config: Dict) -> Dict:
        pass

    def execute_command(self, command: str, extra_fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        start = datetime.utcnow().isoformat()
        t0 = time.time()
        try:
            args = command if isinstance(command, list) else command.split()
            proc = subprocess.run(args, capture_output=True, text=True, check=False)
            duration = round(time.time() - t0, 2)
            end = datetime.utcnow().isoformat()
            return {
                'stdout': proc.stdout.strip(),
                'stderr': proc.stderr.strip(),
                'return_code': proc.returncode,
                'duration': duration,
                'start': start,
                'end': end,
                **(extra_fields or {})
            }
        except Exception as e:
            duration = round(time.time() - t0, 2)
            end = datetime.utcnow().isoformat()
            return {
                'stdout': '',
                'stderr': str(e),
                'return_code': -1,
                'duration': duration,
                'start': start,
                'end': end,
                **(extra_fields or {})
            }

    def log_command(self, func: Optional[Callable] = None, *, name: str = "Unnamed Command"):
        if func is None:
            return functools.partial(self.log_command, name=name)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            if self._live_cb:
                stamp = result.get('end', datetime.utcnow().isoformat())
                msg = f"[{stamp}] {self.TEST_NAME}/{name} → rc={result.get('return_code')} | {result.get('stderr') or result.get('stdout')}"
                self._live_cb(msg)

            log_entry = {
                'type': 'command', 'timestamp': result.get('end'),
                'test_name': self.TEST_NAME, 'category': self.CATEGORY,
                'command_name': name, 'executed_command': result.get('executed_command', func.__name__),
                'stdout': result.get('stdout'), 'stderr': result.get('stderr'),
                'return_code': result.get('return_code'), 'duration': result.get('duration')
            }
            self.logger.info(json.dumps(log_entry))

            row = [
                result.get('start'), result.get('end'), self.TEST_NAME,
                name, result.get('source_ip', self.base_fields['source_ip']),
                result.get('source_hostname', self.base_fields['source_hostname']),
                result.get('dest_ip', self.base_fields['dest_ip']),
                result.get('dest_hostname', self.base_fields['dest_hostname']),
                result.get('dest_port', self.base_fields['dest_port']),
                result.get('Proxy', self.base_fields['Proxy']),
                'success' if result.get('return_code') == 0 else 'failure',
                result.get('stderr') or result.get('stdout')
            ]
            self.csv_writer.writerow(row)
            self.csv_fp.flush()
            return result

        return wrapper

    def log_result(self, result: Dict):
        end = datetime.utcnow().isoformat()
        full = {
            'Start': datetime.fromtimestamp(self.test_start_time).isoformat(),
            'End': end,
            'Test_case_name': self.TEST_NAME,
            'executed_command': result.get('executed_command', ''),
            'source_ip': result.get('source_ip', self.base_fields['source_ip']),
            'source_hostname': result.get('source_hostname', self.base_fields['source_hostname']),
            'dest_ip': result.get('dest_ip', self.base_fields['dest_ip']),
            'dest_hostname': result.get('dest_hostname', self.base_fields['dest_hostname']),
            'dest_port': result.get('dest_port', self.base_fields['dest_port']),
            'Proxy': result.get('Proxy', self.base_fields['Proxy']),
            'Result': result.get('status'),
            'comment': result.get('comment')
        }
        self.logger.info(json.dumps(full))
        self.csv_writer.writerow(list(full.values()))
        self.csv_fp.flush()

    def _setup_json_logger(self, console_output: bool) -> logging.Logger:
        logger = logging.getLogger(self.TEST_NAME)
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            handler = logging.FileHandler('test_logs.json')
            handler.setFormatter(jsonlogger.JsonFormatter())
            logger.addHandler(handler)
            if console_output:
                ch = logging.StreamHandler()
                ch.setFormatter(logging.Formatter('%(message)s'))
                logger.addHandler(ch)
        return logger

    def get_source_hostname(self) -> str:
        return os.getenv('COMPUTERNAME') or platform.node() or 'unknown'

    def get_source_ip(self) -> str:
        try:
            return socket.gethostbyname(socket.gethostname())
        except:
            return 'unknown'

    def load_config(self) -> Dict:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'configs', f'{self.CATEGORY}.json'
        )
        try:
            with open(config_path) as f:
                return json.load(f).get(self.TEST_NAME, {})
        except:
            return {}

    def _fail_test(self, message: str) -> Dict:
        return {
            "status": "error",
            "executed_command": self.TEST_NAME,
            "comment": message,
            "dest_ip": self.base_fields['dest_ip'],
            "dest_port": self.base_fields['dest_port'],
            "Proxy": self.base_fields['Proxy']
        }

