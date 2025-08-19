#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner for MCPlease MCP Server

This script runs all tests across different categories and provides
detailed reporting, coverage analysis, and performance metrics.
"""

import asyncio
import json
import subprocess
import sys
import time
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import statistics

# Test categories and their descriptions
TEST_CATEGORIES = {
    "unit": {
        "description": "Unit tests for individual components",
        "pattern": "tests/test_*.py",
        "exclude": ["test_integration", "test_performance", "test_e2e"]
    },
    "integration": {
        "description": "Integration tests for component interaction",
        "pattern": "tests/test_*integration*.py",
        "exclude": []
    },
    "security": {
        "description": "Security and authentication tests",
        "pattern": "tests/test_*security*.py",
        "exclude": []
    },
    "performance": {
        "description": "Performance and load testing",
        "pattern": "tests/test_*performance*.py",
        "exclude": []
    },
    "deployment": {
        "description": "Deployment and container tests",
        "pattern": "tests/test_*deployment*.py",
        "exclude": []
    },
    "ide": {
        "description": "IDE integration and compatibility tests",
        "pattern": "tests/test_*ide*.py",
        "exclude": []
    },
    "e2e": {
        "description": "End-to-end workflow tests",
        "pattern": "tests/test_*e2e*.py",
        "exclude": []
    }
}


@dataclass
class TestResult:
    """Individual test result."""
    name: str
    category: str
    status: str  # "passed", "failed", "skipped", "error"
    duration: float
    output: str
    error: Optional[str] = None
    coverage: Optional[float] = None


@dataclass
class CategoryResult:
    """Test category results."""
    category: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    total_duration: float
    coverage: Optional[float] = None
    tests: List[TestResult] = None


@dataclass
class TestSuiteReport:
    """Complete test suite report."""
    timestamp: str
    total_tests: int
    total_passed: int
    total_failed: int
    total_skipped: int
    total_errors: int
    total_duration: float
    overall_coverage: float
    categories: Dict[str, CategoryResult]
    summary: str
    recommendations: List[str]


class ComprehensiveTestRunner:
    """Comprehensive test suite runner."""
    
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.project_root = Path(__file__).parent.parent
        self.results: Dict[str, CategoryResult] = {}
        self.start_time = time.time()
        
    async def run_all_tests(self) -> TestSuiteReport:
        """Run all test categories."""
        print("🚀 Starting Comprehensive Test Suite")
        print("=" * 50)
        
        # Run each test category
        for category, config in TEST_CATEGORIES.items():
            if self.args.categories and category not in self.args.categories:
                continue
                
            print(f"\n📋 Running {category.upper()} tests...")
            print(f"   {config['description']}")
            
            result = await self.run_category_tests(category, config)
            self.results[category] = result
            
            # Print category summary
            self.print_category_summary(result)
        
        # Generate comprehensive report
        report = self.generate_report()
        
        # Print final summary
        self.print_final_summary(report)
        
        # Save report if requested
        if self.args.output:
            self.save_report(report, self.args.output)
        
        return report
    
    async def run_category_tests(self, category: str, config: Dict[str, Any]) -> CategoryResult:
        """Run tests for a specific category."""
        start_time = time.time()
        
        # Find test files
        test_files = self.find_test_files(category, config)
        
        if not test_files:
            return CategoryResult(
                category=category,
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=0,
                total_duration=0,
                tests=[]
            )
        
        # Run tests
        test_results = []
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        total_errors = 0
        
        for test_file in test_files:
            result = await self.run_test_file(test_file, category)
            test_results.append(result)
            
            if result.status == "passed":
                total_passed += 1
            elif result.status == "failed":
                total_failed += 1
            elif result.status == "skipped":
                total_skipped += 1
            else:
                total_errors += 1
        
        duration = time.time() - start_time
        
        # Calculate coverage if available
        coverage = self.calculate_category_coverage(test_results)
        
        return CategoryResult(
            category=category,
            total_tests=len(test_results),
            passed=total_passed,
            failed=total_failed,
            skipped=total_skipped,
            errors=total_errors,
            total_duration=duration,
            coverage=coverage,
            tests=test_results
        )
    
    def find_test_files(self, category: str, config: Dict[str, Any]) -> List[Path]:
        """Find test files for a category."""
        pattern = config["pattern"]
        exclude_patterns = config["exclude"]
        
        test_files = []
        tests_dir = self.project_root / "tests"
        
        if not tests_dir.exists():
            return []
        
        for test_file in tests_dir.glob(pattern):
            # Check if file should be excluded
            should_exclude = any(exclude in test_file.name for exclude in exclude_patterns)
            if not should_exclude:
                test_files.append(test_file)
        
        return test_files
    
    async def run_test_file(self, test_file: Path, category: str) -> TestResult:
        """Run a single test file."""
        start_time = time.time()
        
        try:
            # Run pytest on the test file
            cmd = [
                sys.executable, "-m", "pytest",
                str(test_file),
                "-v",
                "--tb=short"
            ]
            
            if self.args.coverage:
                cmd.extend(["--cov", "--cov-report=term-missing"])
            
            if self.args.verbose:
                cmd.append("-s")
            
            # Run the test
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            duration = time.time() - start_time
            
            # Determine test status
            if process.returncode == 0:
                status = "passed"
                error = None
            elif process.returncode == 1:
                status = "failed"
                error = stderr.decode() if stderr else "Test execution failed"
            elif process.returncode == 2:
                status = "error"
                error = stderr.decode() if stderr else "Test execution error"
            else:
                status = "error"
                error = f"Unknown return code: {process.returncode}"
            
            # Extract coverage if available
            coverage = None
            if self.args.coverage and "TOTAL" in stdout.decode():
                coverage = self.extract_coverage(stdout.decode())
            
            return TestResult(
                name=test_file.name,
                category=category,
                status=status,
                duration=duration,
                output=stdout.decode(),
                error=error,
                coverage=coverage
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name=test_file.name,
                category=category,
                status="error",
                duration=duration,
                output="",
                error=str(e)
            )
    
    def extract_coverage(self, output: str) -> Optional[float]:
        """Extract coverage percentage from pytest output."""
        try:
            for line in output.split('\n'):
                if 'TOTAL' in line and '%' in line:
                    # Extract percentage
                    parts = line.split()
                    for part in parts:
                        if '%' in part:
                            return float(part.replace('%', ''))
        except:
            pass
        return None
    
    def calculate_category_coverage(self, test_results: List[TestResult]) -> Optional[float]:
        """Calculate average coverage for a category."""
        coverages = [r.coverage for r in test_results if r.coverage is not None]
        if coverages:
            return statistics.mean(coverages)
        return None
    
    def generate_report(self) -> TestSuiteReport:
        """Generate comprehensive test report."""
        total_tests = sum(r.total_tests for r in self.results.values())
        total_passed = sum(r.passed for r in self.results.values())
        total_failed = sum(r.failed for r in self.results.values())
        total_skipped = sum(r.skipped for r in self.results.values())
        total_errors = sum(r.errors for r in self.results.values())
        total_duration = time.time() - self.start_time
        
        # Calculate overall coverage
        coverages = [r.coverage for r in self.results.values() if r.coverage is not None]
        overall_coverage = statistics.mean(coverages) if coverages else 0.0
        
        # Generate summary
        if total_failed == 0 and total_errors == 0:
            summary = "✅ All tests passed successfully!"
        elif total_failed > 0:
            summary = f"⚠️ {total_failed} tests failed, {total_passed} passed"
        else:
            summary = f"❌ {total_errors} test errors occurred"
        
        # Generate recommendations
        recommendations = self.generate_recommendations()
        
        return TestSuiteReport(
            timestamp=datetime.now().isoformat(),
            total_tests=total_tests,
            total_passed=total_passed,
            total_failed=total_failed,
            total_skipped=total_skipped,
            total_errors=total_errors,
            total_duration=total_duration,
            overall_coverage=overall_coverage,
            categories=self.results,
            summary=summary,
            recommendations=recommendations
        )
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Coverage recommendations
        if self.results:
            avg_coverage = statistics.mean([r.coverage for r in self.results.values() if r.coverage is not None])
            if avg_coverage < 80:
                recommendations.append("Consider improving test coverage (currently below 80%)")
            elif avg_coverage < 90:
                recommendations.append("Good test coverage, consider aiming for 90%+")
        
        # Failed test recommendations
        total_failed = sum(r.failed for r in self.results.values())
        if total_failed > 0:
            recommendations.append(f"Fix {total_failed} failing tests before deployment")
        
        # Performance recommendations
        if "performance" in self.results:
            perf_result = self.results["performance"]
            if perf_result.failed > 0:
                recommendations.append("Performance tests are failing - review performance bottlenecks")
        
        # Security recommendations
        if "security" in self.results:
            sec_result = self.results["security"]
            if sec_result.failed > 0:
                recommendations.append("Security tests are failing - critical security review needed")
        
        # General recommendations
        if not recommendations:
            recommendations.append("All tests passing - ready for deployment")
        
        return recommendations
    
    def print_category_summary(self, result: CategoryResult):
        """Print summary for a test category."""
        status_emoji = "✅" if result.failed == 0 and result.errors == 0 else "❌"
        
        print(f"   {status_emoji} {result.category.upper()}: {result.passed}/{result.total_tests} passed")
        print(f"      Duration: {result.total_duration:.2f}s")
        
        if result.coverage is not None:
            print(f"      Coverage: {result.coverage:.1f}%")
        
        if result.failed > 0:
            print(f"      ❌ {result.failed} failed")
        if result.errors > 0:
            print(f"      ⚠️ {result.errors} errors")
        if result.skipped > 0:
            print(f"      ⏭️ {result.skipped} skipped")
    
    def print_final_summary(self, report: TestSuiteReport):
        """Print final test summary."""
        print("\n" + "=" * 50)
        print("📊 COMPREHENSIVE TEST SUITE RESULTS")
        print("=" * 50)
        
        print(f"⏱️  Total Duration: {report.total_duration:.2f}s")
        print(f"🧪 Total Tests: {report.total_tests}")
        print(f"✅ Passed: {report.total_passed}")
        print(f"❌ Failed: {report.total_failed}")
        print(f"⚠️  Errors: {report.total_errors}")
        print(f"⏭️  Skipped: {report.total_skipped}")
        print(f"📈 Overall Coverage: {report.overall_coverage:.1f}%")
        
        print(f"\n📝 Summary: {report.summary}")
        
        if report.recommendations:
            print("\n💡 Recommendations:")
            for rec in report.recommendations:
                print(f"   • {rec}")
    
    def save_report(self, report: TestSuiteReport, output_path: str):
        """Save test report to file."""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(asdict(report), f, indent=2)
            
            print(f"\n💾 Report saved to: {output_file.absolute()}")
        except Exception as e:
            print(f"⚠️  Failed to save report: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Test Suite Runner for MCPlease MCP Server"
    )
    
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=list(TEST_CATEGORIES.keys()),
        help="Specific test categories to run"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Enable coverage reporting"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--output",
        help="Output file for JSON report"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel (experimental)"
    )
    
    args = parser.parse_args()
    
    # Create and run test runner
    runner = ComprehensiveTestRunner(args)
    
    try:
        asyncio.run(runner.run_all_tests())
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
