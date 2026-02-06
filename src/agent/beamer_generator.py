"""
Beamer Presentation Generator
=============================

Converts parsed TeX structure into Beamer slides.

Beamer is LaTeX-based, so we're generating LaTeX code that produces PDF slides.
This is much cleaner than converting to PowerPoint XML.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional
from .tex_parser import TexNode


class BeamerGenerator:
    """
    Generates Beamer presentation from parsed TeX nodes.
    
    Usage:
        generator = BeamerGenerator(
            title="My Paper",
            author="John Doe",
            institute="MIT"
        )
        beamer_code = generator.generate(parsed_nodes)
    """
    
    def __init__(self, title: str, author: str, institute: str = "", date: str = "", figure_root: Optional[Path] = None, max_slides: int = 20, content_extractor=None):
        self.title = title
        self.author = author
        self.institute = institute
        self.date = date or r"\today"
        self.slide_count = 0
        self.figure_root = Path(figure_root).resolve() if figure_root else None
        self.max_slides = max_slides  # Default 20 slides total
        self.content_extractor = content_extractor  # Optional LLM-powered content generator

        # Section priority configuration
        self.high_priority_keywords = [
            'method', 'algorithm', 'approach', 'experiment', 'result', 'evaluation',
            'technique', 'model', 'architecture', 'analysis', 'finding', 'ablation',
            'implementation', 'performance', 'evaluation', 'validation'
        ]

        self.low_priority_keywords = [
            'introduction', 'background', 'related work', 'prior work', 'motivation',
            'preliminaries', 'notation'
        ]

        self.skip_keywords = [
            'reference', 'bibliography', 'appendix', 'acknowledgement', 'supplementary',
            'acknowledgment', 'prompt example', 'naming variants', 'use of large language'
        ]
    def generate(self, nodes: List[TexNode], user_prompt: str = "", summary_content: Optional[str] = None) -> str:
        """
        Generate Beamer LaTeX code from parsed nodes with intelligent filtering.

        Args:
            nodes: List of TexNode objects from parser
            user_prompt: Optional user direction (e.g., "2 slides per section, emphasize figures")
            summary_content: Optional LLM-generated summary for overview slide

        Returns:
            Complete Beamer LaTeX code with limited slide count
        """
        beamer_code = self._generate_preamble()
        beamer_code += "\n\\begin{document}\n\n"

        # Title slide (counts as 1)
        beamer_code += self._generate_title_slide()

        # Optional overview slide informed by LLM summary (counts as 1)
        if summary_content:
            beamer_code += self._generate_overview_slide(summary_content)

        # Filter and prioritize sections based on NO-BORE rule
        filtered_sections = self._filter_and_prioritize_sections(nodes)

        # Generate content slides with strict limits
        for section_info in filtered_sections:
            if self.slide_count >= self.max_slides:
                break  # Stop when we hit max slides

            node = section_info['node']
            priority = section_info['priority']
            max_slides_for_section = section_info['max_slides']

            beamer_code += self._generate_section_frames(
                node,
                max_slides=max_slides_for_section,
                priority=priority
            )

        beamer_code += "\n\\end{document}\n"

        return beamer_code
    
    def _generate_preamble(self) -> str:
        """Generate Beamer document preamble with Fix Protocols applied"""
        return r"""\documentclass{beamer}
\usetheme{Madrid}
\usecolortheme{default}

\usepackage[utf8]{inputenc}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{graphicx}
\usepackage{cleveref}
\usepackage{booktabs}

\title{""" + self.title + r"""}
\author{""" + self.author + r"""}
\institute{""" + self.institute + r"""}
\date{""" + self.date + r"""}
"""

    def _classify_section_priority(self, section_title: str) -> str:
        """
        Classify section priority based on keywords.
        Returns: 'skip', 'low', 'medium', or 'high'
        """
        title_lower = section_title.lower()

        # Check if should be skipped entirely
        if any(keyword in title_lower for keyword in self.skip_keywords):
            return 'skip'

        # Check if high priority
        if any(keyword in title_lower for keyword in self.high_priority_keywords):
            return 'high'

        # Check if low priority
        if any(keyword in title_lower for keyword in self.low_priority_keywords):
            return 'low'

        # Default to medium priority
        return 'medium'

    def _filter_and_prioritize_sections(self, nodes: List[TexNode]) -> List[Dict]:
        """
        Filter and prioritize sections according to NO-BORE rule.
        Returns list of section info dicts with priority and max_slides.
        """
        sections = []
        low_priority_combined_content = []

        for node in nodes:
            if node.type != 'section':
                continue

            priority = self._classify_section_priority(node.content)

            if priority == 'skip':
                continue  # Skip entirely (appendices, acknowledgements, etc.)

            if priority == 'low':
                # Combine all low-priority sections into one
                low_priority_combined_content.append(node)
                continue

            # Assign max slides based on priority
            if priority == 'high':
                max_slides_for_section = 3  # High priority: up to 3 slides
            elif priority == 'medium':
                max_slides_for_section = 2  # Medium priority: up to 2 slides
            else:
                max_slides_for_section = 1

            sections.append({
                'node': node,
                'priority': priority,
                'max_slides': max_slides_for_section
            })

        # Add combined low-priority section as 1 slide at the beginning
        if low_priority_combined_content:
            combined_node = self._combine_low_priority_sections(low_priority_combined_content)
            sections.insert(0, {
                'node': combined_node,
                'priority': 'low',
                'max_slides': 1
            })

        return sections

    def _combine_low_priority_sections(self, nodes: List[TexNode]) -> TexNode:
        """
        Combine multiple low-priority sections (Intro, Background, Related Work) into one.
        Uses paragraph combining to avoid broken lines.
        """
        combined_title = "Background \\& Context"  # Escape ampersand for LaTeX
        combined_node = TexNode(type='section', content=combined_title, level=0)

        # Take only first 2-3 key bullets from each section
        for node in nodes[:3]:  # Max 3 low-priority sections
            # Get text children and combine into paragraphs
            text_children = [c for c in node.children if c.type == 'text']
            if text_children:
                # Combine text nodes into paragraphs
                paragraphs = self._combine_text_nodes(text_children)
                # Take first 2 paragraphs and create text nodes
                for para in paragraphs[:2]:
                    para_node = TexNode(type='text', content=para, level=0)
                    combined_node.children.append(para_node)

        return combined_node

    def _generate_title_slide(self) -> str:
        """Generate title slide"""
        self.slide_count += 1
        return r"""\begin{frame}
  \titlepage
