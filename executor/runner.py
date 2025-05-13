import subprocess
import os
import yaml
import logging
from datetime import datetime
from executor.logger import log_test_execution  # Assuming you have a logger module to log to a file

# Setup logging to a log file
log_file = "test_execution.log"
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')

def run_test_case(test_path):
    with open(test_path, 'r') as file:
        test_data = yaml.safe_load(file)

    # Extract necessary info from the YAML file
    os_type = test_data.get("os_type", "unix")
    wsl = test_data.get("wsl", False)
    log_commands = test_data.get("log_commands", False)
    test_case = test_data.get("test_case", {})

    # Network-related info (optional)
    source_ip = test_data.get("source_ip", "N/A")
    source_hostname = test_data.get("source_hostname", "N/A")
    dest_ip = test_data.get("dest_ip", "N/A")
    dest_hostname = test_data.get("dest_hostname", "N/A")
    dest_port = test_data.get("dest_port", "N/A")
    proxy = test_data.get("proxy", "N/A")

    test_name = test_case.get("name", "Unknown Test")
    test_description = test_case.get("description", "")
    commands = test_case.get("commands", [])

    logging.info(f"Running test: {test_name} - {test_description}")

    # Log the test case start info
    log_test_execution(test_name, "running", "N/A", source_ip, source_hostname, dest_ip, dest_hostname, dest_port,
                       proxy)

    result_output = []  # Store all command outputs here

    for command_data in commands:
        command = command_data["command"]
        command_name = command_data.get("name", "Unnamed Command")

        if log_commands:
            logging.info(f"Executing command: {command_name} - {command}")
            result_output.append(f"Executing command: {command_name} - {command}")

        try:
            # Determine if we are running Unix or Windows commands
            if os_type == "unix":
                if wsl:
                    result = subprocess.run(["wsl", "bash", "-c", command], capture_output=True, text=True)
                else:
                    result = subprocess.run(command, capture_output=True, text=True, shell=True)
            elif os_type == "windows":
                result = subprocess.run(command, capture_output=True, text=True, shell=True)

            command_result = f"Command '{command_name}' executed with return code {result.returncode}:\n"
            command_result += f"stdout: {result.stdout}\nstderr: {result.stderr}"
            result_output.append(command_result)

            if result.returncode == 0:
                logging.info(f"Command '{command_name}' executed successfully.")
            else:
                logging.error(f"Command '{command_name}' failed: {result.stderr}")
        except Exception as e:
            logging.error(f"Error executing command '{command_name}': {str(e)}")
            result_output.append(f"Error executing command '{command_name}': {str(e)}")

    # Log the test completion info
    log_test_execution(test_name, "completed", "N/A", source_ip, source_hostname, dest_ip, dest_hostname, dest_port,
                       proxy)

    return "\n".join(result_output)  # Return all collected command outputs as the result
def run_yaml_test(test_path):
    """
    Executes a YAML-based test case and logs the result.

    :param test_path: Path to the YAML test case.
    :return: Outcome of the test execution.
    """
    # Read YAML content
    with open(test_path, 'r') as file:
        test_data = yaml.safe_load(file)

    test_case_name = test_data.get('test_case_name', 'Unknown Test')
    commands = test_data.get('commands', [])
    log_commands = test_data.get('log_commands', False)
    result = "Success"  # Default result, adjust based on test execution

    # List to hold command outputs for logging
    command_outputs = []

    # Debug print to see what commands are being executed
    print(f"Test Case: {test_case_name}")
    print(f"Commands: {commands}")

    # Execute the test commands
    for command_data in commands:
        command = command_data.get('command', '')
        use_wsl = command_data.get('wsl', False)  # Check if the 'wsl' flag is True

        if log_commands:
            command_outputs.append(command)  # Track the commands for logging

        try:
            # Determine if we need to run the command via WSL or not
            if use_wsl:
                print(f"Running command in WSL: {command}")
                wsl_command = f"wsl {command}"
                result_output = subprocess.run(wsl_command, check=True, shell=True, text=True, capture_output=True)
            else:
                print(f"Running command in default environment: {command}")
                result_output = subprocess.run(command, check=True, shell=True, text=True, capture_output=True)

            # Capture the output
            command_result = result_output.stdout + result_output.stderr
            print(f"Command output: {command_result}")  # Debug print for command output
            command_outputs.append(command_result)  # Log output for this command

        except subprocess.CalledProcessError as e:
            result = "Failure"
            command_outputs.append(f"Error: {str(e)}")
            break

    # Log all command outputs and final results
    log_test_execution(test_case_name, result, command_outputs)

    # Return a string summarizing the test result
    return f"Test {test_case_name} completed with result: {result}\nOutputs:\n" + "\n".join(command_outputs)

def log_test_execution(test_case_name, result, command_outputs, source_ip="N/A", source_hostname="N/A",
                       dest_ip="N/A", dest_hostname="N/A", dest_port="N/A", proxy="N/A", comment=""):
    # Capture start and end time automatically
    start_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    duration = "N/A"  # Placeholder for duration logic, could be computed

    # Log the test execution details
    logging.info(f"Start: {start_date}, End: {end_date}, Test_case_name: {test_case_name}, "
                 f"Executed_command: {command_outputs}, Source_ip: {source_ip}, Source_hostname: {source_hostname}, "
                 f"Dest_ip: {dest_ip}, Dest_hostname: {dest_hostname}, Dest_port: {dest_port}, "
                 f"Proxy: {proxy}, Result: {result}, Comment: {comment}")
