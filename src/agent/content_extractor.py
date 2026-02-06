"""
LLM Content Extractor with Multimodal Support
==============================================

Uses a chat LLM (Gemini or NVIDIA DeepSeek) to:
- Read structured TeX nodes
- Analyze figures, tables, and equations (MULTIMODAL)
- Build an outline understanding
- Produce a presentation plan aligned with a user prompt (short vs. long)
"""

from __future__ import annotations

from typing import List, Optional
from pathlib import Path

from .tex_parser import TexNode


DEFAULT_SYSTEM_PROMPT = (
    "You are a professional presentation planner. Given structured TeX sections, build a clear,"
    " accurate outline for slides. Be concise, avoid hallucinating, and keep equations"
    " or claims only if present in the input.\n\n"
    "CRITICAL RULES:\n"
    "1. THE NO-BORE RULE: Apply section weighting hierarchy:\n"
    "   - HIGH PRIORITY (Detailed, 2-3 slides, 5-6 bullets each): Methodology, Novel Algorithms, Main Experimental Results\n"
    "   - LOW PRIORITY (Brief, 1 slide max, 3-4 bullets total): Introduction, Background, Related Work\n"
    "   - IGNORE: References, Appendices, Acknowledgements\n"
    "2. THE ONE SLIDE, ONE CLAIM RULE: If a section is very long, split it into specific insights.\n"
    "   Example: Split 'Experiments' into 'Accuracy Results' and 'Ablation Studies' as separate slides.\n"
    "3. NEVER use conversational filler like 'Here is the presentation' or 'Slide 1: Title'.\n"
    "4. NEVER create an 'Overview' that just lists slide numbers. Focus on key contributions only."
)