\end{frame}

"""

    def _generate_overview_slide(self, summary_content: str) -> str:
        """
        Generate an overview slide from LLM summary.
        FIX PROTOCOL #3 & #7: Remove conversational filler and useless content.
        """
        self.slide_count += 1

        cleaned_lines: List[str] = []
        for line in summary_content.split("\n"):
            stripped = line.strip(" -*\t#")
            if not stripped:
                continue

            lowered = stripped.lower()

            # FIX PROTOCOL #7: Remove useless overview content
            skip_patterns = [
                "slide", ":", "here's", "here is", "presentation", "based on",
                "following", "provided", "document", "outline", "overview",
                "---", "--", "===", "***"
            ]

            if any(pattern in lowered for pattern in skip_patterns):
                continue

            # FIX PROTOCOL #3: Remove Markdown syntax
            # Convert **bold** to \textbf{bold}
            stripped = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', stripped)
            # Convert *italic* to \textit{italic}
            stripped = re.sub(r'\*(.+?)\*', r'\\textit{\1}', stripped)
            # Remove list markers (*, -, 1., etc.)
            stripped = re.sub(r'^(\d+\.|\*|-)\s+', '', stripped)

            sanitized = self._sanitize_bullet(stripped, escape_ampersand=True)
            if sanitized and len(sanitized) > 10:  # Skip very short fragments
                cleaned_lines.append(sanitized)

        if not cleaned_lines:
            return ""  # Don't generate empty overview

        # Limit to first 5-6 key bullets only
        cleaned_lines = cleaned_lines[:6]

        bullets = "\n".join([f"  \\item {line}" for line in cleaned_lines])
        return f"""\n\\begin{{frame}}
\\frametitle{{Overview}}

\\begin{{itemize}}
{bullets}
\\end{{itemize}}

