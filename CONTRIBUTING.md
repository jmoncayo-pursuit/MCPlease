# Contributing to MCPlease

Thank you for your interest in contributing to MCPlease! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### 1. **Fork the Repository**
- Fork the MCPlease repository to your GitHub account
- Clone your fork locally: `git clone https://github.com/your-username/MCPlease.git`

### 2. **Create a Feature Branch**
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 3. **Make Your Changes**
- Write clean, well-documented code
- Follow the existing code style and conventions
- Add tests for new functionality
- Update documentation as needed

### 4. **Test Your Changes**
```bash
# Run the test suite
make test-installer
python scripts/test_transports.py
python -m pytest tests/ -v

# Test specific functionality
python scripts/test_mcp_setup.py
```

### 5. **Commit Your Changes**
Use conventional commit format:
```bash
git commit -m "feat: add new transport protocol"
git commit -m "fix: resolve memory leak in AI model"
git commit -m "docs: update installation guide"
```

### 6. **Push and Create Pull Request**
```bash
git push origin feature/your-feature-name
```
Then create a Pull Request on GitHub.

## 📋 Development Guidelines

### **Code Style**
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to all public functions
- Keep functions focused and single-purpose

### **Testing**
- Write unit tests for new functionality
- Ensure all tests pass before submitting
- Add integration tests for complex features
- Test across different platforms when possible

### **Documentation**
- Update README.md for user-facing changes
- Add inline comments for complex logic
- Update API documentation if applicable
- Include examples for new features

## 🏗️ Project Structure

```
mcplease/
├── src/                    # Source code
├── scripts/               # Utility and test scripts
├── tests/                 # Test suite
├── docs/                  # Documentation
├── examples/              # Example usage
└── docker/                # Docker configurations
```

## 🧪 Testing

### **Running Tests**
```bash
# Quick tests
make test-installer
make test-installer-dry-run

# Transport tests
python scripts/test_transports.py

# Full test suite
python -m pytest tests/ -v
```

### **Test Coverage**
- Aim for >80% test coverage
- Test edge cases and error conditions
- Include integration tests for critical paths

## 🐛 Bug Reports

When reporting bugs, please include:
- **Description** of the issue
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, etc.)
- **Error messages or logs**

## 💡 Feature Requests

For feature requests:
- **Describe the feature** and its benefits
- **Explain use cases** where it would be helpful
- **Consider implementation** complexity
- **Check if similar features** already exist

## 📝 Pull Request Guidelines

### **Before Submitting**
- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] No unnecessary files included

### **PR Description**
- **Summary** of changes
- **Motivation** for the change
- **Testing** performed
- **Breaking changes** (if any)

## 🚀 Release Process

### **Versioning**
We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### **Release Checklist**
- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in relevant files
- [ ] Release notes prepared

## 🆘 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check the docs/ directory
- **Code Examples**: See the examples/ directory

## 📄 License

By contributing to MCPlease, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to MCPlease! 🚀