class ContentExtractor:
    def __init__(self, client, model: str, system_prompt: str | None = None) -> None:
        self.client = client
        self.model = model
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT

        # Detect if client supports multimodal (NVIDIA has encode_image method)
        self.supports_multimodal = hasattr(client, 'encode_image')

    def generate_slide_bullets_with_image(
        self,
        section_content: str,
        section_title: str,
        image_path: Optional[str | Path] = None,
        max_bullets: int = 5
    ) -> List[str]:
        """
        Use LLM to generate intelligent bullets with MULTIMODAL image analysis.

        Args:
            section_content: Raw text from the section
            section_title: Title of the section
            image_path: Optional path to figure/chart to analyze
            max_bullets: Maximum number of bullets to generate

        Returns:
            List of intelligently summarized bullet points (with image insights)
        """
        # If no image or client doesn't support multimodal, fall back to text-only
        if not image_path or not self.supports_multimodal:
            return self.generate_slide_bullets(section_content, section_title, max_bullets)

        image_path = Path(image_path)
        if not image_path.exists():
            return self.generate_slide_bullets(section_content, section_title, max_bullets)

        # MULTIMODAL: Include image in the analysis
        prompt_text = f"""Section: {section_title}

Text content:
{section_content[:1500]}

Task: Analyze the provided image/figure and create {max_bullets} concise, informative bullet points for a presentation slide.

Rules:
1. INTEGRATE insights from BOTH the text and the image
2. Each bullet should be 1-2 sentences maximum
3. Focus on KEY INSIGHTS from the figure (trends, comparisons, key results)
4. Make bullets ACTIONABLE and SPECIFIC
5. Prioritize numbers, results, and concrete findings shown in the image

Output format: One bullet per line, starting with "-"
"""

        try:
            # Use multimodal chat (NVIDIA DeepSeek supports this)
            response = self.client.chat_with_image(
                model=self.model,
                text=prompt_text,
                image_path=image_path,
                system_prompt="You are an expert at analyzing research figures and distilling insights into presentation-ready bullet points.",
                max_tokens=500,
                temperature=0.3
            )

            # Parse response into list
            bullets = [
                line.strip().lstrip('-').lstrip('•').strip()
                for line in response.split('\n')
                if line.strip() and (line.strip().startswith('-') or line.strip().startswith('•'))
            ]

            return bullets[:max_bullets] if bullets else self.generate_slide_bullets(section_content, section_title, max_bullets)

        except Exception as e:
            print(f"⚠️  Multimodal generation failed: {e}")
            # Fallback to text-only
            return self.generate_slide_bullets(section_content, section_title, max_bullets)

    def generate_slide_bullets(self, section_content: str, section_title: str, max_bullets: int = 5) -> List[str]:
        """
        Use LLM to generate intelligent, concise bullets for a single slide.

        Args:
            section_content: Raw text from the section
            section_title: Title of the section
            max_bullets: Maximum number of bullets to generate

        Returns:
            List of intelligently summarized bullet points
        """
        prompt = f"""Section: {section_title}

Content:
{section_content[:2000]}

Task: Create {max_bullets} concise, informative bullet points for a presentation slide.

Rules:
1. Each bullet should be 1-2 sentences maximum
2. Focus on KEY INSIGHTS, not just facts
3. Make bullets ACTIONABLE and SPECIFIC
4. Avoid generic statements
5. Prioritize numbers, results, and concrete findings

Output format: One bullet per line, starting with "-"
"""

        messages = [
            {"role": "system", "content": "You are an expert at distilling research into presentation-ready bullet points."},
            {"role": "user", "content": prompt}
        ]

        response = self.client.chat(
            model=self.model,
            messages=messages,
            max_tokens=400,
            temperature=0.3
        )

        # Parse response into list
        bullets = [
            line.strip().lstrip('-').lstrip('•').strip()
            for line in response.split('\n')
            if line.strip() and (line.strip().startswith('-') or line.strip().startswith('•'))
        ]

        return bullets[:max_bullets]

    def determine_slide_count(self, nodes: List[TexNode], user_prompt: str = "") -> int:
        """
        Use LLM to intelligently determine optimal slide count based on content.

        Returns: Recommended slide count (5-100)
        """
        outline = self._nodes_to_outline(nodes)[:3000]  # Limit for token efficiency

        prompt = f"""Paper structure:
{outline}

User request: {user_prompt or "Standard research presentation"}

Task: Determine the OPTIMAL number of slides for this presentation.

Consider:
- Content density (more complex = more slides)
- Number of figures/tables/equations
- Key contributions (each needs proper explanation)
- Balance between detail and brevity

Provide ONLY a number between 5 and 100. No explanation.
"""

        messages = [
            {"role": "system", "content": "You are an expert presentation planner."},
            {"role": "user", "content": prompt}
        ]

        response = self.client.chat(
            model=self.model,
            messages=messages,
            max_tokens=10,
            temperature=0.2
        )

        # Extract number from response
        import re
        match = re.search(r'\d+', response)
        if match:
            count = int(match.group())
            return max(5, min(100, count))  # Clamp to 5-100

        # Fallback: estimate based on content
        section_count = sum(1 for n in nodes if n.type == 'section')
        return max(10, min(50, section_count * 2))

    def summarize(self, nodes: List[TexNode], user_prompt: str = "", max_tokens: int = 900) -> str:
        """
        Summarize the paper into a slide-oriented outline using intelligent section weighting.
        Returns a markdown-like string (safe to render on a slide).

        Implements:
        - NO-BORE RULE: Prioritize methodology/experiments, minimize intro/background
        - BLOCKSWORLD CONSTRAINT: If document > 10k chars, use Executive Summary Mode
        - ONE SLIDE, ONE CLAIM: Split large sections into focused insights
        """
        outline_text = self._nodes_to_outline(nodes)

        # BLOCKSWORLD CONSTRAINT: If document exceeds 10,000 characters, switch to Executive Summary Mode
        if len(outline_text) > 10000:
            return self._executive_summary_mode(nodes, user_prompt, max_tokens)

        # Apply section weighting analysis
        weighted_text = self._apply_section_weighting(outline_text)

        user_instructions = (
            user_prompt.strip()
            if user_prompt.strip()
            else "Create a slide-friendly outline following the NO-BORE rule: detailed coverage of methodology and experiments, brief intro/background."
        )

        content = (
            "Document outline (from TeX parser) with section priorities:\n"
            f"{weighted_text}\n\n"
            "Presentation request from user (style/length):\n"
            f"{user_instructions}\n\n"
            "Produce concise bullet points. Favor factual, grounded statements."
            " Focus on high-priority sections (Methodology, Algorithms, Experiments)."
            " Keep low-priority sections (Intro, Background, Related Work) minimal."
            " If unsure, say 'unspecified'."
        )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": content},
        ]

        return self.client.chat(model=self.model, messages=messages, max_tokens=max_tokens, temperature=0.4)

    def _executive_summary_mode(self, nodes: List[TexNode], user_prompt: str, max_tokens: int) -> str:
        """
        BLOCKSWORLD CONSTRAINT: When document > 10k chars, use Executive Summary Mode.
        Identify top 3 contributions and build presentation around proving those 3 points.
        """
        # Extract key sections only
        key_sections = self._extract_key_sections(nodes)

        content = (
            "EXECUTIVE SUMMARY MODE (Large document detected):\n\n"
            f"Key sections from paper:\n{key_sections}\n\n"
            "Your task:\n"
            "1. Identify the TOP 3 CONTRIBUTIONS of this paper\n"
            "2. Build the entire presentation around PROVING these 3 points\n"
            "3. Discard all minor details that do not support these 3 points\n"
            "4. Keep it focused and impactful\n\n"
            f"User style request: {user_prompt or 'Concise, focused presentation'}\n\n"
            "Output format: List the 3 contributions as clear bullet points, then suggest how to prove each one."
        )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": content},
        ]

        return self.client.chat(model=self.model, messages=messages, max_tokens=max_tokens, temperature=0.4)

    def _extract_key_sections(self, nodes: List[TexNode]) -> str:
        """Extract only high-priority sections for executive summary mode."""
        lines: list[str] = []

        # Priority keywords for section identification
        high_priority_keywords = [
            'method', 'algorithm', 'approach', 'experiment', 'result', 'evaluation',
            'technique', 'model', 'architecture', 'analysis', 'finding', 'contribution'
        ]

        def is_high_priority(content: str) -> bool:
            content_lower = content.lower()
            return any(keyword in content_lower for keyword in high_priority_keywords)

        def walk_key_sections(node: TexNode, depth: int = 0) -> None:
            if node.type == 'section' and is_high_priority(node.content):
                indent = "  " * depth
                lines.append(f"{indent}- section: {node.content.strip()}")
                # Include immediate children of high-priority sections
                for child in node.children[:5]:  # Limit to first 5 children
                    child_indent = "  " * (depth + 1)
                    lines.append(f"{child_indent}- {child.type}: {child.content.strip()[:100]}")

        for n in nodes:
            walk_key_sections(n, depth=0)

        return "\n".join(lines) if lines else self._nodes_to_outline(nodes)[:3000]

    def _apply_section_weighting(self, outline_text: str) -> str:
        """
        Apply NO-BORE RULE section weighting to mark priority levels.
        """
        lines = outline_text.split('\n')
        weighted_lines: list[str] = []

        # Define section priority patterns
        high_priority_patterns = [
            'method', 'algorithm', 'approach', 'experiment', 'result', 'evaluation',
            'technique', 'model', 'architecture', 'analysis', 'finding', 'ablation',
            'implementation', 'evaluation', 'performance'
        ]

        low_priority_patterns = [
            'introduction', 'background', 'related work', 'prior work', 'motivation',
            'preliminaries'
        ]

        ignore_patterns = [
            'reference', 'appendix', 'acknowledgement', 'supplementary'
        ]

        for line in lines:
            line_lower = line.lower()

            # Check if should be ignored
            if any(pattern in line_lower for pattern in ignore_patterns):
                continue  # Skip these sections entirely

            # Mark priority levels
            if any(pattern in line_lower for pattern in high_priority_patterns):
                weighted_lines.append(f"[HIGH PRIORITY] {line}")
            elif any(pattern in line_lower for pattern in low_priority_patterns):
                weighted_lines.append(f"[LOW PRIORITY - BRIEF] {line}")
            else:
                weighted_lines.append(line)

        return "\n".join(weighted_lines)

    def _nodes_to_outline(self, nodes: List[TexNode]) -> str:
        """Convert parsed nodes to a compact outline string for the LLM."""
        lines: list[str] = []

        def walk(node: TexNode, depth: int = 0) -> None:
            indent = "  " * depth
            prefix = "- " if node.type in {"section", "subsection", "text"} else "* "
            lines.append(f"{indent}{prefix}{node.type}: {node.content.strip()}")
            for child in node.children:
                walk(child, depth + 1)

        for n in nodes:
            walk(n, depth=0)

        return "\n".join(lines)
