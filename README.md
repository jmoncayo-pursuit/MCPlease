# MCPlease - Offline AI Coding Assistant

🤖 **Powered by OSS-20B** | 🔒 **100% Offline & Private** | 💻 **VSCode Ready** | ⚡ **One-Command Setup**

MCPlease is an offline AI coding assistant that runs entirely on your machine. It provides intelligent code completion, explanations, and debugging help using a locally-hosted language model, ensuring your code never leaves your machine.

## 🎯 **The Promise: AI-Native Development, Offline**

**Before MCPlease**: Multiple setup steps, manual configuration, restarting processes
**With MCPlease**: Download model once, then run `./start.sh` for instant AI coding

Built for AI-native builders who want to keep building without cloud dependencies or credit systems.

## ✨ Features

- **🔒 Complete Privacy**: All AI processing happens locally - your code never leaves your machine
- **⚡ Simple Setup**: Download model once, then `./start.sh` for instant AI coding
- **🧠 Professional AI**: Full OSS-20B model for production-quality coding assistance
- **💻 Cross-Platform**: Works on macOS, Linux, and Windows
- **🔌 VSCode Ready**: Seamless integration with Continue.dev extension
- **🚀 AI-Native**: Built for developers who code with AI

## 🚀 Quick Start

### Download OSS-20B Model (Required)

```bash
python download_model.py
```

**This is required** - MCPlease needs the OSS-20B model to provide AI coding assistance.

### Start MCPlease

```bash
./start.sh
```

### Start Using MCPlease

1. **Download the model**: `python download_model.py` (required)
2. **Start the system**: `./start.sh`
3. **Wait for VSCode** to open
4. **Press `Ctrl+I`** in VSCode to open Continue.dev
5. **Start coding** with AI assistance!

**Note**: The fallback responses are just for testing - real AI coding assistance requires the full model.

## 📋 System Requirements

### Required
- **Python 3.9+**
- **VSCode** with Continue.dev extension
- **Any available port** (automatically finds one)
- **15GB+ free disk space** (for OSS-20B model)
- **Stable internet connection** (for model download)
- **Patience** (10-30 minutes download time)

### What You Get
- **Full OSS-20B model** for AI coding assistance
- **Offline AI coding** - no cloud dependencies
- **Professional-grade AI responses** for building
- **Continue.dev integration** in VSCode

## 🔌 VSCode Integration

**Automatic!** No manual configuration needed.

1. **Download the model**: `python download_model.py` (required first)
2. **Run `./start.sh`** - This configures everything automatically
3. **VSCode opens** with Continue.dev already configured
4. **Press `Ctrl+I`** to start using AI assistance
5. **Start coding** immediately!

The setup script handles all configuration automatically.

## 💡 Usage Examples

### Code Completion
```python
def fibonacci(n):
    # AI will complete this function
```

### Code Explanation
Select any code and ask: "What does this function do?"

### Debugging Help
Paste error messages and get intelligent debugging suggestions.

## 🛠️ Manual Installation

If you prefer manual setup:

```bash
# Clone repository
git clone https://github.com/your-org/mcplease.git
cd mcplease

# Start server manually
python mcplease_http_server.py

# Configure VSCode manually
# (See .vscode/settings.json for configuration)
```

## 📊 Performance

- **Response Time**: Instant with fallback responses
- **Memory Usage**: Minimal (fallback mode)
- **Setup Time**: ~10 seconds total
- **Context Length**: Unlimited (fallback mode)

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   VSCode IDE    │◄──►│  HTTP Server     │◄──►│  AI Responses   │
│  (Continue.dev) │    │  (Port 8000)     │    │  (Fallback)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                       ┌──────────────────┐
                       │  VSCode Config   │
                       │  (Auto-setup)    │
                       └──────────────────┘
```

## 🔧 Advanced Usage

### Model Management

#### Download OSS-20B Model (Required)
```bash
python download_model.py
```
- Downloads the full model (~13GB)
- Automatically checks disk space
- Resumes interrupted downloads
- **Required for AI coding assistance**

#### Check Model Status
```bash
ls -la models/gpt-oss-20b/
```
- Verify model files are present
- Check total size (~13GB)

#### Remove Model (Not Recommended)
```bash
rm -rf models/gpt-oss-20b/
```
- Frees up ~13GB of disk space
- **Breaks AI functionality** - only use if you know what you're doing

### Server Configuration

#### Custom Server Port
```bash
# The system automatically finds an available port
# If you need a specific port, set the PORT environment variable:
PORT=9000 ./start.sh
```

#### Manual Server Start
```bash
python mcplease_http_server.py
```

#### Custom VSCode Config
```bash
# Edit .vscode/settings.json for custom settings
```

## 🧪 Development

### Project Structure
```
mcplease/
├── start.sh                    # One-command setup script
├── mcplease_http_server.py     # HTTP server for Continue.dev
├── .vscode/settings.json       # VSCode configuration
├── tests/                      # Test suite
└── examples/                   # Usage examples
```

### Running Tests
```bash
python -m pytest tests/ -v
```

### Test Server
```bash
python test_server.py
```

## 🤝 Contributing

We welcome contributions! 

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

### Common Issues

#### Model Download Problems
- **Slow download**: Normal for 13GB file, be patient
- **Download interrupted**: Just run `python download_model.py` again - it will resume
- **Not enough disk space**: Free up at least 15GB before downloading
- **Network errors**: Check your internet connection and try again

#### Server Issues
- **Port conflicts**: Automatically resolved - the system finds an available port
- **Continue.dev not working**: Restart VSCode after running `./start.sh`

### Getting Help
- **Documentation**: Check our documentation files
- **Issues**: Report bugs on GitHub Issues
- **Questions**: Open a GitHub Discussion

## 🙏 Acknowledgments

- **Continue.dev** for the excellent VSCode integration
- **FastAPI** for the high-performance HTTP server
- **VSCode** for the extensible IDE platform

---
<div align="center">
**MCPlease** - Made with ❤️ for developers who want offline AI coding assistance
#ForTheLoveOfCode
</div>