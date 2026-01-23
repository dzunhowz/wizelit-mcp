"""
Schema validation utilities for Python code.
"""
import ast
from typing import Dict, List, Optional, Any


class SchemaValidator:
    """Validates Python code structure against expected schemas."""
    
    def __init__(self):
        self.errors: List[str] = []
    
    def validate_function_signature(
        self,
        code: str,
        function_name: str,
        expected_params: List[str],
        expected_return_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate a function signature against expectations.
        
        Args:
            code: Python code to analyze
            function_name: Name of function to validate
            expected_params: List of expected parameter names
            expected_return_type: Expected return type annotation (optional)
            
        Returns:
            Dict with validation results
        """
        self.errors = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "valid": False,
                "function_found": False,
                "error": f"Syntax error: {str(e)}",
            }
        
        # Find the function
        func_def = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                func_def = node
                break
        
        if not func_def:
            return {
                "valid": False,
                "function_found": False,
                "error": f"Function '{function_name}' not found",
            }
        
        # Extract parameter names
        actual_params = [arg.arg for arg in func_def.args.args]
        
        # Check parameters
        missing_params = set(expected_params) - set(actual_params)
        extra_params = set(actual_params) - set(expected_params)
        
        # Extract return type if present
        return_annotation = None
        if func_def.returns:
            return_annotation = ast.unparse(func_def.returns)
        
        # Build result
        is_valid = len(missing_params) == 0 and len(extra_params) == 0
        if expected_return_type and return_annotation:
            is_valid = is_valid and return_annotation == expected_return_type
        
        return {
            "valid": is_valid,
            "function_found": True,
            "function_name": function_name,
            "actual_params": actual_params,
            "expected_params": expected_params,
            "missing_params": list(missing_params),
            "extra_params": list(extra_params),
            "return_annotation": return_annotation,
            "expected_return_type": expected_return_type,
            "has_docstring": ast.get_docstring(func_def) is not None,
        }
    
    def validate_class_structure(
        self,
        code: str,
        class_name: str,
        expected_methods: List[str],
    ) -> Dict[str, Any]:
        """
        Validate a class structure against expectations.
        
        Args:
            code: Python code to analyze
            class_name: Name of class to validate
            expected_methods: List of expected method names
            
        Returns:
            Dict with validation results
        """
        self.errors = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "valid": False,
                "class_found": False,
                "error": f"Syntax error: {str(e)}",
            }
        
        # Find the class
        class_def = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                class_def = node
                break
        
        if not class_def:
            return {
                "valid": False,
                "class_found": False,
                "error": f"Class '{class_name}' not found",
            }
        
        # Extract method names
        actual_methods = [
            node.name 
            for node in class_def.body 
            if isinstance(node, ast.FunctionDef)
        ]
        
        # Check methods
        missing_methods = set(expected_methods) - set(actual_methods)
        extra_methods = set(actual_methods) - set(expected_methods)
        
        is_valid = len(missing_methods) == 0 and len(extra_methods) == 0
        
        return {
            "valid": is_valid,
            "class_found": True,
            "class_name": class_name,
            "actual_methods": actual_methods,
            "expected_methods": expected_methods,
            "missing_methods": list(missing_methods),
            "extra_methods": list(extra_methods),
            "has_init": "__init__" in actual_methods,
            "method_count": len(actual_methods),
        }
    
    def validate_code_quality(self, code: str) -> Dict[str, Any]:
        """
        Perform basic code quality checks.
        
        Args:
            code: Python code to analyze
            
        Returns:
            Dict with quality metrics
        """
        self.errors = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "valid_syntax": False,
                "error": f"Syntax error: {str(e)}",
            }
        
        # Count various elements
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        
        # Check for type hints
        functions_with_hints = 0
        for func in functions:
            if func.returns or any(arg.annotation for arg in func.args.args):
                functions_with_hints += 1
        
        # Check for docstrings
        documented_functions = sum(1 for f in functions if ast.get_docstring(f))
        documented_classes = sum(1 for c in classes if ast.get_docstring(c))
        
        return {
            "valid_syntax": True,
            "function_count": len(functions),
            "class_count": len(classes),
            "import_count": len(imports),
            "functions_with_type_hints": functions_with_hints,
            "type_hint_coverage": f"{(functions_with_hints / len(functions) * 100) if functions else 0:.1f}%",
            "documented_functions": documented_functions,
            "function_documentation_rate": f"{(documented_functions / len(functions) * 100) if functions else 0:.1f}%",
            "documented_classes": documented_classes,
            "class_documentation_rate": f"{(documented_classes / len(classes) * 100) if classes else 0:.1f}%",
        }
