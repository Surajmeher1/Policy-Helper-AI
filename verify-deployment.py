#!/usr/bin/env python3

"""
AWS EC2 Deployment Verification Script
Checks system health and application status
"""

import subprocess
import sys
import os
from datetime import datetime

# Color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
NC = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*50}{NC}")
    print(f"{BLUE}{text}{NC}")
    print(f"{BLUE}{'='*50}{NC}")

def print_success(text):
    print(f"{GREEN}✓ {text}{NC}")

def print_warning(text):
    print(f"{YELLOW}⚠ {text}{NC}")

def print_error(text):
    print(f"{RED}✗ {text}{NC}")

def run_command(cmd, description=""):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "Command timeout"
    except Exception as e:
        return False, str(e)

def check_service_status(service_name):
    """Check if a systemd service is running"""
    success, _ = run_command(f"systemctl is-active --quiet {service_name}")
    return success

def check_port_listening(port):
    """Check if a port is listening"""
    success, output = run_command(f"sudo netstat -tlpn 2>/dev/null | grep :{port} || echo ''")
    return port in output if output else False

def check_disk_space():
    """Check available disk space"""
    success, output = run_command("df -h / | tail -1")
    if success:
        parts = output.split()
        if len(parts) >= 5:
            return output
    return "Unable to check"

def check_disk_usage():
    """Check disk usage percentage"""
    success, output = run_command("df -h / | tail -1 | awk '{print $5}'")
    if success:
        return output
    return "Unable to check"

def check_memory():
    """Check available RAM"""
    success, output = run_command("free -h | grep Mem | awk '{print $2}'")
    if success:
        return output
    return "Unable to check"

def check_memory_usage():
    """Check memory usage percentage"""
    success, output = run_command("free | grep Mem | awk '{printf(\"%.1f%\", $3/$2 * 100)}'")
    if success:
        return output
    return "Unable to check"

def check_python_packages():
    """Check if required Python packages are installed"""
    packages = ['flask', 'torch', 'transformers', 'gunicorn']
    missing = []
    
    for package in packages:
        success, _ = run_command(
            f"source /var/www/policy-helper-ai/venv/bin/activate && "
            f"python3 -c \"import {package.replace('-', '_')}\" 2>/dev/null"
        )
        if not success:
            missing.append(package)
    
    return missing

def check_app_files():
    """Check if required app files exist"""
    app_dir = "/var/www/policy-helper-ai"
    required_files = [
        f"{app_dir}/app.py",
        f"{app_dir}/requirements.txt",
        f"{app_dir}/templates",
        f"{app_dir}/instance",
    ]
    
    missing = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing.append(file_path)
    
    return missing

def check_nginx_config():
    """Verify Nginx configuration"""
    success, output = run_command("sudo nginx -t 2>&1")
    return success, output

def main():
    print(f"\n{BLUE}Policy Helper AI - Deployment Verification{NC}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # System Status
    print_header("System Status")
    
    total_ram = check_memory()
    ram_usage = check_memory_usage()
    print_success(f"Total RAM: {total_ram}")
    print_success(f"RAM Usage: {ram_usage}")
    
    disk_space = check_disk_space()
    disk_usage = check_disk_usage()
    print_success(f"Disk Space: {disk_space}")
    print_success(f"Disk Usage: {disk_usage}")
    
    # Service Status
    print_header("Service Status")
    
    services = ['policy-helper-ai', 'nginx']
    for service in services:
        if check_service_status(service):
            print_success(f"{service} is running")
        else:
            print_error(f"{service} is NOT running")
    
    # Port Status
    print_header("Network Status")
    
    if check_port_listening(80):
        print_success("Port 80 (HTTP) is listening")
    else:
        print_error("Port 80 (HTTP) is NOT listening")
    
    if check_port_listening(443):
        print_success("Port 443 (HTTPS) is listening")
    else:
        print_warning("Port 443 (HTTPS) is NOT listening (normal if SSL not set up)")
    
    # Application Files
    print_header("Application Files")
    
    missing_files = check_app_files()
    if not missing_files:
        print_success("All required application files found")
    else:
        print_error("Missing files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
    
    # Python Dependencies
    print_header("Python Dependencies")
    
    missing_packages = check_python_packages()
    if not missing_packages:
        print_success("All required Python packages installed")
    else:
        print_error("Missing packages:")
        for package in missing_packages:
            print(f"  - {package}")
    
    # Nginx Configuration
    print_header("Nginx Configuration")
    
    success, output = check_nginx_config()
    if success:
        print_success("Nginx configuration is valid")
    else:
        print_error("Nginx configuration has errors:")
        print(output)
    
    # Gunicorn Socket
    print_header("Gunicorn Socket")
    
    if os.path.exists('/run/policy-helper-ai.sock'):
        print_success("Gunicorn socket exists")
    else:
        print_error("Gunicorn socket not found (Gunicorn may not be running)")
    
    # Summary
    print_header("Summary")
    
    if not missing_files and not missing_packages:
        print_success("All checks passed!")
        print("\nApplication is ready for use.")
        return 0
    else:
        print_warning("Some checks failed. Review errors above.")
        print("\nTo troubleshoot:")
        print("  sudo journalctl -u policy-helper-ai -f")
        print("  sudo tail -f /var/log/nginx/error.log")
        return 1

if __name__ == '__main__':
    sys.exit(main())
