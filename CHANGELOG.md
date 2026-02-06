# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial public release
- Complete GitHub repository setup
- Comprehensive documentation (README, CONTRIBUTING, EXAMPLES)
- CI/CD workflow with GitHub Actions
- MIT License

## [0.1.0] - 2024-02-06

### Added
- **The Three Laws of Slide Generation**
  - SHORT TITLE LAW: 6-word maximum for slide titles
  - NO GHOST COLUMNS: Only use columns when images exist
  - CAPTION SANITIZATION: Never split sentences between title and body

- **The 8 Fix Protocols**
  1. Title Length Enforcement
  2. Table Rendering with Booktabs
  3. Citation Removal
  4. Ampersand Handling
  5. Column Layout Safety
  6. Manual Break Stripping
  7. Demo Mode Prevention
  8. Path Sanitization

- **Core Features**
  - LaTeX document parsing and structure extraction
  - Automatic Beamer slide generation
  - Professional table formatting with booktabs
  - Smart figure layout with column detection
  - Intelligent text filtering for narrow columns
  - Section prioritization and slide limiting

- **Pipeline Components**
  - `tex_cleaner.py`: LaTeX preprocessing and macro extraction
  - `tex_parser.py`: Hierarchical document parsing
  - `beamer_generator.py`: Slide generation engine
  - `presentation_agent.py`: Pipeline orchestrator
  - `content_extractor.py`: Optional LLM summarization
  - `cli.py`: Command-line interface

- **Table Support**
  - Automatic table detection via ampersand delimiters
  - Row splitting for concatenated data
  - Auto-generated column headers for numbered items
  - Professional booktabs formatting
  - Smart font sizing (`\scriptsize`) for data-heavy tables

- **Figure Handling**
  - Image existence checking
  - Path sanitization (strip long prefixes)
  - Column layout with image + bullets
  - Fallback to full-width layout if image missing
  - Long bullet filtering for narrow columns (>100 words or >500 chars)

- **Configuration**
  - Environment-based settings (.env)
  - Optional Gemini API integration
  - Slide count customization via style prompts
  - Flexible output paths

### Changed
- Improved text node combination to preserve table structure
- Enhanced bullet detection to prevent table rows from becoming bullets
- Optimized column layout logic to prevent ghost columns

### Fixed
- Tables rendering as itemized lists instead of proper tabular
- Long figure captions creating walls of text in narrow columns
- Image paths containing long arXiv folder prefixes
- Ampersands being escaped in table cells
- Demo mode causing black image placeholders
- LaTeX commands in titles causing compilation errors
- Concatenated table rows appearing as single strings

## [0.0.1] - 2024-01-XX

### Added
- Initial prototype with basic LaTeX to Beamer conversion
- Simple section parsing
- Basic figure and equation detection
- Command-line interface skeleton

---

## Version History Notes

### Breaking Changes
None yet (pre-1.0 release)

### Deprecations
- Hugging Face client (`hf_client.py`) - Gemini API preferred
- LLM features are optional; system works with rule-based processing

### Migration Guide
N/A - Initial release

---

## Future Roadmap

### v0.2.0 (Planned)
- [ ] Support for algorithm environments
- [ ] Better handling of subfigures
- [ ] Custom Beamer themes support
- [ ] Multiple output formats (reveal.js, PowerPoint)

### v0.3.0 (Planned)
- [ ] Interactive mode for slide customization
- [ ] Web interface
- [ ] Batch processing improvements
- [ ] Advanced table detection (multi-line cells)

### v1.0.0 (Planned)
- [ ] Stable API
- [ ] Comprehensive test suite
- [ ] Full documentation site
- [ ] PyPI package release

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute changes.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.
