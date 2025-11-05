# Contributing to MemoryStack

First off, thank you for considering contributing to MemoryStack! 🎉

It's people like you that make MemoryStack such a great tool. We welcome contributions from everyone, whether it's:

- 🐛 Bug reports
- 💡 Feature requests
- 📝 Documentation improvements
- 🔧 Code contributions
- 🌍 Translations
- ✨ New backend adapters

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Redis (for testing)
- Basic understanding of FastAPI and async Python
- Git

### Development Setup

1. **Fork the repository**
   ```bash
   # Click "Fork" on GitHub, then:
   git clone https://github.com/YOUR_USERNAME/memorystack
   cd memorystack
   ```

2. **Set up development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Dev dependencies
   ```

3. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

4. **Make your changes**
   - Write code
   - Add tests
   - Update documentation

5. **Test your changes**
   ```bash
   # Run tests
   pytest tests/

   # Run linting
   black src/
   flake8 src/
   mypy src/
   ```

6. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   # or
   git commit -m "fix: resolve issue with memory leaks"
   ```

7. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   # Then create a Pull Request on GitHub
   ```

## Contribution Guidelines

### Code Style

- **Python**: Follow [PEP 8](https://pep8.org/)
- **Formatting**: Use `black` with default settings
- **Imports**: Use `isort` for organizing imports
- **Type hints**: Use type hints where possible
- **Docstrings**: Use Google-style docstrings

Example:
```python
def search_memories(
    query: str,
    user_id: str,
    limit: int = 5
) -> List[Dict]:
    """Search for relevant memories.

    Args:
        query: The search query
        user_id: User identifier
        limit: Maximum number of results

    Returns:
        List of memory dictionaries with scores

    Raises:
        MemoryBackendError: If backend is unavailable
    """
    # Implementation
```

### Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat: add Pinecone backend adapter
fix: resolve Redis connection timeout
docs: update installation guide
refactor: simplify query classification logic
test: add tests for progressive injection
```

### Pull Request Process

1. **Update documentation** if you changed APIs or added features
2. **Add tests** for new functionality
3. **Update CHANGELOG.md** with your changes
4. **Ensure all tests pass** before submitting
5. **Request review** from maintainers
6. **Address feedback** promptly and professionally

### Pull Request Template

Your PR should include:

```markdown
## Description
Brief description of what this PR does

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added new tests for new features
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No breaking changes (or documented)
```

## Areas for Contribution

### 🔌 **Backend Adapters**

Create adapters for new memory backends:

- Pinecone
- Weaviate
- Qdrant
- Chroma
- Milvus
- Your custom backend

See `src/memorystack/backends/base.py` for the interface.

### 🌍 **Language Support**

Add query patterns for new languages:

- Spanish
- French
- German
- Japanese
- Your language

See `src/memorystack/memory/intelligent_router.py`.

### 📝 **Documentation**

- Improve existing docs
- Add tutorials
- Create video guides
- Write blog posts
- Translate documentation

### 🧪 **Testing**

- Add unit tests
- Add integration tests
- Improve test coverage
- Add performance benchmarks

### ✨ **Features**

Check our [roadmap](README.md#-roadmap) for planned features or suggest new ones!

## Reporting Bugs

### Before Submitting

1. **Check existing issues** to avoid duplicates
2. **Try the latest version** - bug might be fixed
3. **Gather information**:
   - MemoryStack version
   - Python version
   - Operating system
   - Backend being used
   - Steps to reproduce

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Start MemoryStack with...
2. Send request with...
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Environment**
- MemoryStack version: X.Y.Z
- Python version: 3.X.Y
- OS: Ubuntu 22.04 / macOS 14 / Windows 11
- Backend: Graphiti / Supermemory / etc.

**Logs**
```
Paste relevant logs here
```

**Additional context**
Any other information that might help.
```

## Suggesting Features

We love new ideas! Before suggesting:

1. **Check existing issues** and discussions
2. **Explain the use case** - why is this needed?
3. **Describe the solution** - how should it work?
4. **Consider alternatives** - are there other ways?

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem. Ex. I'm frustrated when...

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Other solutions or features you've considered.

**Additional context**
Screenshots, examples, or mockups.
```

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of:

- Age
- Body size
- Disability
- Ethnicity
- Gender identity and expression
- Level of experience
- Nationality
- Personal appearance
- Race
- Religion
- Sexual identity and orientation

### Our Standards

**Positive behavior:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what's best for the community
- Showing empathy towards others

**Unacceptable behavior:**
- Trolling, insulting, or derogatory comments
- Public or private harassment
- Publishing others' private information
- Any conduct which could reasonably be considered inappropriate

### Enforcement

Instances of abusive behavior may be reported to the project maintainers. All complaints will be reviewed and investigated promptly and fairly.

## Questions?

- 💬 [GitHub Discussions](https://github.com/joaolvivas/memorystack/discussions)
- 🐛 [GitHub Issues](https://github.com/joaolvivas/memorystack/issues)
- 📧 Email: [your-email]

## Recognition

Contributors will be recognized in:
- README.md
- CHANGELOG.md
- GitHub contributors page

Thank you for making MemoryStack better! 🚀🧠
