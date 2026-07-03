# Contributing to Shadow-OT

Thank you for your interest in contributing to Shadow-OT! This document provides guidelines for contributing to the project.

## 🤝 How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Environment details (OS, Docker version, etc.)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:
- A clear description of the enhancement
- Why this would be useful
- Potential implementation approach
- Any relevant examples

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** with clear, concise commits
3. **Test your changes** thoroughly
4. **Update documentation** if needed
5. **Submit a pull request** with a clear description

## 🛠️ Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/shadowot.git
cd shadowot

# Create a feature branch
git checkout -b feature/your-feature-name

# Make changes and test
docker-compose build
docker-compose up -d

# Run tests
docker-compose exec api pytest tests/
```

## 📝 Coding Standards

### Python
- Follow PEP 8 style guide
- Use meaningful variable names
- Add docstrings to functions and classes
- Keep functions small and focused
- Write unit tests for new features

### JavaScript/React
- Follow ESLint configuration
- Use functional components with hooks
- Keep components small and reusable
- Add PropTypes for type checking
- Write clear component documentation

### Docker
- Keep Dockerfiles simple and efficient
- Use multi-stage builds where appropriate
- Minimize image layers
- Document environment variables

## 🧪 Testing

Before submitting a PR, ensure:
- All existing tests pass
- New features have test coverage
- No console errors in the dashboard
- Docker containers build successfully
- Documentation is updated

## 📚 Documentation

- Update README.md for user-facing changes
- Add inline code comments for complex logic
- Update API documentation for new endpoints
- Create/update architecture diagrams if needed

## 🔐 Security

- Never commit sensitive data (credentials, API keys)
- Use environment variables for configuration
- Report security vulnerabilities privately
- Follow secure coding practices

## 💬 Communication

- Be respectful and constructive
- Ask questions if something is unclear
- Provide context in discussions
- Be patient with review process

## 📜 Code of Conduct

- Be welcoming and inclusive
- Respect different viewpoints
- Accept constructive criticism gracefully
- Focus on what's best for the community

## 🎯 Priority Areas

We especially welcome contributions in:
- New protocol support (DNP3, IEC 104, etc.)
- ML model improvements
- UI/UX enhancements
- Documentation improvements
- Bug fixes
- Performance optimizations

## 📞 Questions?

Feel free to open an issue for questions or reach out to the maintainers.

Thank you for contributing to Shadow-OT! 🙏
