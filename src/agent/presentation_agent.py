"""
Presentation Agent Orchestrator
================================

Main pipeline that coordinates:
1. TeX Cleaning (handle macros, comments, environments)
2. Content Parsing (extract structure)
3. LLM Analysis (optional - understand topics)
4. Beamer Generation (create slides)

This is the highest-level interface users interact with.
"""

from pathlib import Path
from typing import Optional, Dict
import json

from .tex_cleaner import TexCleaner
from .tex_parser import TexParser, TexNode
from .beamer_generator import BeamerGenerator
from .content_extractor import ContentExtractor
from .config import load_settings
from .hf_client import HuggingFaceClient
from .gemini_client import GeminiClient
from .nvidia_client import NvidiaClient


class PresentationAgent:
    """
    Main agent for converting research papers to presentations.
    
    Usage:
        agent = PresentationAgent()
        
        # 1. Load paper
        agent.load_tex_file("paper.tex")
        
        # 2. Set presentation parameters
        agent.set_presentation_params(
            title="My Paper Title",
            author="Author Name",
            style_prompt="Make it concise with 1-2 slides per section"
        )
        
        # 3. Generate presentation
        beamer_code = agent.generate_presentation()
        agent.save_presentation("output.tex")
    """
    
    def __init__(self):
        self.raw_tex = None
        self.cleaned_tex = None
        self.parsed_nodes = None
        self.beamer_code = None
        self.llm_summary: Optional[str] = None
        self.paper_root: Optional[Path] = None
        
        self.title = "Presentation"
        self.author = "Unknown"
        self.institute = ""
        self.style_prompt = ""
        
        self.cleaner = TexCleaner()
        self.parser = TexParser()
        self.generator = None
        self.hf_client: Optional[HuggingFaceClient] = None
        self.hf_model: Optional[str] = None
        self.hf_system_prompt: Optional[str] = None
        self.gemini_client: Optional[GeminiClient] = None
        self.gemini_model: Optional[str] = None
        self.nvidia_client: Optional[NvidiaClient] = None
        self.nvidia_model: Optional[str] = None
        self.llm_client = None  # Unified client reference
        self.llm_model: Optional[str] = None  # Unified model reference

        self.pipeline_log = []
    
    def load_tex_file(self, filepath: str) -> None:
        """Load TeX file from disk"""
        self.log(f"Loading TeX file: {filepath}")
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        self.raw_tex = path.read_text()
        self.paper_root = path.parent
        self.log(f"Loaded {len(self.raw_tex)} characters")

    def load_tex_from_folder(self, folder_path: str, main_filename: Optional[str] = None) -> None:
        """Load TeX by pointing at a folder; picks the main .tex file automatically."""
        folder = Path(folder_path)
        if not folder.is_dir():
            raise NotADirectoryError(f"Folder not found: {folder_path}")

        candidate: Optional[Path] = None

        if main_filename:
            candidate = folder / main_filename
            if not candidate.exists():
                raise FileNotFoundError(f"Main TeX not found: {candidate}")
        else:
            tex_files = list(folder.rglob("*.tex"))
            if not tex_files:
                raise FileNotFoundError(f"No .tex files found under: {folder_path}")

            def has_documentclass(path: Path) -> bool:
                try:
                    snippet = path.read_text(encoding="utf-8", errors="ignore")[:5000]
                except Exception:
                    return False
                return "\\documentclass" in snippet

            doc_files = [p for p in tex_files if has_documentclass(p)]
            candidate = doc_files[0] if doc_files else tex_files[0]

        self.paper_root = folder
        self.load_tex_file(str(candidate))
    
    def load_tex_string(self, tex_content: str) -> None:
        """Load TeX from string"""
        self.raw_tex = tex_content
        self.log(f"Loaded TeX from string: {len(self.raw_tex)} characters")
    
    def set_presentation_params(
        self,
        title: str,
        author: str,
        institute: str = "",
        style_prompt: str = ""
    ) -> None:
        """
        Set presentation metadata and styling.
        
        Args:
            title: Presentation title
            author: Author name
            institute: Institution name
            style_prompt: User instructions for presentation style
                Example: "Create 2-3 slides per section. Emphasize figures."
        """
        self.title = title
        self.author = author
        self.institute = institute
        self.style_prompt = style_prompt
        
        self.log(f"Set presentation params: {title} by {author}")
        if style_prompt:
            self.log(f"Style prompt: {style_prompt}")
    
    def process_pipeline(self) -> None:
        """
        Run the entire pipeline:
        1. Clean TeX
        2. Parse content
        3. (Future: LLM analysis)
        4. Generate Beamer
        """
        if self.raw_tex is None:
            raise ValueError("No TeX content loaded. Call load_tex_file() first.")
        
        # Step 1: Clean TeX
        self.log("\n=== STEP 1: CLEANING TEX ===")
        self._step_clean()
        
        # Step 2: Parse content
        self.log("\n=== STEP 2: PARSING CONTENT ===")
        self._step_parse()
        
        # Step 3: LLM understanding (optional but recommended)
        self.log("\n=== STEP 3: LLM UNDERSTANDING ===")
        self._step_understand()

        # Step 3: Generate Beamer (future: could add LLM here)
        self.log("\n=== STEP 4: GENERATING BEAMER ===")
        self._step_generate()
        
        self.log("\n=== PIPELINE COMPLETE ===")
    
    def _step_clean(self) -> None:
        """Execute cleaning step"""
        self.cleaned_tex = self.cleaner.clean(self.raw_tex)
        
        stats = self.cleaner.get_statistics()
        self.log(f"Macros found: {stats['macros_found']}")
        self.log(f"Custom environments: {stats['custom_environments']}")
        self.log(f"Cleaned content length: {len(self.cleaned_tex)} chars")
        
        # Show what macros were found
        if self.cleaner.macros:
            self.log("Macros extracted:")
            for name, defn in self.cleaner.macros.items():
                self.log(f"  \\{name} → {defn.body[:50]}")
    
    def _step_parse(self) -> None:
        """Execute parsing step"""
        self.parsed_nodes = self.parser.parse(self.cleaned_tex)
        
        self.log(f"Top-level nodes found: {len(self.parsed_nodes)}")
        
        # Log structure
        for i, node in enumerate(self.parsed_nodes):
            self.log(f"  [{i}] {node.type}: {node.content[:50]}")
            for child in node.children[:3]:  # Show first 3 children
                self.log(f"      ↳ {child.type}: {child.content[:40]}")

    def _ensure_llm_client(self) -> bool:
        """Ensure LLM client is available; return True if ready. Supports NVIDIA (primary), Gemini, HF."""
        # If already set
        if self.llm_client and self.llm_model:
            return True

        try:
            settings = load_settings()
        except Exception as exc:  # noqa: BLE001
            self.log(f"LLM disabled (missing config): {exc}")
            return False

        # PRIMARY: NVIDIA DeepSeek-V3.2
        if settings.llm_provider == "nvidia":
            self.nvidia_client = NvidiaClient(
                settings.nvidia_api_key,  # type: ignore[arg-type]
                base_url=settings.nvidia_base_url,
            )
            self.nvidia_model = settings.nvidia_model
            self.llm_client = self.nvidia_client
            self.llm_model = self.nvidia_model
            self.hf_system_prompt = settings.system_prompt
            self.log(f"🧠 LLM enabled with NVIDIA model: {self.nvidia_model}")
            return True

        # FALLBACK 1: Gemini
        elif settings.llm_provider == "gemini":
            self.gemini_client = GeminiClient(settings.gemini_api_key)  # type: ignore[arg-type]
            self.gemini_model = settings.gemini_model
            self.llm_client = self.gemini_client
            self.llm_model = self.gemini_model
            self.hf_system_prompt = settings.system_prompt
            self.log(f"LLM enabled with Gemini model: {self.gemini_model}")
            return True

        # FALLBACK 2: HuggingFace
        elif settings.llm_provider == "hf":
            self.log("HuggingFace provider not yet supported in this version")
            return False

        else:
            self.log(f"Unsupported LLM provider: {settings.llm_provider}")
            return False

    def _step_understand(self) -> None:
        """Use LLM to build a presentation outline/summary."""
        if not self.parsed_nodes:
            self.log("Skipping LLM understanding (no parsed nodes).")
            return

        if not self._ensure_llm_client():
            self.log("Skipping LLM understanding (LLM client unavailable).")
            return

        # Use unified client/model references
        client = self.llm_client
        model = self.llm_model
        system_prompt = self.hf_system_prompt

        if not client or not model:
            self.log("Skipping LLM understanding (client/model missing).")
            return

        extractor = ContentExtractor(
            client=client,
            model=model,
            system_prompt=system_prompt,
        )

        try:
            self.llm_summary = extractor.summarize(self.parsed_nodes, self.style_prompt)
            self.log("LLM summary generated (showing first lines):")
            preview_lines = (self.llm_summary or "").split("\n")[:4]
            for line in preview_lines:
                self.log(f"  {line}")
        except Exception as exc:  # noqa: BLE001
            self.llm_summary = None
            self.log(f"LLM understanding failed: {exc}")

    def _collect_section_assets(self):
        assets = []
        if not self.parsed_nodes:
            return assets
        for node in self.parsed_nodes:
            if node.type != 'section':
                continue
            image_path = None
            core_equation = None
            for child in node.children:
                if child.type == 'figure' and not image_path:
                    image_path = child.meta.get('image_path') if child.meta else None
                if child.type == 'equation' and not core_equation:
                    core_equation = child.meta.get('core_equation') if child.meta else child.content
            assets.append({
                'section': node.content,
                'image_path': image_path,
                'core_equation': core_equation,
            })
        return assets
    
    def _step_generate(self) -> None:
        """Execute Beamer generation step with LLM as primary content brain"""

        # Default max slides (fallback if LLM not available)
        max_slides = self._extract_max_slides_from_prompt(self.style_prompt)
        extractor = None

        # PRIMARY PATH: Use LLM as the main brain for content generation
        if self._ensure_llm_client():
            client = self.llm_client
            model = self.llm_model
            system_prompt = self.hf_system_prompt

            if client and model:
                self.log("🧠 LLM mode: Using intelligent content generation (primary method)")

                extractor = ContentExtractor(
                    client=client,
                    model=model,
                    system_prompt=system_prompt,
                )

                try:
                    # LLM determines optimal slide count dynamically (5-100)
                    llm_slide_count = extractor.determine_slide_count(
                        self.parsed_nodes,
                        self.style_prompt
                    )
                    self.log(f"✓ LLM determined optimal slide count: {llm_slide_count}")
                    max_slides = llm_slide_count
                except Exception as e:
                    self.log(f"⚠️  LLM slide count failed (API limit/error), using default: {max_slides} slides")
                    self.log(f"   Error: {e}")
        else:
            # FALLBACK PATH: No API key or client unavailable
            self.log("⚙️  Fallback mode: No LLM available (missing API key or offline)")
            self.log("   Using rule-based heuristics as backup")

        # Create generator with LLM as primary content brain
        self.generator = BeamerGenerator(
            title=self.title,
            author=self.author,
            institute=self.institute,
            figure_root=self.paper_root,
            max_slides=max_slides,
            content_extractor=extractor  # LLM brain (None = fallback to rules)
        )

        self.beamer_code = self.generator.generate(
            self.parsed_nodes,
            user_prompt=self.style_prompt,
            summary_content=self.llm_summary
        )

        stats = self.generator.get_statistics()
        self.log(f"Slides generated: {stats['slides_generated']}")
        self.log(f"Max slides allowed: {max_slides}")
        self.log(f"Beamer code length: {len(self.beamer_code)} chars")

        # collect section assets for report
        self.section_assets = self._collect_section_assets()

    def _extract_max_slides_from_prompt(self, style_prompt: str) -> int:
        """Extract max slides number from style prompt, default to 20."""
        import re

        # Look for patterns like "15-20 slides", "20 slides", "15 to 20 slides"
        patterns = [
            r'(\d+)\s*-\s*(\d+)\s*slides?',  # "15-20 slides"
            r'(\d+)\s+to\s+(\d+)\s*slides?',  # "15 to 20 slides"
            r'(\d+)\s*slides?',  # "20 slides"
        ]

        for pattern in patterns:
            match = re.search(pattern, style_prompt.lower())
            if match:
                if len(match.groups()) == 2:
                    # Range found, use upper bound
                    return int(match.group(2))
                else:
                    # Single number found
                    return int(match.group(1))

        # Default to 20 slides
        return 20
    
    def generate_presentation(self) -> str:
        """
        Run full pipeline and return Beamer code.
        
        Returns:
            LaTeX code for Beamer presentation
        """
        self.process_pipeline()
        return self.beamer_code
    
    def save_presentation(self, filepath: str) -> None:
        """Save Beamer code to file"""
        if self.beamer_code is None:
            raise ValueError("No presentation generated yet. Call process_pipeline() first.")
        
        path = Path(filepath)
        path.write_text(self.beamer_code)
        self.log(f"Saved presentation to: {filepath}")
    
    def save_report(self, filepath: str) -> None:
        """Save processing report"""
        report = {
            'title': self.title,
            'author': self.author,
            'input_size': len(self.raw_tex) if self.raw_tex else 0,
            'cleaned_size': len(self.cleaned_tex) if self.cleaned_tex else 0,
            'nodes_parsed': len(self.parsed_nodes) if self.parsed_nodes else 0,
            'slides_generated': self.generator.get_statistics()['slides_generated'] if self.generator else 0,
            'section_assets': getattr(self, 'section_assets', []),
            'pipeline_log': self.pipeline_log,
        }
        
        path = Path(filepath)
        path.write_text(json.dumps(report, indent=2))
        self.log(f"Saved report to: {filepath}")
    
    def log(self, message: str) -> None:
        """Log message"""
        print(message)
        self.pipeline_log.append(message)


