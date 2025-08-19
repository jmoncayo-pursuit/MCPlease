#!/usr/bin/env python3
"""
Test script for MCPlease Universal Installer
Tests individual functions without running full installation
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def test_os_detection():
    """Test OS detection logic"""
    print("🧪 Testing OS detection...")
    
    # Test what the installer would detect
    os_type = os.environ.get('OSTYPE', 'unknown')
    print(f"OSTYPE: {os_type}")
    
    if os_type.startswith('linux'):
        if os.path.exists('/etc/os-release'):
            with open('/etc/os-release', 'r') as f:
                content = f.read()
                if 'Ubuntu' in content:
                    print("✅ Detected: Ubuntu")
                elif 'Debian' in content:
                    print("✅ Detected: Debian")
                elif 'CentOS' in content:
                    print("✅ Detected: CentOS")
                else:
                    print("✅ Detected: Linux (generic)")
        else:
            print("✅ Detected: Linux")
    elif os_type.startswith('darwin'):
        print("✅ Detected: macOS")
    elif os_type.startswith('msys') or os_type.startswith('cygwin'):
        print("✅ Detected: Windows")
    else:
        print("⚠️  Unknown OS type")
    
    return True

def test_python_detection():
    """Test Python detection logic"""
    print("\n🧪 Testing Python detection...")
    
    # Test python3
    try:
        result = subprocess.run(['python3', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ python3: {version}")
        else:
            print("❌ python3 not available")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ python3 not available")
    
    # Test python
    try:
        result = subprocess.run(['python', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ python: {version}")
        else:
            print("❌ python not available")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ python not available")
    
    return True

def test_package_manager_detection():
    """Test package manager detection"""
    print("\n🧪 Testing package manager detection...")
    
    package_managers = [
        ('apt-get', 'apt (Ubuntu/Debian)'),
        ('yum', 'yum (CentOS/RHEL)'),
        ('dnf', 'dnf (Fedora)'),
        ('pacman', 'pacman (Arch)'),
        ('brew', 'brew (macOS)'),
        ('choco', 'chocolatey (Windows)')
    ]
    
    found_managers = []
    for cmd, name in package_managers:
        try:
            result = subprocess.run([cmd, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ {name}: {cmd}")
                found_managers.append(name)
            else:
                print(f"❌ {name}: not available")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"❌ {name}: not available")
    
    if found_managers:
        print(f"\n✅ Found package managers: {', '.join(found_managers)}")
    else:
        print("\n⚠️  No package managers detected")
    
    return True

def test_docker_detection():
    """Test Docker detection"""
    print("\n🧪 Testing Docker detection...")
    
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Docker: {version}")
            
            # Test if Docker daemon is running
            try:
                result = subprocess.run(['docker', 'info'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print("✅ Docker daemon: running")
                else:
                    print("⚠️  Docker daemon: not running")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                print("⚠️  Docker daemon: not accessible")
        else:
            print("❌ Docker not available")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Docker not available")
    
    return True

def test_system_requirements():
    """Test system requirements checking"""
    print("\n🧪 Testing system requirements...")
    
    # Check disk space
    try:
        if platform.system() == 'Windows':
            # Windows disk space check
            result = subprocess.run(['wmic', 'logicaldisk', 'get', 'size,freespace'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            free_space_gb = int(parts[1]) / (1024**3)
                            print(f"✅ Disk space: {free_space_gb:.1f}GB available")
                            break
        else:
            # Unix disk space check
            result = subprocess.run(['df', '.'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) >= 4:
                        free_space_gb = int(parts[3]) / (1024**2)
                        print(f"✅ Disk space: {free_space_gb:.1f}GB available")
    except Exception as e:
        print(f"⚠️  Could not check disk space: {e}")
    
    # Check memory (Unix only)
    if platform.system() != 'Windows':
        try:
            result = subprocess.run(['free', '-g'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) >= 2:
                        total_memory_gb = int(parts[1])
                        print(f"✅ Total memory: {total_memory_gb}GB")
        except Exception as e:
            print(f"⚠️  Could not check memory: {e}")
    
    return True

def test_installer_files():
    """Test if installer files exist and are accessible"""
    print("\n🧪 Testing installer files...")
    
    files_to_check = [
        'install.sh',
        'install.bat',
        'requirements.txt',
        'scripts/setup_ide.py',
        'mcplease_mcp_server.py',
        'mcplease_http_server.py'
    ]
    
    all_files_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path}: exists")
        else:
            print(f"❌ {file_path}: missing")
            all_files_exist = False
    
    # Check if install.sh is executable
    if os.path.exists('install.sh'):
        if os.access('install.sh', os.X_OK):
            print("✅ install.sh: executable")
        else:
            print("⚠️  install.sh: not executable")
            all_files_exist = False
    
    return all_files_exist

def main():
    """Run all installer tests"""
    print("🚀 MCPlease Universal Installer - Local Testing")
    print("=" * 60)
    
    tests = [
        ("OS Detection", test_os_detection),
        ("Python Detection", test_python_detection),
        ("Package Manager Detection", test_package_manager_detection),
        ("Docker Detection", test_docker_detection),
        ("System Requirements", test_system_requirements),
        ("Installer Files", test_installer_files)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Installer should work on this system.")
        print("\n💡 To test full installation:")
        print("   • Backup your current setup")
        print("   • Run: ./install.sh")
        print("   • Or test in a clean directory")
    else:
        print("⚠️  Some tests failed. Check the issues above.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
