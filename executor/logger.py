import logging
from datetime import datetime

# Configure the logger
logging.basicConfig(
    filename='test_execution.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)


def log_test_execution(test_case_name, result, command_outputs, source_ip="N/A", source_hostname="N/A",
                       dest_ip="N/A", dest_hostname="N/A", dest_port="N/A", proxy="N/A", comment=""):
    # Capture start and end time automatically
    start_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    duration = "N/A"  # Placeholder for duration logic, could be computed
    logging.info(f"Start: {start_date}, End: {end_date}, Test_case_name: {test_case_name}, "
                 f"Executed_command: {command_outputs}, Source_ip: {source_ip}, Source_hostname: {source_hostname}, "
                 f"Dest_ip: {dest_ip}, Dest_hostname: {dest_hostname}, Dest_port: {dest_port}, "
                 f"Proxy: {proxy}, Result: {result}, Comment: {comment}")