\\end{{frame}}
"""
    
    def _generate_slide_from_node(self, node: TexNode, depth: int = 0) -> str:
        """
        Recursively generate slides from node hierarchy.
        
        Strategy:
        - Section headers become new slides
        - Subsection headers become bullet points or new slides
        - Text becomes bullet items or slide content
        - Equations are preserved as-is
        - Figures/citations are noted
        """
        
        if node.type == 'section':
            return self._generate_section_frames(node)
        
        elif node.type == 'subsection':
            return self._generate_subsection_content(node)
        
        elif node.type == 'equation':
            return self._generate_equation_slide(node)
        
        elif node.type == 'text':
            return self._generate_text_bullet(node)
        
        elif node.type == 'citation':
            return self._generate_citation_note(node)
        
        return ""

    def _generate_section_frames(self, node: TexNode, max_slides: int = 2, priority: str = 'medium') -> str:
        """
        Generate frames for a section respecting slide rules and limits.

        Args:
            node: Section node to generate slides for
            max_slides: Maximum number of slides for this section
            priority: Section priority ('low', 'medium', 'high')
        """
        frames = []
        slides_generated_for_section = 0

        # Collect children by type
        figures = [c for c in node.children if c.type == 'figure']
        equations = [c for c in node.children if c.type == 'equation']
        texts = [c for c in node.children if c.type == 'text']

        # CRITICAL FIX: Combine consecutive text nodes into paragraphs FIRST
        # This prevents line-broken text from becoming separate bullets
        combined_paragraphs = self._combine_text_nodes(texts)

        # Generate bullets: Use LLM if available, otherwise use rule-based splitting
        text_bullets: List[str] = []

        if self.content_extractor:
            # PRIMARY: LLM-POWERED intelligent content summarization
            # Combine all paragraph text for context
            section_text = ' '.join(combined_paragraphs)

            # Determine max bullets based on priority
            if priority == 'low':
                max_bullets_for_llm = 4
            elif priority == 'medium':
                max_bullets_for_llm = 8
            else:  # high priority
                max_bullets_for_llm = 12

            try:
                # MULTIMODAL: If figure exists, use image-aware generation
                if figures and hasattr(self.content_extractor, 'supports_multimodal') and self.content_extractor.supports_multimodal:
                    fig = figures[0]
                    image_path = fig.meta.get('image_path', '') if fig.meta else ''

                    if image_path and self.figure_root:
                        # Resolve image path relative to paper root
                        full_image_path = self._resolve_image_path(image_path)
                        text_bullets = self.content_extractor.generate_slide_bullets_with_image(
                            section_content=section_text,
                            section_title=node.content,
                            image_path=full_image_path,
                            max_bullets=max_bullets_for_llm
                        )
                    else:
                        # No valid image path, use text-only
                        text_bullets = self.content_extractor.generate_slide_bullets(
                            section_content=section_text,
                            section_title=node.content,
                            max_bullets=max_bullets_for_llm
                        )
                else:
                    # TEXT-ONLY: No figure or multimodal not supported
                    text_bullets = self.content_extractor.generate_slide_bullets(
                        section_content=section_text,
                        section_title=node.content,
                        max_bullets=max_bullets_for_llm
                    )
            except Exception as e:
                # FALLBACK: Use rule-based if LLM fails (API limit, timeout, etc.)
                print(f"⚠️  LLM generation failed for '{node.content}', using rule fallback: {e}")
                for paragraph in combined_paragraphs:
                    sanitized_text = self._pre_sanitize_text(paragraph)
                    text_bullets.extend(self._split_bullet(sanitized_text))
        else:
            # FALLBACK: Rule-based heuristic (no LLM available)
            for paragraph in combined_paragraphs:
                # Pre-sanitize the full text to handle multi-line citations
                sanitized_text = self._pre_sanitize_text(paragraph)
                # Then split into bullets
                text_bullets.extend(self._split_bullet(sanitized_text))

        # Limit bullets based on priority
        if priority == 'low':
            max_bullets = 4  # Low priority: max 4 bullets total
            text_bullets = text_bullets[:max_bullets]
        elif priority == 'medium':
            max_bullets = 8  # Medium priority: max 8 bullets total
            text_bullets = text_bullets[:max_bullets]
        else:  # high priority
            max_bullets = 15  # High priority: max 15 bullets total
            text_bullets = text_bullets[:max_bullets]

        # Check if we've hit max slides already
        if self.slide_count >= self.max_slides:
            return ""

        # Visual-first if figure exists
        if figures and slides_generated_for_section < max_slides:
            fig = figures[0]
            bullets = text_bullets[:3]  # max 3 bullets with figure
            frames.append(
                self._frame_with_figure(
                    title=fig.meta.get('caption') or node.content,
                    image_path=fig.meta.get('image_path', ''),
                    bullets=bullets,
                )
            )
            slides_generated_for_section += 1
            text_bullets = text_bullets[3:]  # Remove used bullets

        # Equation-focused if no figure but equation exists
        elif equations and slides_generated_for_section < max_slides:
            eq = equations[0]
            bullets = text_bullets[:3]
            frames.append(
                self._frame_with_equation(
                    title=node.content,
                    equation=eq.content,
                    bullets=bullets,
                )
            )
            slides_generated_for_section += 1
            text_bullets = text_bullets[3:]  # Remove used bullets

        # Generate remaining text content slides (if any bullets left and space available)
        if text_bullets and slides_generated_for_section < max_slides:
            # Use smaller chunks for better readability
            bullets_per_slide = 5 if priority == 'high' else 4
            bullet_chunks = self._chunk_bullets(text_bullets, chunk_size=bullets_per_slide)

            # Limit number of continuation slides
            max_continuation_slides = max_slides - slides_generated_for_section
            bullet_chunks = bullet_chunks[:max_continuation_slides]

            for idx, chunk in enumerate(bullet_chunks):
                if slides_generated_for_section >= max_slides:
                    break
                if self.slide_count >= self.max_slides:
                    break

                frames.append(
                    self._frame_with_bullets(
                        title=node.content if idx == 0 else f"{node.content} (cont.)",
                        bullets=chunk,
                    )
                )
                slides_generated_for_section += 1

        return "".join(frames)

    def _resolve_image_path(self, image_path: str) -> str:
        """
        Resolve figure path against figure_root; prefer sanitized short path.
        FIX PROTOCOL #8: Sanitize paths by removing long folder prefixes.
        """
        if not image_path:
            return image_path

        # FIX PROTOCOL #8: Path Sanitization
        # Remove long prefixes like "arXiv-2602.04843v1/figures/img.pdf" -> "figures/img.pdf"
        path = Path(image_path)

        # If path has more than 2 parts, simplify to last 2 (e.g., "figures/img.pdf")
        parts = path.parts
        if len(parts) > 2:
            # Keep only last 2 parts: directory and filename
            sanitized = Path(*parts[-2:])
            image_path = sanitized.as_posix()
            path = Path(image_path)

        # Check if sanitized path exists (relative to cwd or figure_root)
        if path.is_absolute() and path.exists():
            return path.as_posix()

        if self.figure_root:
            candidate = (self.figure_root / image_path).resolve()
            if candidate.exists():
                # Return sanitized path (not the full path from cwd)
                # This keeps the path short and clean in the LaTeX output
                return image_path

        return image_path

    # Utility helpers
    def _combine_text_nodes(self, text_nodes: List[TexNode]) -> List[str]:
        """
        Combine consecutive text nodes into complete paragraphs.
        This prevents parser line-breaks from creating separate bullets.

        SPECIAL CASE: If text nodes look like table rows (contain '&'),
        keep them separate to enable table detection.

        The parser often splits paragraphs into multiple text nodes at line breaks.
        We recombine ALL of them into a single continuous text, then let _split_bullet
        handle the intelligent splitting based on sentence boundaries.
        """
        if not text_nodes:
            return []

        # CRITICAL FIX: Check if these look like table rows
        # If most nodes contain '&', treat them as table rows and DON'T combine
        nodes_with_ampersand = sum(1 for node in text_nodes if '&' in node.content)
        total_nodes = len(text_nodes)

        # If > 50% of nodes contain ampersands, likely a table - keep rows separate
        if nodes_with_ampersand > total_nodes * 0.5:
            table_rows = []
            for node in text_nodes:
                content = node.content.strip()
                if content:
                    table_rows.append(content)
            return table_rows

        # NOT a table - combine normally
        all_text_parts = []

        for node in text_nodes:
            content = node.content.strip()
            if content:
                all_text_parts.append(content)

        if not all_text_parts:
            return []

        # Join all parts with spaces to create continuous text
        combined_text = ' '.join(all_text_parts)

        # Return as a single paragraph - _split_bullet will handle the rest
        return [combined_text]

    def _pre_sanitize_text(self, text: str) -> str:
        """
        Pre-sanitize full text content BEFORE splitting into bullets.
        This catches citations and refs that span multiple lines.
        """
        # Remove ALL citation commands (including multi-line)
        # Match \cite{...} even across line breaks
        text = re.sub(r'\\cite[pt]?\{[^}]+\}', '', text, flags=re.DOTALL)

        # Remove ALL reference commands
        text = re.sub(r'\\[Cc]?ref\{[^}]+\}', '', text, flags=re.DOTALL)
        text = re.sub(r'\\label\{[^}]+\}', '', text, flags=re.DOTALL)

        # Remove manual line breaks
        text = re.sub(r'\\\\(?![a-zA-Z])', ' ', text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _split_bullet(self, text: str, max_len: int = 200) -> List[str]:
        """
        Split long text into multiple bullets, keeping each around max_len characters.
        Handles sentence fragments intelligently to avoid broken bullets.
        INCREASED max_len from 160 to 200 to reduce unnecessary splits.
        """
        # Split on sentence boundaries
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]

        if not sentences:
            return [text.strip()] if text.strip() else []

        parts: List[str] = []
        current = ""

        def is_sentence_fragment(s: str) -> bool:
            """Check if this looks like a sentence fragment (doesn't start with capital)."""
            s = s.strip()
            if not s:
                return True
            # Fragment if: starts lowercase, or very short (< 20 chars)
            return s[0].islower() or len(s) < 20

        def flush_chunk(chunk: List[str]) -> None:
            """Flush chunk and check if it's a fragment that should merge with previous."""
            if not chunk:
                return
            chunk_text = " ".join(chunk)

            # CRITICAL FIX: If this chunk is a fragment (starts lowercase) and we have previous parts,
            # merge it with the last part instead of creating a new bullet
            if parts and is_sentence_fragment(chunk_text):
                parts[-1] = f"{parts[-1]} {chunk_text}"
            else:
                parts.append(chunk_text)

        i = 0
        while i < len(sentences):
            sentence = sentences[i]

            # If this is a fragment and we have more sentences, try to attach it to previous/next
            if is_sentence_fragment(sentence):
                # Attach to current if we have one
                if current:
                    current = f"{current} {sentence}"
                    i += 1
                    continue
                # Otherwise attach to next sentence if available
                elif i + 1 < len(sentences):
                    sentence = f"{sentence} {sentences[i+1]}"
                    i += 1  # Skip the next sentence since we combined it

            # Now try to add sentence to current chunk
            candidate = f"{current} {sentence}".strip() if current else sentence

            if len(candidate) <= max_len:
                current = candidate
            else:
                # Current chunk is full, flush it
                if current:
                    parts.append(current)
                    current = ""

                # Handle sentence that's too long by itself
                if len(sentence) > max_len:
                    words = sentence.split()
                    chunk: List[str] = []
                    chunk_len = 0
                    for w in words:
                        add_len = len(w) + (1 if chunk else 0)
                        if chunk_len + add_len > max_len:
                            flush_chunk(chunk)
                            chunk = [w]
                            chunk_len = len(w)
                        else:
                            chunk.append(w)
                            chunk_len += add_len
                    flush_chunk(chunk)
                else:
                    current = sentence

            i += 1

        # Flush remaining
        if current:
            parts.append(current)

        return parts or [text.strip()]

    def _strip_manual_breaks(self, text: str) -> str:
        """Remove explicit line breaks to keep paragraphs clean."""
        return re.sub(r"\\\\(?![a-zA-Z])", " ", text)

    def _convert_markdown(self, text: str) -> str:
        """Convert simple Markdown emphasis to LaTeX."""
        text = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", text)
        text = re.sub(r"\*(.+?)\*", r"\\textit{\1}", text)
        text = re.sub(r"`([^`]+)`", r"\\texttt{\1}", text)
        return text

    def _sanitize_bullet(self, text: str, escape_ampersand: bool = True) -> str:
        """
        Normalize bullet text for clean LaTeX output.
        CONTENT SANITIZATION RULES (STRICT):
        1. NO CITATION KEYS: Remove \\cite{...}, \\citep{...}, \\citet{...}
        2. NO INTERNAL REFS: Remove \\ref{...}, \\cref{...}, \\Cref{...}, \\label{...}
        3. TEXT NORMALIZATION: Join broken lines, remove manual breaks
        """
        cleaned = text.strip()

        # Remove list markers
        cleaned = re.sub(r"^[*-]\s+", "", cleaned)
        cleaned = re.sub(r"^\d+\.\s+", "", cleaned)

        # RULE 1: NO CITATION KEYS - Remove all citation commands
        # \cite{key1,key2}, \citep{...}, \citet{...}, etc.
        cleaned = re.sub(r'\\cite[pt]?\{[^}]+\}', '', cleaned)

        # RULE 2: NO INTERNAL REFS - Remove all reference commands
        # \ref{...}, \cref{...}, \Cref{...}, \label{...}
        cleaned = re.sub(r'\\[Cc]?ref\{[^}]+\}', '', cleaned)
        cleaned = re.sub(r'\\label\{[^}]+\}', '', cleaned)

        # RULE 3: TEXT NORMALIZATION - Join broken lines
        # Remove manual line breaks (\\) that break sentences
        cleaned = self._strip_manual_breaks(cleaned)

        # Join lines that were artificially broken
        # Replace multiple spaces/newlines with single space
        cleaned = re.sub(r'\s+', ' ', cleaned)

        # Convert markdown (but preserve existing LaTeX)
        cleaned = self._convert_markdown(cleaned)

        # Remove phrases that reference missing sections
        cleaned = re.sub(r'\(see\s+\)', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'in\s+\)', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\(prompt example in\s+\)', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\(\s*\)', '', cleaned)  # Remove empty parens

        # Clean up spacing around punctuation
        cleaned = re.sub(r'\s+([.,;:])', r'\1', cleaned)  # Remove space before punctuation
        cleaned = re.sub(r'([.,;:])\s+', r'\1 ', cleaned)  # Single space after punctuation

        # Final cleanup
        cleaned = cleaned.strip()

        if escape_ampersand:
            cleaned = cleaned.replace("&", r"\&")

        return cleaned

    def _extract_table_rows(self, bullets: List[str]) -> List[List[str]]:
        r"""
        Detect structured rows separated by '&' or '\&' and return tabular rows.
        CRITICAL: Handle both escaped (\&) and unescaped (&) ampersands.
        """
        rows: List[List[str]] = []
        col_count: Optional[int] = None

        # CRITICAL FIX: Split concatenated table rows first
        # Detect patterns like "Mystery 1 & ... Mystery 2 & ..." and split them
        expanded_bullets = []
        for bullet in bullets:
            # Check if this looks like concatenated table rows with numbered items
            # Pattern: "Mystery N & ... text Mystery M &" where N and M are different numbers

            # More flexible pattern: look for "Mystery <digit>" appearing multiple times
            mystery_pattern = r'(Mystery|Test|Item|Row|Case|Scenario)\s+\d+'
            matches = list(re.finditer(mystery_pattern, bullet, re.IGNORECASE))

            if len(matches) >= 2:
                # We have multiple "Mystery N" patterns - likely concatenated rows
                # Split right before each occurrence (except the first)
                parts = []
                prev_start = 0

                for i, match in enumerate(matches):
                    if i == 0:
                        # Skip the first match, just record where it starts
                        prev_start = match.start()
                        continue

                    # Add the segment from previous match start to this match start
                    segment = bullet[prev_start:match.start()].strip()
                    if segment:
                        parts.append(segment)
                    prev_start = match.start()

                # Add the final segment
                final_segment = bullet[prev_start:].strip()
                if final_segment:
                    parts.append(final_segment)

                expanded_bullets.extend(parts)
            else:
                expanded_bullets.append(bullet)

        for raw in expanded_bullets:
            cleaned = self._strip_manual_breaks(raw)

            # Check for both unescaped & and escaped \&
            has_ampersand = "&" in cleaned or r"\&" in cleaned
            if not has_ampersand:
                return []

            # Normalize: temporarily replace \& with & for splitting
            normalized = cleaned.replace(r"\&", "&")

            if "&" not in normalized:
                return []

            parts = [self._convert_markdown(p.strip(" \\")) for p in normalized.split("&")]
            if col_count is None:
                col_count = len(parts)
                if col_count < 2:
                    return []
            elif len(parts) != col_count:
                return []

            rows.append([re.sub(r"\s+", " ", p).strip() for p in parts])

        return rows if rows and len(rows) >= 2 else []

    def _render_table(self, rows: List[List[str]]) -> str:
        """
        FIX PROTOCOL #2: Render proper LaTeX tables using booktabs.
        CRITICAL: Sanitize cells but DON'T escape ampersands (they're table delimiters).
        Now wraps in table environment with small font like user's example.
        """
        if not rows:
            return ""

        cols = len(rows[0])
        # Use mix of left/center alignment: first column left, data columns centered
        col_spec = "l" + " ".join(["c" for _ in range(cols - 1)])

        # Sanitize each cell (but don't escape ampersands - they're needed for table structure)
        def sanitize_table_cell(text: str) -> str:
            """Sanitize cell content without escaping ampersands."""
            sanitized = self._sanitize_bullet(text, escape_ampersand=False)
            # Shorten long text for table cells
            words = sanitized.split()
            if len(words) > 4:
                # Keep first 3 words for long descriptions
                sanitized = " ".join(words[:3]) + "..."
            return sanitized

        # Check if first row looks like numbered items (Mystery 1, Test 1, etc.)
        # If so, generate generic column headers
        first_cell = rows[0][0].strip() if rows and rows[0] else ""
        looks_like_numbered_data = re.match(r'(Mystery|Test|Item|Row|Case)\s+\d+', first_cell, re.IGNORECASE)

        if looks_like_numbered_data:
            # Generate generic headers based on column count
            if cols == 5:
                # Common pattern: Variant, Accuracy, Improvement1, Improvement2, Description
                header = [r"\textbf{Variant}", r"\textbf{Acc}", r"\textbf{Gain 1}", r"\textbf{Gain 2}", r"\textbf{Description}"]
            elif cols == 4:
                header = [r"\textbf{Item}", r"\textbf{Value 1}", r"\textbf{Value 2}", r"\textbf{Notes}"]
            elif cols == 3:
                header = [r"\textbf{Item}", r"\textbf{Value}", r"\textbf{Notes}"]
            else:
                # Generic headers
                header = [r"\textbf{Col " + str(i+1) + "}" for i in range(cols)]

            # All rows are data rows
            data_rows = [[sanitize_table_cell(cell) for cell in row] for row in rows]
        else:
            # First row is header
            header = [f"\\textbf{{{sanitize_table_cell(cell)}}}" for cell in rows[0]]
            data_rows = [[sanitize_table_cell(cell) for cell in row] for row in rows[1:]]

        header_line = " & ".join(header)
        body_lines = [" & ".join(row) + " \\\\" for row in data_rows]

        # Wrap in table environment with smaller font (like user's example)
        return (
            "\\scriptsize\n"
            "  \\begin{table}\n"
            "    \\centering\n"
            f"    \\begin{{tabular}}{{{col_spec}}}\n"
            "      \\toprule\n"
            f"      {header_line} \\\\\n"
            "      \\midrule\n"
            "      " + "\n      ".join(body_lines) + "\n"
            "      \\bottomrule\n"
            "    \\end{tabular}\n"
            "  \\end{table}\n"
        )

    def _sanitize_title(self, title: str, max_words: int = 6) -> tuple[str, str]:
        """
        Enforce SHORT TITLE LAW: cap at 6 words maximum.
        Also removes citations and internal refs from titles.

        Returns (short_title, full_description) where:
        - short_title: Clean, complete phrase (max 6 words)
        - full_description: Full sentence for body if needed
        """
        # First sanitize to remove citations and refs
        title = re.sub(r'\\cite[pt]?\{[^}]+\}', '', title)
        title = re.sub(r'\\[Cc]?ref\{[^}]+\}', '', title)
        title = re.sub(r'\\label\{[^}]+\}', '', title)

        # Remove manual line breaks
        title = re.sub(r"\\\\(?![a-zA-Z])", " ", title)

        # CRITICAL FIX: Remove LaTeX formatting commands (textbf, textit, etc.)
        # These can break when title is truncated mid-command
        title = re.sub(r'\\textbf\{([^}]+)\}', r'\1', title)
        title = re.sub(r'\\textit\{([^}]+)\}', r'\1', title)
        title = re.sub(r'\\emph\{([^}]+)\}', r'\1', title)
        title = re.sub(r'\\texttt\{([^}]+)\}', r'\1', title)

        # Normalize whitespace
        title = re.sub(r'\s+', ' ', title).strip()

        words = title.split()

        # If already short enough, return as-is
        if len(words) <= max_words:
            return title.strip(), ""

        # CAPTION SANITIZATION: Extract a clean short title
        # If title starts with descriptive patterns, extract the subject
        short_title = self._extract_short_title(title, max_words)

        # Return short title + full description for body
        return short_title, title

    def _extract_short_title(self, title: str, max_words: int = 6) -> str:
        """
        Extract a SHORT, meaningful title from a long caption/title.
        Handles common figure caption patterns.
        """
        # Common caption patterns to simplify
        patterns = [
            (r'^(Layer-wise|Cross-[Mm]odel|[Mm]ulti-[Ll]ayer)\s+(\w+)', r'\1 \2'),  # "Layer-wise PCA" -> keep
            (r'^(\w+)\s+with\s+.*', r'\1 Analysis'),  # "Similarities with..." -> "Similarities Analysis"
            (r'^(\w+)\s+of\s+(\w+)\s+.*', r'\1 of \2'),  # "Analysis of model..." -> "Analysis of model"
            (r'^(\w+)\s+shows?\s+.*', r'\1 Results'),  # "Figure shows..." -> "Figure Results"
            (r'^(\w+\s+\w+)\s+from\s+.*', r'\1'),  # "Action representations from..." -> "Action representations"
        ]

        for pattern, replacement in patterns:
            match = re.match(pattern, title, re.IGNORECASE)
            if match:
                short = re.sub(pattern, replacement, title, flags=re.IGNORECASE)
                words = short.split()
                if len(words) <= max_words:
                    return short.strip()

        # Fallback: Take first max_words that form a noun phrase
        # Avoid breaking mid-phrase by finding last noun/adjective
        words = title.split()
        if len(words) > max_words:
            # Try to end at a natural boundary (before prepositions)
            prepositions = {'from', 'with', 'across', 'under', 'over', 'during', 'at', 'in', 'on'}
            for i in range(min(max_words, len(words)), 0, -1):
                if i < len(words) and words[i].lower() in prepositions:
                    return " ".join(words[:i]).strip()
            # Just take first max_words
            return " ".join(words[:max_words]).strip()

        return title.strip()

    def _chunk_bullets(self, bullets: List[str], chunk_size: int) -> List[List[str]]:
        return [bullets[i:i+chunk_size] for i in range(0, len(bullets), chunk_size)] or [[]]

    def _frame_with_bullets(self, title: str, bullets: List[str]) -> str:
        self.slide_count += 1
        clean_title, full_description = self._sanitize_title(title)
        final_bullets = bullets.copy()

        # CAPTION SANITIZATION: If we have a full description different from title,
        # add it as first bullet (but don't duplicate if it's already in bullets)
        if full_description and full_description != clean_title:
            # Only add if first bullet doesn't already contain this info
            if not final_bullets or full_description not in final_bullets[0]:
                final_bullets.insert(0, full_description)

        # CRITICAL: Check for tables BEFORE sanitizing bullets
        table_rows = self._extract_table_rows(final_bullets)
        if table_rows:
            table_block = self._render_table(table_rows)
            return f"""\n\\begin{{frame}}
        \\frametitle{{{clean_title}}}

    {table_block}

    \\end{{frame}}
    """

        # Not a table - sanitize bullets normally (with ampersand escaping)
        items = "\n".join([f"  \\item {self._sanitize_bullet(b)}" for b in final_bullets if self._sanitize_bullet(b)])
        return f"""\n\\begin{{frame}}
        \\frametitle{{{clean_title}}}

    \\begin{{itemize}}
    {items}
    \\end{{itemize}}

    \\end{{frame}}
    """

    def _frame_with_figure(self, title: str, image_path: str, bullets: List[str]) -> str:
        self.slide_count += 1

        # First clean the raw title
        title = re.sub(r'\\cite[pt]?\{[^}]+\}', '', title)
        title = re.sub(r'\\[Cc]?ref\{[^}]+\}', '', title)
        title = re.sub(r'\\label\{[^}]+\}', '', title)
        title = re.sub(r'\s+', ' ', title).strip()

        # Apply SHORT TITLE LAW
        clean_title, full_description = self._sanitize_title(title)
        final_bullets = bullets.copy()

        resolved_image = self._resolve_image_path(image_path)

        # NO GHOST COLUMNS RULE: Only use columns if image exists
        # Check if resolved path exists or is likely to exist
        image_exists = bool(resolved_image and (
            Path(resolved_image).exists() or
            'figures/' in resolved_image or
            resolved_image.endswith(('.pdf', '.png', '.jpg', '.jpeg'))
        ))

        if not image_exists:
            # Fall back to full-width itemize (no ghost columns)
            # In this case, we CAN add full description since we have full width
            if full_description and full_description != clean_title:
                if not final_bullets or full_description not in final_bullets[0]:
                    final_bullets.insert(0, full_description)

            items = "\n".join([f"  \\item {self._sanitize_bullet(b)}" for b in final_bullets if self._sanitize_bullet(b)])
            return f"""\n\\begin{{frame}}
        \\frametitle{{{clean_title}}}

    \\begin{{itemize}}
    {items}
    \\end{{itemize}}

    \\end{{frame}}
    """

        # Image exists - use columns layout
        # CRITICAL GENERAL FIX: For column layouts, filter out overly long bullets
        # Narrow columns (0.4 textwidth) can't handle walls of text in ANY paper
        # General rule: keep bullets under 100 words or 500 chars for column layouts
        def is_bullet_too_long(bullet: str) -> bool:
            """Check if bullet is too long for narrow column layout"""
            word_count = len(bullet.split())
            char_count = len(bullet)
            return word_count > 100 or char_count > 500

        # DON'T add full_description if it's too long for column layout
        # Only add if it's concise enough to fit in narrow column
        if full_description and full_description != clean_title:
            if not is_bullet_too_long(full_description):
                if not final_bullets or full_description not in final_bullets[0]:
                    final_bullets.insert(0, full_description)

        # Filter out any overly long bullets from the list
        final_bullets = [b for b in final_bullets if not is_bullet_too_long(b)]

        # Limit to max 3 bullets for column layouts to avoid overcrowding
        final_bullets = final_bullets[:3]

        table_rows = self._extract_table_rows(final_bullets)
        if table_rows:
            table_block = self._render_table(table_rows)
            return f"""\n\\begin{{frame}}
        \\frametitle{{{clean_title}}}
    \\begin{{columns}}
      \\begin{{column}}{{0.55\\textwidth}}
        \\centering
        \\includegraphics[width=\\linewidth]{{{resolved_image}}}
      \\end{{column}}
      \\begin{{column}}{{0.4\\textwidth}}
        {table_block}
      \\end{{column}}
    \\end{{columns}}
    \\end{{frame}}
    """

        items = "\n".join([f"  \\item {self._sanitize_bullet(b)}" for b in final_bullets if self._sanitize_bullet(b)])
        return f"""\n\\begin{{frame}}
        \\frametitle{{{clean_title}}}
    \\begin{{columns}}
      \\begin{{column}}{{0.55\\textwidth}}
        \\centering
        \\includegraphics[width=\\linewidth]{{{resolved_image}}}
      \\end{{column}}
      \\begin{{column}}{{0.4\\textwidth}}
        \\begin{{itemize}}
    {items}
        \\end{{itemize}}
      \\end{{column}}
    \\end{{columns}}
    \\end{{frame}}
    """

    def _frame_with_equation(self, title: str, equation: str, bullets: List[str]) -> str:
        self.slide_count += 1
        clean_title, full_description = self._sanitize_title(title)
        final_bullets = bullets.copy()

        # CAPTION SANITIZATION: Add full description if different
        if full_description and full_description != clean_title:
            if not final_bullets or full_description not in final_bullets[0]:
                final_bullets.insert(0, full_description)

        table_rows = self._extract_table_rows(final_bullets)
        if "\\begin" in equation:
            eq_block = equation
        else:
            eq_block = f"\\begin{{align*}}\n{equation}\n\\end{{align*}}"

        if table_rows:
            table_block = self._render_table(table_rows)
            return f"""\n\\begin{{frame}}
        \\frametitle{{{clean_title}}}

    {eq_block}

    {table_block}
    \\end{{frame}}
    """

        items = "\n".join([f"  \\item {self._sanitize_bullet(b)}" for b in final_bullets if self._sanitize_bullet(b)])
        return f"""\n\\begin{{frame}}
        \\frametitle{{{clean_title}}}

    {eq_block}

    \\begin{{itemize}}
    {items}
    \\end{{itemize}}
    \\end{{frame}}
    """
    
    def _generate_section_slide(self, node: TexNode) -> str:
        """Generate a section slide"""
        self.slide_count += 1
        
        slide = f"""\n\\begin{{frame}}
\\frametitle{{{node.content}}}

"""
        
        # Add children as bullet points or subsection titles
        if node.children:
            slide += "\\begin{itemize}\n"
            for child in node.children:
                if child.type == 'subsection':
                    slide += f"  \\item \\textbf{{{child.content}}}\n"
                elif child.type == 'text':
                    slide += f"  \\item {child.content}\n"
            slide += "\\end{itemize}\n"
        
        slide += "\n\\end{frame}\n"
        return slide
    
    def _generate_subsection_content(self, node: TexNode) -> str:
        """Generate content for a subsection"""
        # Subsections typically become the focus of slides
        output = f"\n\\section{{{node.content}}}\n"
        
        for child in node.children:
            output += self._generate_slide_from_node(child, depth=1)
        
        return output
    
    def _generate_equation_slide(self, node: TexNode) -> str:
        """Generate a slide highlighting an equation"""
        self.slide_count += 1
        
        return f"""\n\\begin{{frame}}
\\frametitle{{Key Formula}}

{node.content}

\\end{{frame}}
"""
    
    def _generate_text_bullet(self, node: TexNode) -> str:
        """Generate a bullet point"""
        return f"  \\item {node.content}\n"
    
    def _generate_citation_note(self, node: TexNode) -> str:
        """Generate a citation reference"""
        return f"\\cite{{{node.content}}} "
    
    def get_statistics(self) -> Dict[str, int]:
        """Return generation statistics"""
        return {
            'slides_generated': self.slide_count,
        }


# Example usage
if __name__ == "__main__":
    from tex_parser import TexNode
    
    # Create sample nodes
    intro_node = TexNode(
        type='section',
        content='Introduction',
        level=0
    )
    intro_node.children = [
        TexNode(type='text', content='Problem statement'),
        TexNode(type='text', content='Motivation'),
    ]
    
    # Generate Beamer code
    generator = BeamerGenerator(
        title="Research Paper Presentation",
        author="John Researcher",
        institute="University"
    )
    
    beamer_code = generator.generate([intro_node])
    print("Generated Beamer LaTeX:")
    print(beamer_code)
    print(f"\nStats: {generator.get_statistics()}")
