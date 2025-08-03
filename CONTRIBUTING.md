# 🤝 Contributing to Aetherra

Welcome to the Aetherra project! We're excited that you want to contribute to the next-generation AI Operating System. This guide will help you get started with contributing to Aetherra.

## 🚀 Quick Start for Contributors

### 1. Fork and Clone the Repository

```bash
# Fork the repository on GitHub first, then clone your fork
git clone https://github.com/YOUR_USERNAME/Aetherra.git
cd Aetherra

# Add the upstream remote
git remote add upstream https://github.com/AetherraLabs/Aetherra.git
```

### 2. Set Up Your Development Environment

```bash
# Create a Python virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install pytest black isort mypy pre-commit
```

### 3. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example environment file
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Required for AI features
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Optional - for enhanced features
DISCORD_TOKEN=your_discord_token_here
TELEGRAM_BOT_TOKEN=your_telegram_token_here
```

### 4. Test Your Setup

**🎨 Testing the Unified GUI (Recommended)**

The Aetherra project now features a unified React + Flask GUI system. This is the easiest way to test your setup:

```bash
# Install Node.js/npm dependencies for React frontend
cd Aetherra/lyrixa_core/gui
npm install

# Return to project root and launch unified GUI
cd ../../../
python Aetherra/gui/launch_aetherra_gui.py
```

This will start:
- **React Frontend**: http://localhost:3000 (Modern cyberpunk interface)
- **Flask API Server**: http://localhost:8686 (Backend with Socket.IO)
- **Real-time Communication**: WebSocket connection between frontend and backend

**[TOOL] Testing Individual Components**

```bash
# Test core AI OS launcher
python aetherra_os_launcher.py --mode test

# Test API server only (Flask backend)
python Aetherra/gui/web_interface_server.py --debug

# Test React frontend only (requires separate API server)
cd Aetherra/lyrixa_core/gui && npm run dev

# Run tests (if available)
pytest
```

### 5. Fix Import Issues (If Any)

If you encounter import errors after cloning/forking, run our automated fix script:

```bash
# Fix common import issues automatically
python fix_imports.py
```

This will:
- [OK] Create missing `__init__.py` files
- [OK] Check Python version compatibility
- [OK] Install missing dependencies
- [OK] Test import patterns
- [OK] Generate a detailed report

For manual troubleshooting, see [IMPORT_FIXES.md](IMPORT_FIXES.md).

**Common import errors and quick fixes:**

```bash
# Error: ModuleNotFoundError: No module named 'aetherra_core'
# Fix: Missing __init__.py files (run fix_imports.py)

# Error: No module named 'flask' or 'aiohttp'
# Fix: Install dependencies
pip install -r requirements.txt

# Error: VS Code import warnings
# Fix: Select correct Python interpreter (Ctrl+Shift+P -> "Python: Select Interpreter")
```

## 🛠️ Development Workflow

### 1. Create a Feature Branch

```bash
# Always create a new branch for your changes
git checkout -b feature/your-feature-name

# Or for bug fixes:
git checkout -b fix/issue-description
```

### 2. Make Your Changes

- Write clear, readable code
- Follow Python PEP 8 style guidelines
- Add comments for complex logic
- Update documentation as needed

### 3. Test Your Changes

```bash
# Format your code
black .
isort .

# Run any available tests
pytest

# Test the unified GUI (recommended)
python Aetherra/gui/launch_aetherra_gui.py

# Or test components individually:
# React frontend only
cd Aetherra/lyrixa_core/gui && npm run dev

# Flask API server only
python Aetherra/gui/web_interface_server.py --debug

# Test core functionality
python aetherra_os_launcher.py --mode test
```

### 4. Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "✨ Add new feature: brief description

- Detailed explanation of what was added
- Any breaking changes
- Reference to issues (closes #123)"
```

### 5. Push and Create Pull Request

```bash
# Push your branch to your fork
git push origin feature/your-feature-name

# Create a pull request on GitHub
# - Use a clear title and description
# - Reference any related issues
# - Add screenshots for UI changes
```

## 📋 Contribution Guidelines

### Code Style

- **Python**: Follow PEP 8, use Black for formatting
- **Naming**: Use descriptive variable and function names
- **Comments**: Explain complex logic and algorithms
- **Docstrings**: Use Google-style docstrings for functions and classes

### Commit Messages

Use conventional commit format:

