# Contributing to Toyota SS.lv Bot

Thank you for your interest in contributing! Here's how you can help make this project better.

## 🚀 Quick Start for Contributors

1. **Fork the repository**
2. **Clone your fork:**
   ```bash
   git clone https://github.com/yourusername/toyota-ss-lv-bot.git
   cd toyota-ss-lv-bot
   ```
3. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make your changes**
5. **Test thoroughly**
6. **Submit a pull request**

## 🛠️ Development Setup

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your bot token

# Run the bot
python toyota_bot_fixed.py
```

### Docker Development
```bash
# Build and run with Docker
docker-compose up --build

# View logs
docker-compose logs -f toyota-bot
```

## 📝 What We're Looking For

### High Priority
- **🐛 Bug fixes** - Especially connection issues or parsing errors
- **⚡ Performance improvements** - Memory usage, response time
- **🔒 Security enhancements** - Input validation, error handling
- **🧪 Tests** - Unit tests, integration tests

### Medium Priority  
- **📊 New monitoring sources** - Additional SS.lv sections
- **🎯 Enhanced filtering** - More sophisticated car matching
- **📱 UI improvements** - Better message formatting
- **🌍 Internationalization** - Support for other languages

### Nice to Have
- **📈 Analytics** - Usage statistics, performance metrics
- **🎨 Customization** - User-specific filters
- **🔔 Advanced notifications** - Price alerts, condition changes

## 🧪 Testing

### Manual Testing
```bash
# Test complete system
python test_complete_system.py

# Test phone extraction
python test_phone_extraction.py

# Debug specific features
python debug_phone_extraction.py
```

### Automated Testing
```bash
# Run CI pipeline locally
pytest tests/ -v --cov=toyota_bot_fixed

# Lint code
pylint toyota_bot_fixed.py

# Security scan
bandit -r . -f json
```

## 📋 Code Guidelines

### Python Style
- **Follow PEP 8** - Use consistent formatting
- **Type hints** - Add type annotations where helpful
- **Docstrings** - Document functions and classes
- **Error handling** - Proper exception handling

### Git Commits
- **Descriptive messages** - Explain what and why
- **Small commits** - One logical change per commit
- **Present tense** - "Add feature" not "Added feature"

### Examples:
```bash
# Good commits
git commit -m "Add crash severity detection for damaged vehicles"
git commit -m "Fix memory leak in phone extraction caching"
git commit -m "Improve error handling for network timeouts"

# Avoid
git commit -m "Fix bug"
git commit -m "Update code"
git commit -m "Changes"
```

## 🔍 Areas for Contribution

### Bot Features
- **Smart filtering logic** (`filter_all_listings()`, `filter_crash_toyotas()`)
- **Crash detection** (`generate_crash_labels()`)
- **Message formatting** (`format_listings_message()`)
- **Phone extraction** (`extract_phone_with_js()`)

### Infrastructure
- **Docker optimization** (multi-stage builds, smaller images)
- **CI/CD improvements** (better testing, deployment)
- **Monitoring** (health checks, alerts)
- **Documentation** (API docs, tutorials)

### Data Processing
- **HTML parsing** (BeautifulSoup improvements)
- **Data validation** (input sanitization)
- **Caching strategies** (Redis, file-based)
- **Rate limiting** (respectful scraping)

## 🐛 Bug Reports

When reporting bugs, include:

1. **Environment details:**
   - Python version
   - Operating system
   - Docker version (if using Docker)

2. **Steps to reproduce:**
   ```
   1. Start the bot with...
   2. Send command...
   3. Observe error...
   ```

3. **Expected vs actual behavior**

4. **Logs and error messages:**
   ```
   Include relevant log entries
   ```

5. **Screenshots** (if applicable)

## ✨ Feature Requests

For new features:

1. **Check existing issues** - Avoid duplicates
2. **Describe the problem** - What need does this address?
3. **Propose solution** - How should it work?
4. **Consider alternatives** - What other options exist?
5. **Implementation plan** - Break down into steps

## 📞 Getting Help

- **GitHub Issues** - Bug reports, feature requests
- **GitHub Discussions** - Questions, ideas, general discussion
- **Code Review** - Submit PRs for feedback

## 🏆 Recognition

Contributors will be:
- **Listed in README** - Recognition for significant contributions
- **Mentioned in releases** - Credit for features and fixes
- **Invited to collaborate** - Ongoing participation opportunities

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You

Every contribution helps make this project better for the Toyota enthusiast community in Latvia. Whether it's code, documentation, bug reports, or feature ideas - we appreciate your help!

---

Happy coding! 🚗💻