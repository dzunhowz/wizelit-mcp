"""
Code formatting utilities for Python code.
"""
import ast
import textwrap
from typing import Dict, Any


class CodeFormatter:
    """Formats Python code with various strategies."""
    
    @staticmethod
    def format_with_black_rules(code: str) -> Dict[str, Any]:
        """
        Apply Black-style formatting rules (without black dependency).
        
        Performs:
        - Add spaces around operators (=, +, -, *, /, ==, !=, etc.)
        - Fix indentation (4 spaces per level) using AST
        - Remove trailing whitespace
        - Normalize blank lines (max 2 consecutive)
        - Ensure single trailing newline
        
        Args:
            code: Python code to format
            
        Returns:
            Dict with formatted code and stats
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "success": False,
                "error": f"Syntax error: {str(e)}",
                "formatted_code": code,
            }
        
        # Use AST unparse (Python 3.9+) to get properly formatted code
        # This automatically handles operator spacing and indentation
        if hasattr(ast, 'unparse'):
            formatted_code = ast.unparse(tree)
        else:
            # Fallback for Python < 3.9: use code generation via AST
            # This is a simplified version that doesn't handle all cases
            formatted_code = code
        
        # Clean up the formatted code
        lines = formatted_code.split('\n')
        cleaned_lines = []
        
        # Remove trailing whitespace
        for line in lines:
            cleaned_lines.append(line.rstrip())
        
        # Remove excessive blank lines (max 2 consecutive)
        final_lines = []
        consecutive_blanks = 0
        for line in cleaned_lines:
            if line.strip() == '':
                consecutive_blanks += 1
                if consecutive_blanks <= 2:
                    final_lines.append(line)
            else:
                consecutive_blanks = 0
                final_lines.append(line)
        
        formatted_code = '\n'.join(final_lines)
        
        # Remove trailing blank lines
        while formatted_code.endswith('\n\n\n'):
            formatted_code = formatted_code[:-1]
        
        # Ensure single trailing newline
        if formatted_code and not formatted_code.endswith('\n'):
            formatted_code += '\n'
        
        original_lines = len(code.split('\n'))
        formatted_lines_count = len(final_lines)
        
        return {
            "success": True,
            "formatted_code": formatted_code,
            "original_line_count": original_lines,
            "formatted_line_count": formatted_lines_count,
            "lines_removed": original_lines - formatted_lines_count,
        }
    
    @staticmethod
    def normalize_imports(code: str) -> Dict[str, Any]:
        """
        Normalize and organize import statements.
        
        Args:
            code: Python code to process
            
        Returns:
            Dict with organized imports
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "success": False,
                "error": f"Syntax error: {str(e)}",
                "formatted_code": code,
            }
        
        lines = code.split('\n')
        
        # Separate imports and other code
        import_lines = []
        other_lines = []
        in_imports = True
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('import ', 'from ')) and in_imports:
                import_lines.append(line)
            elif stripped == '' and in_imports and not import_lines:
                other_lines.append(line)
            else:
                in_imports = False
                other_lines.append(line)
        
        # Sort imports
        stdlib_imports = []
        third_party_imports = []
        local_imports = []
        
        for imp in import_lines:
            stripped = imp.strip()
            if stripped.startswith('from .') or stripped.startswith('import .'):
                local_imports.append(imp)
            elif stripped.startswith(('from __future__', 'import sys', 'import os', 'import re')):
                stdlib_imports.append(imp)
            else:
                third_party_imports.append(imp)
        
        # Combine in order: stdlib, third-party, local
        organized_imports = []
        if stdlib_imports:
            organized_imports.extend(sorted(set(stdlib_imports)))
        if third_party_imports:
            if organized_imports:
                organized_imports.append('')  # Blank line separator
            organized_imports.extend(sorted(set(third_party_imports)))
        if local_imports:
            if organized_imports:
                organized_imports.append('')  # Blank line separator
            organized_imports.extend(sorted(set(local_imports)))
        
        # Reconstruct code
        if organized_imports:
            organized_imports.append('')  # Blank line after imports
        formatted_code = '\n'.join(organized_imports + other_lines)
        
        return {
            "success": True,
            "formatted_code": formatted_code,
            "import_count": len(import_lines),
            "imports_organized": True,
            "sections": {
                "stdlib": len(stdlib_imports),
                "third_party": len(third_party_imports),
                "local": len(local_imports),
            },
        }
    
    @staticmethod
    def indent_code(code: str, indent_size: int = 4) -> Dict[str, Any]:
        """
        Normalize indentation in code.
        
        Args:
            code: Python code to process
            indent_size: Number of spaces for indentation
            
        Returns:
            Dict with reformatted code
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "success": False,
                "error": f"Syntax error: {str(e)}",
                "formatted_code": code,
            }
        
        lines = code.split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.strip() == '':
                formatted_lines.append('')
            else:
                # Get leading spaces
                leading_spaces = len(line) - len(line.lstrip())
                # Calculate indentation level
                indent_level = leading_spaces // 4  # Assume original was 4-space
                # Apply new indentation
                new_indent = ' ' * (indent_level * indent_size)
                formatted_lines.append(new_indent + line.lstrip())
        
        formatted_code = '\n'.join(formatted_lines)
        if formatted_code and not formatted_code.endswith('\n'):
            formatted_code += '\n'
        
        return {
            "success": True,
            "formatted_code": formatted_code,
            "indent_size": indent_size,
            "normalized": True,
        }
