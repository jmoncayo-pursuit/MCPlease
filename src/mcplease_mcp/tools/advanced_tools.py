"""
MCPlease MCP Server - Advanced AI Tools

This module provides advanced AI-powered tools for code review,
refactoring, documentation generation, and code analysis.
"""

import asyncio
import re
import ast
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import structlog

from ..utils.logging import get_structured_logger
from ..utils.exceptions import ValidationError, AIModelError
from .ai_tools import AITools


@dataclass
class CodeIssue:
    """Represents a code quality issue."""
    line_number: int
    severity: str  # "error", "warning", "info"
    category: str  # "style", "security", "performance", "maintainability"
    message: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None


@dataclass
class RefactoringSuggestion:
    """Represents a code refactoring suggestion."""
    line_number: int
    description: str
    before_code: str
    after_code: str
    reasoning: str
    impact: str  # "low", "medium", "high"


@dataclass
class DocumentationSection:
    """Represents a documentation section."""
    title: str
    content: str
    level: int  # heading level (1, 2, 3, etc.)
    code_examples: List[str] = None


class AdvancedAITools:
    """Advanced AI-powered tools for code analysis and improvement."""
    
    def __init__(self, ai_tools: AITools):
        self.ai_tools = ai_tools
        self.logger = get_structured_logger(__name__)
    
    async def code_review(self, code: str, language: str, focus_areas: List[str] = None) -> Dict[str, Any]:
        """
        Perform comprehensive code review using AI.
        
        Args:
            code: Source code to review
            language: Programming language
            focus_areas: Specific areas to focus on (style, security, performance, etc.)
        
        Returns:
            Dictionary containing review results
        """
        try:
            # Validate inputs
            if not code.strip():
                raise ValidationError("Code cannot be empty")
            
            if not language:
                raise ValidationError("Language must be specified")
            
            # Set default focus areas if none specified
            if not focus_areas:
                focus_areas = ["style", "security", "performance", "maintainability"]
            
            # Create review prompt
            review_prompt = self._create_review_prompt(code, language, focus_areas)
            
            # Get AI response
            response = await self.ai_tools._call_ai_model(review_prompt)
            
            # Parse and structure the response
            review_results = self._parse_review_response(response, code)
            
            return {
                "success": True,
                "language": language,
                "focus_areas": focus_areas,
                "total_issues": len(review_results["issues"]),
                "issues": review_results["issues"],
                "summary": review_results["summary"],
                "score": review_results["score"]
            }
            
        except Exception as e:
            self.logger.error(f"Code review failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "language": language
            }
    
    async def suggest_refactoring(self, code: str, language: str, refactoring_type: str = "general") -> Dict[str, Any]:
        """
        Suggest code refactoring improvements using AI.
        
        Args:
            code: Source code to refactor
            language: Programming language
            refactoring_type: Type of refactoring (general, performance, readability, etc.)
        
        Returns:
            Dictionary containing refactoring suggestions
        """
        try:
            # Validate inputs
            if not code.strip():
                raise ValidationError("Code cannot be empty")
            
            if not language:
                raise ValidationError("Language must be specified")
            
            # Create refactoring prompt
            refactor_prompt = self._create_refactor_prompt(code, language, refactoring_type)
            
            # Get AI response
            response = await self.ai_tools._call_ai_model(refactor_prompt)
            
            # Parse and structure the response
            refactoring_results = self._parse_refactor_response(response, code)
            
            return {
                "success": True,
                "language": language,
                "refactoring_type": refactoring_type,
                "total_suggestions": len(refactoring_results["suggestions"]),
                "suggestions": refactoring_results["suggestions"],
                "summary": refactoring_results["summary"]
            }
            
        except Exception as e:
            self.logger.error(f"Refactoring suggestion failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "language": language
            }
    
    async def generate_documentation(self, code: str, language: str, doc_type: str = "api") -> Dict[str, Any]:
        """
        Generate documentation for code using AI.
        
        Args:
            code: Source code to document
            language: Programming language
            doc_type: Type of documentation (api, readme, inline, etc.)
        
        Returns:
            Dictionary containing generated documentation
        """
        try:
            # Validate inputs
            if not code.strip():
                raise ValidationError("Code cannot be empty")
            
            if not language:
                raise ValidationError("Language must be specified")
            
            # Create documentation prompt
            doc_prompt = self._create_doc_prompt(code, language, doc_type)
            
            # Get AI response
            response = await self.ai_tools._call_ai_model(doc_prompt)
            
            # Parse and structure the response
            doc_results = self._parse_doc_response(response, doc_type)
            
            return {
                "success": True,
                "language": language,
                "doc_type": doc_type,
                "documentation": doc_results["documentation"],
                "sections": doc_results["sections"],
                "summary": doc_results["summary"]
            }
            
        except Exception as e:
            self.logger.error(f"Documentation generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "language": language
            }
    
    async def analyze_code_complexity(self, code: str, language: str) -> Dict[str, Any]:
        """
        Analyze code complexity using AI and static analysis.
        
        Args:
            code: Source code to analyze
            language: Programming language
        
        Returns:
            Dictionary containing complexity analysis
        """
        try:
            # Validate inputs
            if not code.strip():
                raise ValidationError("Code cannot be empty")
            
            if not language:
                raise ValidationError("Language must be specified")
            
            # Perform static analysis
            static_metrics = self._analyze_static_metrics(code, language)
            
            # Create complexity analysis prompt
            complexity_prompt = self._create_complexity_prompt(code, language, static_metrics)
            
            # Get AI response
            response = await self.ai_tools._call_ai_model(complexity_prompt)
            
            # Parse and structure the response
            complexity_results = self._parse_complexity_response(response, static_metrics)
            
            return {
                "success": True,
                "language": language,
                "static_metrics": static_metrics,
                "ai_analysis": complexity_results["ai_analysis"],
                "complexity_score": complexity_results["complexity_score"],
                "recommendations": complexity_results["recommendations"]
            }
            
        except Exception as e:
            self.logger.error(f"Complexity analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "language": language
            }
    
    async def detect_code_smells(self, code: str, language: str) -> Dict[str, Any]:
        """
        Detect code smells and anti-patterns using AI.
        
        Args:
            code: Source code to analyze
            language: Programming language
        
        Returns:
            Dictionary containing detected code smells
        """
        try:
            # Validate inputs
            if not code.strip():
                raise ValidationError("Code cannot be empty")
            
            if not language:
                raise ValidationError("Language must be specified")
            
            # Create code smell detection prompt
            smell_prompt = self._create_smell_prompt(code, language)
            
            # Get AI response
            response = await self.ai_tools._call_ai_model(smell_prompt)
            
            # Parse and structure the response
            smell_results = self._parse_smell_response(response, code)
            
            return {
                "success": True,
                "language": language,
                "total_smells": len(smell_results["smells"]),
                "smells": smell_results["smells"],
                "categories": smell_results["categories"],
                "summary": smell_results["summary"]
            }
            
        except Exception as e:
            self.logger.error(f"Code smell detection failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "language": language
            }
    
    def _create_review_prompt(self, code: str, language: str, focus_areas: List[str]) -> str:
        """Create a prompt for code review."""
        areas_text = ", ".join(focus_areas)
        
        prompt = f"""You are an expert code reviewer. Please review the following {language} code focusing on: {areas_text}.

Code to review:
```{language}
{code}
```

Please provide a comprehensive code review including:
1. Code quality issues (line numbers, severity, category, message, suggestion)
2. Overall assessment and score (1-10)
3. Summary of findings

Format your response as JSON with the following structure:
{{
    "issues": [
        {{
            "line_number": <line>,
            "severity": "<error|warning|info>",
            "category": "<style|security|performance|maintainability>",
            "message": "<description>",
            "suggestion": "<improvement suggestion>",
            "code_snippet": "<relevant code>"
        }}
    ],
    "summary": "<overall assessment>",
    "score": <1-10>
}}"""
        
        return prompt
    
    def _create_refactor_prompt(self, code: str, language: str, refactoring_type: str) -> str:
        """Create a prompt for refactoring suggestions."""
        prompt = f"""You are an expert code refactoring specialist. Please analyze the following {language} code and suggest {refactoring_type} refactoring improvements.

Code to refactor:
```{language}
{code}
```

Please provide refactoring suggestions including:
1. Specific refactoring opportunities (line numbers, description, before/after code)
2. Reasoning for each suggestion
3. Impact assessment (low/medium/high)

Format your response as JSON with the following structure:
{{
    "suggestions": [
        {{
            "line_number": <line>,
            "description": "<what to refactor>",
            "before_code": "<current code>",
            "after_code": "<refactored code>",
            "reasoning": "<why this refactoring helps>",
            "impact": "<low|medium|high>"
        }}
    ],
    "summary": "<overall refactoring strategy>"
}}"""
        
        return prompt
    
    def _create_doc_prompt(self, code: str, language: str, doc_type: str) -> str:
        """Create a prompt for documentation generation."""
        prompt = f"""You are an expert technical writer. Please generate {doc_type} documentation for the following {language} code.

Code to document:
```{language}
{code}
```

Please generate comprehensive {doc_type} documentation including:
1. Clear explanations of functionality
2. Usage examples
3. Parameter descriptions
4. Return value explanations
5. Code examples

Format your response as JSON with the following structure:
{{
    "documentation": "<main documentation text>",
    "sections": [
        {{
            "title": "<section title>",
            "content": "<section content>",
            "level": <heading level>,
            "code_examples": ["<example 1>", "<example 2>"]
        }}
    ],
    "summary": "<brief overview>"
}}"""
        
        return prompt
    
    def _create_complexity_prompt(self, code: str, language: str, static_metrics: Dict[str, Any]) -> str:
        """Create a prompt for complexity analysis."""
        metrics_text = "\n".join([f"- {k}: {v}" for k, v in static_metrics.items()])
        
        prompt = f"""You are an expert code complexity analyst. Please analyze the following {language} code and its static metrics.

Code to analyze:
```{language}
{code}
```

Static metrics:
{metrics_text}

Please provide a complexity analysis including:
1. Overall complexity assessment
2. Specific complexity issues
3. Recommendations for improvement
4. Complexity score (1-10, where 1 is simple, 10 is extremely complex)

Format your response as JSON with the following structure:
{{
    "ai_analysis": "<detailed complexity analysis>",
    "complexity_score": <1-10>,
    "recommendations": ["<recommendation 1>", "<recommendation 2>"]
}}"""
        
        return prompt
    
    def _create_smell_prompt(self, code: str, language: str) -> str:
        """Create a prompt for code smell detection."""
        prompt = f"""You are an expert code quality analyst. Please detect code smells and anti-patterns in the following {language} code.

Code to analyze:
```{language}
{code}
```

Please identify code smells including:
1. Long methods/functions
2. Large classes
3. Duplicate code
4. Complex conditionals
5. Poor naming
6. Violations of SOLID principles
7. Other anti-patterns

Format your response as JSON with the following structure:
{{
    "smells": [
        {{
            "line_number": <line>,
            "type": "<smell type>",
            "description": "<description>",
            "severity": "<high|medium|low>",
            "suggestion": "<how to fix>"
        }}
    ],
    "categories": {{
        "naming": <count>,
        "complexity": <count>,
        "duplication": <count>,
        "structure": <count>
    }},
    "summary": "<overall assessment>"
}}"""
        
        return prompt
    
    def _analyze_static_metrics(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze static code metrics."""
        metrics = {
            "lines_of_code": len(code.splitlines()),
            "characters": len(code),
            "functions": 0,
            "classes": 0,
            "imports": 0,
            "comments": 0
        }
        
        if language.lower() == "python":
            try:
                tree = ast.parse(code)
                metrics.update(self._analyze_python_ast(tree))
            except SyntaxError:
                pass
        
        return metrics
    
    def _analyze_python_ast(self, tree: ast.AST) -> Dict[str, Any]:
        """Analyze Python AST for metrics."""
        metrics = {
            "functions": 0,
            "classes": 0,
            "imports": 0,
            "comments": 0
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                metrics["functions"] += 1
            elif isinstance(node, ast.ClassDef):
                metrics["classes"] += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                metrics["imports"] += 1
        
        return metrics
    
    def _parse_review_response(self, response: str, code: str) -> Dict[str, Any]:
        """Parse AI response for code review."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                import json
                parsed = json.loads(json_match.group())
                return parsed
            else:
                # Fallback parsing
                return self._fallback_review_parsing(response, code)
        except Exception as e:
            self.logger.warning(f"Failed to parse review response as JSON: {e}")
            return self._fallback_review_parsing(response, code)
    
    def _parse_refactor_response(self, response: str, code: str) -> Dict[str, Any]:
        """Parse AI response for refactoring suggestions."""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                import json
                parsed = json.loads(json_match.group())
                return parsed
            else:
                return self._fallback_refactor_parsing(response, code)
        except Exception as e:
            self.logger.warning(f"Failed to parse refactor response as JSON: {e}")
            return self._fallback_refactor_parsing(response, code)
    
    def _parse_doc_response(self, response: str, doc_type: str) -> Dict[str, Any]:
        """Parse AI response for documentation."""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                import json
                parsed = json.loads(json_match.group())
                return parsed
            else:
                return self._fallback_doc_parsing(response, doc_type)
        except Exception as e:
            self.logger.warning(f"Failed to parse doc response as JSON: {e}")
            return self._fallback_doc_parsing(response, doc_type)
    
    def _parse_complexity_response(self, response: str, static_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI response for complexity analysis."""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                import json
                parsed = json.loads(json_match.group())
                return parsed
            else:
                return self._fallback_complexity_parsing(response, static_metrics)
        except Exception as e:
            self.logger.warning(f"Failed to parse complexity response as JSON: {e}")
            return self._fallback_complexity_parsing(response, static_metrics)
    
    def _parse_smell_response(self, response: str, code: str) -> Dict[str, Any]:
        """Parse AI response for code smell detection."""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                import json
                parsed = json.loads(json_match.group())
                return parsed
            else:
                return self._fallback_smell_parsing(response, code)
        except Exception as e:
            self.logger.warning(f"Failed to parse smell response as JSON: {e}")
            return self._fallback_smell_parsing(response, code)
    
    def _fallback_review_parsing(self, response: str, code: str) -> Dict[str, Any]:
        """Fallback parsing for review response."""
        lines = code.splitlines()
        issues = []
        
        # Simple heuristic parsing
        for i, line in enumerate(lines, 1):
            if len(line.strip()) > 100:  # Long line
                issues.append(CodeIssue(
                    line_number=i,
                    severity="warning",
                    category="style",
                    message="Line is very long",
                    suggestion="Consider breaking into multiple lines",
                    code_snippet=line.strip()
                ))
        
        return {
            "issues": [asdict(issue) for issue in issues],
            "summary": "Basic code review completed",
            "score": 7
        }
    
    def _fallback_refactor_parsing(self, response: str, code: str) -> Dict[str, Any]:
        """Fallback parsing for refactor response."""
        return {
            "suggestions": [],
            "summary": "Refactoring analysis completed"
        }
    
    def _fallback_doc_parsing(self, response: str, doc_type: str) -> Dict[str, Any]:
        """Fallback parsing for documentation response."""
        return {
            "documentation": response,
            "sections": [],
            "summary": "Documentation generated"
        }
    
    def _fallback_complexity_parsing(self, response: str, static_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback parsing for complexity response."""
        return {
            "ai_analysis": response,
            "complexity_score": 5,
            "recommendations": ["Review code structure", "Consider breaking down complex functions"]
        }
    
    def _fallback_smell_parsing(self, response: str, code: str) -> Dict[str, Any]:
        """Fallback parsing for smell response."""
        return {
            "smells": [],
            "categories": {"naming": 0, "complexity": 0, "duplication": 0, "structure": 0},
            "summary": "Code smell analysis completed"
        }
