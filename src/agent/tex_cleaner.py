"""
LaTeX/TeX Cleaner Module
=======================

Fixes the three demons:
1. The Macro Trap - expands \newcommand macros
2. The Comment Ghost - removes comments (smart % handling)
3. The Environment Mask - normalizes custom environments
"""

import re
from typing import Dict, Tuple
from dataclasses import dataclass


@dataclass
class MacroDefinition:
    """Stores a macro definition: name -> replacement text"""
    name: str
    args: int  # number of arguments (0, 1, 2, etc.)
    body: str


class TexCleaner:
    """
    Cleans and normalizes LaTeX before parsing.
    
    Usage:
        cleaner = TexCleaner()
        cleaned = cleaner.clean(raw_tex_content)
    """
    
    def __init__(self):
        self.macros: Dict[str, MacroDefinition] = {}
        self.custom_environments: Dict[str, str] = {}
    
    def clean(self, tex_content: str) -> str:
        """Main cleaning pipeline"""
        # Step 1: Extract and expand macros
        tex_content = self._extract_macros(tex_content)
        tex_content = self._expand_macros(tex_content)
        
        # Step 2: Remove comments smartly
        tex_content = self._clean_comments(tex_content)
        
        # Step 3: Normalize environments
        tex_content = self._normalize_environments(tex_content)
        
        return tex_content.strip()
    
    def _extract_macros(self, tex_content: str) -> str:
        """
        Extract \newcommand definitions and store them.
        
        Examples:
            \newcommand{\alg}{Stochastic Gradient Descent}
            \newcommand{\foo}[2]{#1 and #2}
        """
        # Pattern: \newcommand{\name}[args]{body}
        # The [args] part is optional
        pattern = r'\\newcommand\{\\(\w+)\}(?:\[(\d+)\])?\{([^}]+)\}'
        
        def extract_match(match):
            name = match.group(1)
            args = int(match.group(2)) if match.group(2) else 0
            body = match.group(3)
            
            self.macros[name] = MacroDefinition(name, args, body)
            return ""  # Remove the \newcommand line from content
        
        return re.sub(pattern, extract_match, tex_content)
    
    def _expand_macros(self, tex_content: str) -> str:
        """
        Replace macro calls with their definitions.
        
        Simple case (no args):
            \alg → Stochastic Gradient Descent
        
        With args:
            \foo[arg1][arg2] → arg1 and arg2 (body with #1, #2 replaced)
        """
        for macro_name, macro_def in self.macros.items():
            # For now, handle only no-arg macros
            # (advanced arg parsing comes later)
            if macro_def.args == 0:
                pattern = r'\\' + macro_name + r'(?![a-zA-Z])'  # Avoid partial matches
                # Use function replacement to avoid backslash escapes in macro bodies
                tex_content = re.sub(pattern, lambda _: macro_def.body, tex_content)
        
        return tex_content
    
    def _clean_comments(self, tex_content: str) -> str:
        """
        Remove % comments BUT preserve % when used for percentages.
        
        Rules:
        - "30%" or "40%" → keep the %
        - "% TODO: fix" → remove entire comment
        - "text % comment here" → becomes "text"
        """
        lines = tex_content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Find all % symbols
            i = 0
            result = ""
            while i < len(line):
                if line[i] == '%':
                    # Check if it's a percentage: digit before and nothing critical after
                    is_percentage = (
                        i > 0 and 
                        line[i-1].isdigit() and
                        (i+1 >= len(line) or not line[i+1].isalpha())
                    )
                    
                    if is_percentage:
                        result += '%'
                        i += 1
                    else:
                        # This is a comment - skip rest of line
                        break
                else:
                    result += line[i]
                    i += 1
            
            cleaned_lines.append(result.rstrip())
        
        return '\n'.join(cleaned_lines)
    
    def _normalize_environments(self, tex_content: str) -> str:
        """
        Replace custom environment definitions with standard ones.
        
        Example:
            \def\beq{\begin{equation}}
            \def\eeq{\end{equation}}
        
        Then all \beq...\eeq become \begin{equation}...\end{equation}
        """
        # Extract custom environment definitions
        pattern = r'\\def\\([a-z]+)\{\\begin\{(\w+)\}\}'
        
        def extract_env(match):
            alias = match.group(1)
            env_name = match.group(2)
            self.custom_environments[alias] = env_name
            return ""
        
        tex_content = re.sub(pattern, extract_env, tex_content)
        
        # Replace aliases with standard tags (simple version)
        # This would need more sophisticated parsing for real cases
        
        return tex_content
    
    def get_statistics(self) -> Dict[str, int]:
        """Return cleaning statistics"""
        return {
            'macros_found': len(self.macros),
            'custom_environments': len(self.custom_environments),
        }


# Example usage and tests
if __name__ == "__main__":
    sample_tex = r"""
    \newcommand{\alg}{Stochastic Gradient Descent}
    
    We use \alg for training.
    
    % TODO: Fix this data later
    The accuracy is 95%.
    
    \def\beq{\begin{equation}}
    \beq
    x = 2
    \eeq
    """
    
    cleaner = TexCleaner()
    result = cleaner.clean(sample_tex)
    
    print("Cleaned TeX:")
    print(result)
    print("\nStatistics:", cleaner.get_statistics())
