# Product Requirements Document: Offline-First AI Coding Assistant

## Mission Statement
Create a **100% offline AI coding assistant** that integrates with VSCode via Continue.dev, using your local OSS-20B model. No cloud dependencies, no credits, no internet required.

## What You Get
- **One-command setup** for offline AI coding assistance
- **VSCode integration** via Continue.dev extension
- **Local OSS-20B model** for AI responses
- **Code completion, explanation, debugging, refactoring**
- **Zero configuration** after initial setup

## Technical Approach
1. **HTTP Server Wrapper**: FastAPI server that mimics OpenAI API format
2. **Continue.dev Integration**: VSCode extension that connects to local server
3. **OSS-20B Model**: Local LLM for AI responses (currently using intelligent fallbacks)
4. **One-Command Installer**: `python mcplease_continue.py`

## Implementation Status
✅ **HTTP Server**: `mcplease_http_server.py` - Working on dynamic port allocation
✅ **Continue.dev Config**: Auto-created in `~/.continue/config.json`
✅ **One-Command Setup**: `mcplease_continue.py` - Fully functional
✅ **Basic AI Responses**: Intelligent fallback system working
🔄 **OSS-20B Integration**: Infrastructure ready, needs model connection

## Files Created
- `mcplease_continue.py` - Main setup script
- `mcplease_http_server.py` - HTTP server for Continue.dev
- `~/.continue/config.json` - Continue.dev configuration
- `test_server.py` - Testing script

## Next Steps
1. **Test in VSCode**: Restart VSCode, use Ctrl+I for Continue chat
2. **Add OSS-20B Model**: Connect real AI model to replace fallbacks
3. **Enhance Responses**: Improve AI quality and context awareness

## Success Criteria
- ✅ Continue.dev connects to local server
- ✅ AI responses work offline
- ✅ No cloud dependencies
- ✅ One-command setup
- 🔄 OSS-20B model integration (next phase)w
