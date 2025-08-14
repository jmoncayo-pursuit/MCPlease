# MCPlease MVP - Offline AI Coding Assistant

🤖 **Powered by gpt-oss-20b** | 🔒 **100% Offline & Private** | 💻 **Optimized for Mac** | ⚡ **Zero-configuration setup**

MCPlease MVP is an offline AI coding assistant that runs entirely on your Mac. It provides intelligent code completion, explanations, and debugging help using a locally-hosted 21.5B parameter language model, ensuring your code never leaves your machine.

## ✨ Features

- **🔒 Complete Privacy**: All AI processing happens locally - your code never leaves your machine
- **⚡ Zero Setup**: One command installation with automatic configuration
- **🧠 Powerful AI**: Uses gpt-oss-20b (21.5B parameters) for high-quality code assistance
- **💻 Mac Optimized**: Intelligent memory management works great on 16GB+ Mac systems
- **🔌 VSCode Ready**: Seamless integration with Continue.dev extension
- **🚀 Fast Inference**: Optimized with vLLM and MXFP4 quantization

## 🚀 Quick Start

### One-Command Installation (Recommended)

```bash
curl -sSL https://raw.githubusercontent.com/your-org/mcplease-mvp/main/install.sh | bash
```

That's it! The installer will:
- ✅ Check system requirements
- ✅ Install dependencies
- ✅ Download the AI model
- ✅ Set up everything automatically

### Start Using MCPlease

After installation, restart your terminal and run:

```bash
mcplease --start
```

Or check system status:

```bash
mcplease --status
```

## 📋 System Requirements

- **macOS** (Apple Silicon or Intel)
- **16GB+ RAM** (12GB minimum, 32GB+ ideal)
- **Python 3.9-3.12**
- **50GB+ free disk space** (for model storage)
- **Internet connection** (for initial setup only)

## 🔌 VSCode Integration

1. **Install Continue.dev extension** in VSCode
2. **Configure the extension** to use MCPlease:
   - Open Continue.dev settings
   - Add MCPlease as a provider
   - Set endpoint to your local server
3. **Start coding** with AI assistance!

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
git clone https://github.com/your-org/mcplease-mvp.git
cd mcplease-mvp

# Run setup
python mcplease.py --setup

# Start server
python mcplease.py --start
```

## 📊 Performance

- **Response Time**: ~2-5 seconds for code completion
- **Memory Usage**: 8-12GB during inference
- **Model Size**: ~21GB on disk (compressed)
- **Context Length**: Up to 8192 tokens

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   VSCode IDE    │◄──►│  MCP Protocol    │◄──►│  AI Model       │
│  (Continue.dev) │    │     Server       │    │  (gpt-oss-20b)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                       ┌──────────────────┐
                       │ Memory Manager   │
                       │ & Optimization   │
                       └──────────────────┘
```

## 🔧 Advanced Usage

### Custom Memory Limits
```bash
mcplease --start --max-memory 8  # Use max 8GB RAM
```

### Debug Mode
```bash
mcplease --start --debug  # Enable detailed logging
```

### Custom Model Path
```bash
mcplease --start --model-path /path/to/model
```

## 🧪 Development

### Project Structure
```
mcplease-mvp/
├── src/
│   ├── models/        # AI model management
│   ├── mcp/           # MCP protocol implementation  
│   ├── environment/   # Environment setup
│   └── utils/         # Shared utilities
├── tests/             # Test suite
├── examples/          # Usage examples
└── mcplease.py        # Main entry point
```

### Running Tests
```bash
python -m pytest tests/ -v
```

### Memory Management Demo
```bash
python examples/memory_management_demo.py
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check our [docs](docs/) folder
- **Issues**: Report bugs on [GitHub Issues](https://github.com/your-org/mcplease-mvp/issues)
- **Discussions**: Join our [GitHub Discussions](https://github.com/your-org/mcplease-mvp/discussions)

## 🙏 Acknowledgments

- **OpenAI** for the gpt-oss-20b model
- **vLLM team** for the high-performance inference engine
- **Continue.dev** for the excellent VSCode integration
- **Hugging Face** for model hosting and distribution

---

**Made with ❤️ for developers who value privacy and performance**