```
type(scope): brief description

Detailed explanation if needed

- Key changes
- Breaking changes
- Issue references
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Pull Request Guidelines

1. **Title**: Clear, descriptive title
2. **Description**: Explain what and why
3. **Testing**: Describe how you tested
4. **Screenshots**: For UI changes
5. **Breaking Changes**: Clearly document any breaking changes

## 🎯 Areas Where We Need Help

### 🔥 High Priority
- **Web Interface**: Enhance the cyberpunk neural interface
- **AI Agents**: Develop new AI agent capabilities
- **Memory Systems**: Improve quantum memory management
- **Documentation**: API documentation and user guides
- **Testing**: Unit tests and integration tests

### 🚀 Medium Priority
- **Performance**: Optimize system performance
- **Security**: Security audits and improvements
- **Mobile Support**: Mobile-responsive web interface
- **Plugins**: Plugin system development
- **Internationalization**: Multi-language support

### 💡 Ideas Welcome
- **New Features**: Creative AI OS features
- **Integrations**: Third-party service integrations
- **Tools**: Developer tools and utilities
- **Examples**: Usage examples and tutorials

## 🐛 Bug Reports

### Before Reporting
1. Check existing issues
2. Test with latest version
3. Provide minimal reproduction

### Bug Report Template
```markdown
**Bug Description**
Clear description of the bug

**Steps to Reproduce**
1. Step one
2. Step two
3. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [Windows/macOS/Linux]
- Python version: [3.x.x]
- Aetherra version: [x.x.x]

**Additional Context**
Screenshots, logs, etc.
```

## ✨ Feature Requests

### Feature Request Template
```markdown
**Feature Description**
Clear description of the feature

**Use Case**
Why is this feature needed?

**Proposed Solution**
How should it work?

**Alternatives Considered**
Other ways to solve this

**Additional Context**
Screenshots, mockups, etc.
```

## 🏗️ Project Structure

```
Aetherra/
├── 🧠 Aetherra/              # Core system
│   ├── gui/                  # Web interface
│   ├── core/                 # Core AI components
│   ├── lyrixa/               # AI assistant
│   └── api/                  # API endpoints
├── 🚀 aetherra_os_launcher.py # OS launcher
├── ⚡ aetherra_kernel_loop.py # System kernel
├── 🌐 aetherra_service_registry.py # Service management
├── 📋 requirements.txt       # Dependencies
├── 📖 README.md             # Project overview
└── 🤝 CONTRIBUTING.md       # This file
```

## [TOOL] Development Tips

### Local Development
- Use the `--debug` flag for development
- Check logs in the console for errors
- Use the web interface for testing: `http://127.0.0.1:8686`

### Testing
- Test both web interface and command-line functionality
- Verify AI features work with your API keys
- Check that new features don't break existing functionality

### Performance
- Profile your code for performance issues
- Optimize database queries
- Consider memory usage for large operations

### Recommended VS Code Extensions

For the best development experience, we recommend installing these VS Code extensions:

#### Essential Extensions
- **[GitLens](https://marketplace.visualstudio.com/items?itemName=eamodio.gitlens)** (`eamodio.gitlens`)
  - 🔍 See git blame annotations and code authorship at a glance
  - 📊 Rich git visualizations and powerful comparison commands
  - 🌊 Navigate git history and explore repositories seamlessly
  - Perfect for understanding code changes and contributor history

#### Additional Helpful Extensions
- **[Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)** - Python language support
- **[Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)** - Fast Python language server
- **[Black Formatter](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter)** - Code formatting
- **[autoDocstring](https://marketplace.visualstudio.com/items?itemName=njpwerner.autodocstring)** - Generate docstrings
- **[Thunder Client](https://marketplace.visualstudio.com/items?itemName=rangav.vscode-thunder-client)** - API testing

#### Quick Install
You can install GitLens directly from VS Code:
1. Open VS Code Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Type: `Extensions: Install Extensions`
3. Search for "GitLens" and install `eamodio.gitlens`

Or use the VS Code command line:
```bash
code --install-extension eamodio.gitlens
```

## 📚 Resources

### Documentation
- [Aetherra Documentation](docs/)
- [API Reference](Aetherra/api/README.md)
- [Web Interface Guide](Aetherra/gui/README.md)

### Community
- [GitHub Discussions](https://github.com/AetherraLabs/Aetherra/discussions)
- [Issues](https://github.com/AetherraLabs/Aetherra/issues)
- [Project Board](https://github.com/AetherraLabs/Aetherra/projects)

### External Resources
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SocketIO Documentation](https://python-socketio.readthedocs.io/)
- [OpenAI API](https://platform.openai.com/docs)

## 🎖️ Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- Hall of Fame for outstanding contributions

## 📝 License

By contributing to Aetherra, you agree that your contributions will be licensed under the GPL-3.0 License.

## ❓ Questions?

- **General Questions**: Use [GitHub Discussions](https://github.com/AetherraLabs/Aetherra/discussions)
- **Bug Reports**: Create an [Issue](https://github.com/AetherraLabs/Aetherra/issues)
- **Feature Requests**: Use [GitHub Discussions](https://github.com/AetherraLabs/Aetherra/discussions)

---

## 🌟 Thank You!

Thank you for contributing to Aetherra! Every contribution, no matter how small, helps make Aetherra better for everyone. Together, we're building the future of AI-native development! 🚀

**Happy Coding!** 💻✨
