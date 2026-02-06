"""
TeX Content Parser
==================

Extracts structured content from cleaned LaTeX:
- Sections and subsections
- Equations
- Citations
- Bullet points
- Figures

Creates a hierarchical structure ready for LLM analysis.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class TexNode:
    """Represents a node in the TeX document hierarchy"""
    type: str  # 'section', 'subsection', 'text', 'equation', 'figure', 'citation'
    content: str
    level: int = 0  # 0=section, 1=subsection, 2=subsubsection
    children: List['TexNode'] = None
    meta: Dict[str, str] | None = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.meta is None:
            self.meta = {}
    
    def to_dict(self):
        """Convert to dictionary for LLM processing"""
        return {
            'type': self.type,
            'content': self.content,
            'level': self.level,
            'children': [child.to_dict() for child in self.children]
        }


class TexParser:
    """
    Parses cleaned TeX content into structured format.
    
    Usage:
        parser = TexParser()
        nodes = parser.parse(cleaned_tex_content)
    """
    
    def __init__(self):
        self.root = None
        self.current_section_stack = []
    
    def parse(self, tex_content: str) -> List[TexNode]:
        """
        Parse TeX content into hierarchical structure.
        Returns list of top-level nodes.
        """
        lines = tex_content.split('\n')
        nodes = []
        current_parent = None
        idx = 0
        
        while idx < len(lines):
            raw_line = lines[idx]
            line = raw_line.strip()
            if not line:
                idx += 1
                continue
            
            # Detect section headers
            if line.startswith('\\section{'):
                title = self._extract_braces(line)
                node = TexNode(type='section', content=title, level=0)
                nodes.append(node)
                current_parent = node
            
            elif line.startswith('\\subsection{'):
                title = self._extract_braces(line)
                node = TexNode(type='subsection', content=title, level=1)
                if current_parent:
                    current_parent.children.append(node)
                    current_parent = node
                else:
                    nodes.append(node)
            
            # Detect equations
            elif '\\begin{equation' in line or '\\begin{align' in line:
                eq_content, end_idx = self._extract_equation_block(lines, idx)
                node = TexNode(
                    type='equation',
                    content=eq_content,
                    level=current_parent.level + 1 if current_parent else 0,
                    meta={'core_equation': eq_content}
                )
                if current_parent:
                    current_parent.children.append(node)
                else:
                    nodes.append(node)
                idx = end_idx + 1
                continue  # skip further processing of this block

            # Detect figure blocks
            elif '\\begin{figure' in line:
                fig_node, end_idx = self._extract_figure_block(lines, idx, current_parent)
                if fig_node:
                    if current_parent:
                        current_parent.children.append(fig_node)
                    else:
                        nodes.append(fig_node)
                idx = end_idx + 1
                continue
            
            # Detect citations
            elif '\\cite{' in line:
                citations = re.findall(r'\\cite\{([^}]+)\}', line)
                for citation in citations:
                    node = TexNode(type='citation', content=citation)
                    if current_parent:
                        current_parent.children.append(node)
                    else:
                        nodes.append(node)
            
            # Regular text
            elif not line.startswith('\\'):
                node = TexNode(
                    type='text',
                    content=line,
                    level=current_parent.level + 1 if current_parent else 0,
                )
                if current_parent:
                    current_parent.children.append(node)
                else:
                    nodes.append(node)

            idx += 1
        
        return nodes
    
    def _extract_braces(self, text: str) -> str:
        """Extract content between first { and matching }"""
        start = text.find('{')
        if start == -1:
            return text
        
        count = 0
        for i, char in enumerate(text[start:]):
            if char == '{':
                count += 1
            elif char == '}':
                count -= 1
                if count == 0:
                    return text[start+1:start+i]
        
        return text[start+1:]
    
    def _extract_equation_block(self, lines: list, start_idx: int) -> tuple[str, int]:
        """Extract equation block from lines; return content and end index"""
        result = []
        i = start_idx
        while i < len(lines):
            result.append(lines[i])
            if '\\end{equation' in lines[i] or '\\end{align' in lines[i]:
                break
            i += 1
        return '\n'.join(result), i

    def _extract_figure_block(self, lines: list, start_idx: int, current_parent: Optional[TexNode]) -> tuple[Optional[TexNode], int]:
        """Extract figure block, returning node and end index."""
        content_lines = []
        image_path = ""
        caption = ""
        i = start_idx
        while i < len(lines):
            line = lines[i]
            content_lines.append(line)
            # capture includegraphics path
            m = re.search(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', line)
            if m:
                image_path = m.group(1)
            if '\\caption{' in line:
                # Use brace extraction to keep nested formatting like \textbf{}
                caption = self._extract_braces(line[line.find('\\caption'):])
            if '\\end{figure' in line:
                break
            i += 1
        if not image_path:
            return None, i
        node = TexNode(
            type='figure',
            content=caption or image_path,
            level=current_parent.level + 1 if current_parent else 0,
            meta={'image_path': image_path, 'caption': caption}
        )
        return node, i
    
    def to_dict_list(self, nodes: List[TexNode]) -> List[dict]:
        """Convert all nodes to dictionaries"""
        return [node.to_dict() for node in nodes]


# Example usage
if __name__ == "__main__":
    sample_cleaned_tex = r"""
    \section{Introduction}
    This is the introduction section.
    We study the problem of optimization.
    
    \subsection{Related Work}
    Previous work \cite{Smith2020} showed important results.
    
    \begin{equation}
    f(x) = x^2
    \end{equation}
    
    \section{Methodology}
    Our approach is novel.
    """
    
    parser = TexParser()
    nodes = parser.parse(sample_cleaned_tex)
    
    print("Parsed structure:")
    for node in nodes:
        print(f"  {node.type}: {node.content[:50]}")
        for child in node.children:
            print(f"    ↳ {child.type}: {child.content[:50]}")