# Example usage
if __name__ == "__main__":
    # Sample TeX content
    sample_paper = r"""
    \documentclass{article}
    
    \newcommand{\alg}{Stochastic Gradient Descent}
    \newcommand{\accuracy}{Classification Accuracy}
    
    \title{My Research Paper}
    \author{Jane Researcher}
    
    \begin{document}
    
    \section{Introduction}
    We study optimization. Our method uses \alg for training.
    
    % TODO: Update these numbers
    Previous work achieved 92% accuracy.
    Our method achieves 95% accuracy.
    
    \section{Methodology}
    Our approach is novel and efficient.
    
    \subsection{Algorithm}
    The algorithm is as follows:
    
    \begin{equation}
    x_{t+1} = x_t - \eta \nabla f(x_t)
    \end{equation}
    
    \section{Results}
    The \accuracy was measured on standard benchmarks.
    
    \end{document}
    """
    
    # Create and run agent
    agent = PresentationAgent()
    agent.load_tex_string(sample_paper)
    agent.set_presentation_params(
        title="My Research Paper",
        author="Jane Researcher",
        institute="University of Research",
        style_prompt="Make it concise, 2 slides per section"
    )
    
    # Generate presentation
    beamer_code = agent.generate_presentation()
    
    # Save outputs
    agent.save_presentation("output.tex")
    agent.save_report("report.json")
    
    print("\n" + "="*50)
    print("GENERATED BEAMER CODE (first 1000 chars):")
    print("="*50)
    print(beamer_code[:1000])
