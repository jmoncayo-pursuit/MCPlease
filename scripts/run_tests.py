#!/usr/bin/env python3
"""
MCPlease MCP Server - Comprehensive Test Suite Runner

This script runs the complete test suite with coverage reporting,
performance testing, and CI/CD integration.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, List, Optional


class TestRunner:
    """Comprehensive test runner for MCPlease MCP Server."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_results = {}
        self.coverage_data = {}
        self.performance_data = {}
        self.logger = logging.getLogger(__name__)
        
    def run_unit_tests(self, verbose: bool = False, coverage: bool = True) -> Dict[str, Any]:
        """Run unit tests with optional coverage."""
        print("🧪 Running unit tests...")
        
        cmd = ["python", "-m", "pytest", "tests/", "-v" if verbose else "-q"]
        
        if coverage:
            cmd.extend([
                "--cov=src",
                "--cov-report=html:htmlcov",
                "--cov-report=json:coverage.json",
                "--cov-report=term-missing"
            ])
        
        # Add markers for unit tests
        cmd.extend(["-m", "unit or not integration"])
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            success = result.returncode == 0
            
            # Parse coverage data if available
            coverage_file = self.project_root / "coverage.json"
            coverage_data = {}
            if coverage and coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
            
            return {
                "success": success,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "coverage": coverage_data.get("totals", {}) if coverage_data else {}
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "Test execution timed out",
                "coverage": {}
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "coverage": {}
            }
    
    def run_integration_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run integration tests."""
        print("🔗 Running integration tests...")
        
        cmd = [
            "python", "-m", "pytest", "tests/",
            "-v" if verbose else "-q",
            "-m", "integration",
            "--tb=short"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for integration tests
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "Integration test execution timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def run_performance_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run performance and load tests."""
        print("⚡ Running performance tests...")
        
        cmd = [
            "python", "-m", "pytest", "tests/",
            "-v" if verbose else "-q",
            "-m", "performance or slow",
            "--tb=short",
            "--benchmark-only" if self._has_pytest_benchmark() else "--durations=10"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=900  # 15 minute timeout for performance tests
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "Performance test execution timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def run_security_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run security-focused tests."""
        print("🔒 Running security tests...")
        
        cmd = [
            "python", "-m", "pytest", "tests/",
            "-v" if verbose else "-q",
            "-k", "security or auth",
            "--tb=short"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def run_linting(self) -> Dict[str, Any]:
        """Run code linting and style checks."""
        print("🎨 Running code linting...")
        
        results = {}
        
        # Black formatting check
        try:
            result = subprocess.run(
                ["python", "-m", "black", "--check", "--diff", "src/", "tests/"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            results["black"] = {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr
            }
        except Exception as e:
            results["black"] = {"success": False, "output": str(e)}
        
        # isort import sorting check
        try:
            result = subprocess.run(
                ["python", "-m", "isort", "--check-only", "--diff", "src/", "tests/"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            results["isort"] = {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr
            }
        except Exception as e:
            results["isort"] = {"success": False, "output": str(e)}
        
        # Flake8 linting
        try:
            result = subprocess.run(
                ["python", "-m", "flake8", "src/", "tests/"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            results["flake8"] = {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr
            }
        except Exception as e:
            results["flake8"] = {"success": False, "output": str(e)}
        
        # MyPy type checking
        try:
            result = subprocess.run(
                ["python", "-m", "mypy", "src/"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            results["mypy"] = {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr
            }
        except Exception as e:
            results["mypy"] = {"success": False, "output": str(e)}
        
        overall_success = all(result["success"] for result in results.values())
        
        return {
            "success": overall_success,
            "results": results
        }
    
    def run_docker_tests(self) -> Dict[str, Any]:
        """Run Docker container tests."""
        print("🐳 Running Docker tests...")
        
        results = {}
        
        # Test x86 build
        try:
            result = subprocess.run(
                ["docker", "build", "-t", "mcplease-test:x86", "."],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600
            )
            results["x86_build"] = {
                "success": result.returncode == 0,
                "output": result.stderr  # Docker outputs to stderr
            }
        except subprocess.TimeoutExpired:
            results["x86_build"] = {"success": False, "output": "Docker build timed out"}
        except Exception as e:
            results["x86_build"] = {"success": False, "output": str(e)}
        
        # Test ARM64 build if Dockerfile.arm64 exists
        arm64_dockerfile = self.project_root / "Dockerfile.arm64"
        if arm64_dockerfile.exists():
            try:
                result = subprocess.run(
                    ["docker", "build", "-f", "Dockerfile.arm64", "-t", "mcplease-test:arm64", "."],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                results["arm64_build"] = {
                    "success": result.returncode == 0,
                    "output": result.stderr
                }
            except subprocess.TimeoutExpired:
                results["arm64_build"] = {"success": False, "output": "Docker build timed out"}
            except Exception as e:
                results["arm64_build"] = {"success": False, "output": str(e)}
        
        # Test container run
        if results.get("x86_build", {}).get("success", False):
            try:
                result = subprocess.run(
                    ["docker", "run", "--rm", "mcplease-test:x86", "--help"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                results["container_run"] = {
                    "success": result.returncode == 0,
                    "output": result.stdout + result.stderr
                }
            except Exception as e:
                results["container_run"] = {"success": False, "output": str(e)}
        
        overall_success = all(result["success"] for result in results.values())
        
        return {
            "success": overall_success,
            "results": results
        }
    
    def generate_test_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive test report."""
        report_lines = [
            "# MCPlease MCP Server - Test Report",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            ""
        ]
        
        # Overall summary
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.get("success", False))
        
        report_lines.extend([
            f"- **Total Test Suites**: {total_tests}",
            f"- **Passed**: {passed_tests}",
            f"- **Failed**: {total_tests - passed_tests}",
            f"- **Success Rate**: {(passed_tests/total_tests)*100:.1f}%",
            ""
        ])
        
        # Detailed results
        for test_name, result in results.items():
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            report_lines.extend([
                f"## {test_name.replace('_', ' ').title()}",
                f"**Status**: {status}",
                ""
            ])
            
            if "coverage" in result and result["coverage"]:
                coverage = result["coverage"]
                report_lines.extend([
                    "**Coverage**:",
                    f"- Lines: {coverage.get('percent_covered', 0):.1f}%",
                    f"- Missing: {coverage.get('missing_lines', 0)} lines",
                    ""
                ])
            
            if not result.get("success", False) and result.get("stderr"):
                report_lines.extend([
                    "**Error Output**:",
                    "```",
                    result["stderr"][:1000] + ("..." if len(result["stderr"]) > 1000 else ""),
                    "```",
                    ""
                ])
        
        return "\n".join(report_lines)
    
    def _has_pytest_benchmark(self) -> bool:
        """Check if pytest-benchmark is available."""
        try:
            import pytest_benchmark  # noqa: F401
            return True
        except ImportError:
            return False
    
    def run_all_tests(
        self,
        include_integration: bool = True,
        include_performance: bool = True,
        include_docker: bool = False,
        verbose: bool = False,
        coverage: bool = True
    ) -> Dict[str, Any]:
        """Run all test suites."""
        print("🚀 Running comprehensive test suite...")
        start_time = time.time()
        
        results = {}
        
        # Unit tests (always run)
        results["unit_tests"] = self.run_unit_tests(verbose=verbose, coverage=coverage)
        
        # Linting (always run)
        results["linting"] = self.run_linting()
        
        # Security tests (always run)
        results["security_tests"] = self.run_security_tests(verbose=verbose)
        
        # Integration tests (optional)
        if include_integration:
            results["integration_tests"] = self.run_integration_tests(verbose=verbose)
        
        # Performance tests (optional)
        if include_performance:
            results["performance_tests"] = self.run_performance_tests(verbose=verbose)
        
        # Docker tests (optional)
        if include_docker:
            results["docker_tests"] = self.run_docker_tests()
        
        total_time = time.time() - start_time
        
        # Generate report
        report = self.generate_test_report(results)
        
        # Save report
        report_file = self.project_root / "test_report.md"
        with open(report_file, "w") as f:
            f.write(report)
        
        print(f"\n📊 Test suite completed in {total_time:.1f}s")
        print(f"📄 Report saved to: {report_file}")
        
        return {
            "results": results,
            "total_time": total_time,
            "report": report,
            "report_file": str(report_file)
        }


def main():
    """Main test runner entry point."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="MCPlease MCP Server Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--security", action="store_true", help="Run security tests only")
    parser.add_argument("--docker", action="store_true", help="Run Docker tests only")
    parser.add_argument("--lint", action="store_true", help="Run linting only")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage reporting")
    parser.add_argument("--no-integration", action="store_true", help="Skip integration tests")
    parser.add_argument("--no-performance", action="store_true", help="Skip performance tests")
    parser.add_argument("--include-docker", action="store_true", help="Include Docker tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--ci", action="store_true", help="CI mode (exit with error code on failure)")
    
    args = parser.parse_args()
    
    # Determine project root
    project_root = Path(__file__).parent.parent
    
    # Create test runner
    runner = TestRunner(project_root)
    
    # Determine what to run
    if args.unit:
        results = {"unit_tests": runner.run_unit_tests(verbose=args.verbose, coverage=not args.no_coverage)}
    elif args.integration:
        results = {"integration_tests": runner.run_integration_tests(verbose=args.verbose)}
    elif args.performance:
        results = {"performance_tests": runner.run_performance_tests(verbose=args.verbose)}
    elif args.security:
        results = {"security_tests": runner.run_security_tests(verbose=args.verbose)}
    elif args.docker:
        results = {"docker_tests": runner.run_docker_tests()}
    elif args.lint:
        results = {"linting": runner.run_linting()}
    else:
        # Run all tests (default)
        test_results = runner.run_all_tests(
            include_integration=not args.no_integration,
            include_performance=not args.no_performance,
            include_docker=args.include_docker,
            verbose=args.verbose,
            coverage=not args.no_coverage
        )
        results = test_results["results"]
    
    # Print summary
    total_suites = len(results)
    passed_suites = sum(1 for r in results.values() if r.get("success", False))
    
    print(f"\n📊 Test Summary:")
    print(f"   Total Suites: {total_suites}")
    print(f"   Passed: {passed_suites}")
    print(f"   Failed: {total_suites - passed_suites}")
    
    # Exit with appropriate code
    if args.ci and passed_suites < total_suites:
        print("\n❌ Some tests failed in CI mode")
        sys.exit(1)
    elif passed_suites == total_suites:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed")
        sys.exit(0)  # Don't fail by default unless in CI mode


if __name__ == "__main__":
    main()