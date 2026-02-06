# Contributing to LaTeX to Beamer Converter

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/AR.git
   cd AR
   ```
3. **Install dependencies**:
   ```bash
   uv sync
   ```
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Add docstrings to all public functions and classes
- Keep functions focused and under 50 lines when possible

Example:
```python
def _sanitize_title(self, title: str, max_words: int = 6) -> tuple[str, str]:
    """
    Enforce SHORT TITLE LAW: cap at 6 words maximum.

    Args:
        title: Raw title text from LaTeX
        max_words: Maximum words allowed in title

    Returns:
        Tuple of (short_title, full_description)
    """
    # Implementation...
```

### Testing

Before submitting your PR:

1. **Run the test suite**:
   ```bash
   uv run pip install pytest
   uv run pytest tests/ -v
   ```

2. **Test with multiple papers**: Try your changes with at least 2-3 different LaTeX papers
3. **Check edge cases**:
   - Papers with no figures
   - Papers with many tables
   - Papers with long section names
   - Papers with complex equations

4. **Verify LaTeX compilation**: Ensure generated `.tex` files compile without errors:
   ```bash
   pdflatex output.tex
   ```

### Adding Tests

When adding new features, please add corresponding tests:

```python
# tests/test_beamer_generator.py
class TestYourFeature:
    def setup_method(self):
        self.generator = BeamerGenerator(...)

    def test_feature_works(self):
        # Your test here
        assert result == expected
```

Test files should:
- Be in `tests/` directory
- Start with `test_` prefix
- Use pytest assertions
- Have clear docstrings explaining what's tested


### The Three Laws Must Hold

All contributions must preserve the **Three Laws of Slide Generation**:

1. **SHORT TITLE LAW**: Titles must never exceed 6 words
2. **NO GHOST COLUMNS**: Only use column layouts when images exist
3. **CAPTION SANITIZATION**: Never split sentences between title and body

If your change affects slide generation, verify these laws still hold.

### The 8 Fix Protocols Must Work

Ensure your changes don't break any of the 8 Fix Protocols:

1. Title length enforcement
2. Table rendering with booktabs
3. Citation removal
4. Ampersand handling
5. Column layout safety
6. Manual break stripping
7. Demo mode prevention
8. Path sanitization

## What to Contribute

### High Priority
- **Bug fixes**: LaTeX compilation errors, table rendering issues
- **Edge case handling**: Unusual LaTeX constructs, complex formatting
- **Performance improvements**: Faster parsing, better memory usage
- **Documentation**: Clarify unclear sections, add examples

### Medium Priority
- **New features**: Additional LaTeX constructs support (algorithms, listings)
- **Output formats**: Support for other presentation frameworks (reveal.js, PowerPoint)
- **Configuration**: More customization options for slide layout

### Low Priority
- **UI improvements**: Better CLI output, progress bars
- **Testing**: Unit tests, integration tests
- **CI/CD**: GitHub Actions workflows

## Pull Request Process

1. **Update documentation**: If you change functionality, update README.md
2. **Add examples**: If adding features, provide usage examples
3. **Write clear commit messages**:
   ```
   Add table row splitting for concatenated data

   - Implement regex pattern matching for "Mystery N" patterns
   - Split concatenated rows before table detection
   - Fixes issue where multi-row tables render as single bullet
   ```

4. **Create pull request**:
   - Use a descriptive title
   - Reference any related issues
   - Explain what changed and why
   - Include before/after examples if applicable

5. **Respond to feedback**: Be open to suggestions and iterate on your PR

## Issue Reporting

When reporting bugs, include:

1. **Minimal reproducible example**: Smallest LaTeX file that triggers the bug
2. **Expected behavior**: What should happen
3. **Actual behavior**: What actually happens
4. **Environment**: OS, Python version, uv version
5. **Error messages**: Full stack traces if applicable

Example:
```
**Bug**: Tables with 3 columns render incorrectly

**Input LaTeX**:
\begin{tabular}{lcc}
Header 1 & Header 2 & Header 3 \\
Row 1 & val1 & val2 \\
\end{tabular}

**Expected**: Proper 3-column booktabs table

**Actual**: All content in first column, malformed layout

**Environment**:
- OS: macOS 14.0
- Python: 3.11.0
- uv: 0.5.0
```

## Code Review Criteria

Pull requests will be evaluated on:

1. **Correctness**: Does it fix the issue or add the feature correctly?
2. **Generality**: Does it work for all papers, not just one specific case?
3. **Simplicity**: Is it the simplest solution that works?
4. **Compatibility**: Does it break existing functionality?
5. **Documentation**: Is it well-documented and easy to understand?

## Community Guidelines

- Be respectful and constructive
- Help others learn and improve
- Focus on the code, not the person
- Assume good intentions
- Welcome newcomers

## Questions?

- Open an issue with the `question` label
- Check existing issues first
- Be specific about what you're trying to do

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for making this tool better for everyone!
