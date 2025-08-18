"""AI Model adapter for integrating existing AIModelManager with MCP tools."""

import logging
from typing import Dict, Any, Optional
import asyncio

# Import existing AI components
try:
    from ...src.models.ai_manager import AIModelManager
    from ...src.config.hardware import HardwareProfile
    AI_COMPONENTS_AVAILABLE = True
except ImportError:
    # Fallback for when existing components are not available
    AIModelManager = None
    HardwareProfile = None
    AI_COMPONENTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class MCPAIAdapter:
    """Adapter to bridge AIModelManager with MCP tools."""
    
    def __init__(self, ai_manager: Optional[Any] = None, max_memory_gb: int = 12):
        """Initialize the AI adapter.
        
        Args:
            ai_manager: Optional existing AIModelManager instance
            max_memory_gb: Maximum memory to use for model loading
        """
        self.ai_manager = ai_manager
        self.max_memory_gb = max_memory_gb
        self.is_initialized = False
        self.model_ready = False
        
        # Initialize AI manager if not provided and components are available
        if not self.ai_manager and AI_COMPONENTS_AVAILABLE and AIModelManager:
            try:
                self.ai_manager = AIModelManager(max_memory_gb=max_memory_gb)
                logger.info("Initialized new AIModelManager instance")
            except Exception as e:
                logger.warning(f"Failed to initialize AIModelManager: {e}")
                self.ai_manager = None
        
        logger.info(f"MCPAIAdapter initialized (AI available: {AI_COMPONENTS_AVAILABLE})")
    
    async def initialize(self) -> bool:
        """Initialize the AI model for inference.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if self.is_initialized:
            return self.model_ready
        
        if not self.ai_manager:
            logger.warning("No AI manager available for initialization")
            self.is_initialized = True
            self.model_ready = False
            return False
        
        try:
            logger.info("Initializing AI model...")
            self.model_ready = await self.ai_manager.load_model()
            self.is_initialized = True
            
            if self.model_ready:
                logger.info("AI model initialized successfully")
            else:
                logger.warning("AI model initialization failed")
            
            return self.model_ready
            
        except Exception as e:
            logger.error(f"Error initializing AI model: {e}")
            self.is_initialized = True
            self.model_ready = False
            return False
    
    async def generate_completion(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate code completion using the AI model.
        
        Args:
            prompt: Input prompt for completion
            context: Optional context information
            
        Returns:
            Generated completion text
        """
        if not await self._ensure_model_ready():
            return self._fallback_completion(prompt, context)
        
        try:
            # Format prompt with context
            formatted_prompt = self._format_completion_prompt(prompt, context)
            
            # Generate using AI model
            result = await self.ai_manager.generate_text(
                prompt=formatted_prompt,
                max_tokens=150,
                temperature=0.3,  # Lower temperature for more deterministic code
                timeout=30.0
            )
            
            return self._clean_completion_result(result)
            
        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            return self._fallback_completion(prompt, context)
    
    async def explain_code(
        self, 
        code: str, 
        language: str,
        detail_level: str = "detailed",
        question: Optional[str] = None
    ) -> str:
        """Generate code explanation using the AI model.
        
        Args:
            code: Code to explain
            language: Programming language
            detail_level: Level of detail for explanation
            question: Optional specific question about the code
            
        Returns:
            Code explanation text
        """
        if not await self._ensure_model_ready():
            return self._fallback_explanation(code, language, detail_level, question)
        
        try:
            # Format prompt for explanation
            formatted_prompt = self._format_explanation_prompt(
                code, language, detail_level, question
            )
            
            # Generate using AI model
            result = await self.ai_manager.generate_text(
                prompt=formatted_prompt,
                max_tokens=300,
                temperature=0.5,
                timeout=30.0
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return self._fallback_explanation(code, language, detail_level, question)
    
    async def debug_code(
        self, 
        code: str, 
        language: str,
        error_message: Optional[str] = None,
        expected_behavior: Optional[str] = None,
        actual_behavior: Optional[str] = None
    ) -> str:
        """Generate debugging assistance using the AI model.
        
        Args:
            code: Code with issues
            language: Programming language
            error_message: Error message if available
            expected_behavior: What the code should do
            actual_behavior: What the code actually does
            
        Returns:
            Debugging analysis and suggestions
        """
        if not await self._ensure_model_ready():
            return self._fallback_debug(code, language, error_message, expected_behavior, actual_behavior)
        
        try:
            # Format prompt for debugging
            formatted_prompt = self._format_debug_prompt(
                code, language, error_message, expected_behavior, actual_behavior
            )
            
            # Generate using AI model
            result = await self.ai_manager.generate_text(
                prompt=formatted_prompt,
                max_tokens=400,
                temperature=0.4,
                timeout=30.0
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating debug assistance: {e}")
            return self._fallback_debug(code, language, error_message, expected_behavior, actual_behavior)
    
    async def _ensure_model_ready(self) -> bool:
        """Ensure the AI model is ready for inference.
        
        Returns:
            True if model is ready
        """
        if not self.is_initialized:
            return await self.initialize()
        
        return self.model_ready
    
    def _format_completion_prompt(self, prompt: str, context: Optional[Dict[str, Any]]) -> str:
        """Format prompt for code completion.
        
        Args:
            prompt: Original prompt
            context: Optional context information
            
        Returns:
            Formatted prompt
        """
        language = context.get("language", "python") if context else "python"
        
        formatted = f"""You are an expert {language} programmer. Complete the following code with proper syntax and best practices.

Code to complete:
```{language}
{prompt}
```

Complete the code naturally and concisely:"""
        
        return formatted
    
    def _format_explanation_prompt(
        self, 
        code: str, 
        language: str, 
        detail_level: str,
        question: Optional[str]
    ) -> str:
        """Format prompt for code explanation.
        
        Args:
            code: Code to explain
            language: Programming language
            detail_level: Level of detail
            question: Optional specific question
            
        Returns:
            Formatted prompt
        """
        if question:
            formatted = f"""You are an expert {language} programmer. Explain this code and answer the specific question.

Code:
```{language}
{code}
```

Question: {question}

Provide a {detail_level} technical explanation:"""
        else:
            formatted = f"""You are an expert {language} programmer. Explain what this code does.

Code:
```{language}
{code}
```

Provide a {detail_level} technical explanation covering:
- What the code does
- How it works
- Key concepts used
- Any notable patterns or techniques"""
        
        return formatted
    
    def _format_debug_prompt(
        self,
        code: str,
        language: str,
        error_message: Optional[str],
        expected_behavior: Optional[str],
        actual_behavior: Optional[str]
    ) -> str:
        """Format prompt for debugging assistance.
        
        Args:
            code: Code with issues
            language: Programming language
            error_message: Error message if available
            expected_behavior: What should happen
            actual_behavior: What actually happens
            
        Returns:
            Formatted prompt
        """
        formatted = f"""You are an expert {language} programmer and debugger. Analyze this code and provide debugging assistance.

Code:
```{language}
{code}
```
"""
        
        if error_message:
            formatted += f"\nError message: {error_message}"
        
        if expected_behavior:
            formatted += f"\nExpected behavior: {expected_behavior}"
        
        if actual_behavior:
            formatted += f"\nActual behavior: {actual_behavior}"
        
        formatted += f"""

Please provide:
1. Analysis of the issue
2. Explanation of what's causing the problem
3. Specific suggestions to fix it
4. Best practices to prevent similar issues"""
        
        return formatted
    
    def _clean_completion_result(self, result: str) -> str:
        """Clean and format completion result.
        
        Args:
            result: Raw completion result
            
        Returns:
            Cleaned completion
        """
        # Remove common artifacts from AI generation
        cleaned = result.strip()
        
        # Remove markdown code blocks if present
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if len(lines) > 2:
                cleaned = "\n".join(lines[1:-1])
        
        return cleaned
    
    def _fallback_completion(self, prompt: str, context: Optional[Dict[str, Any]]) -> str:
        """Fallback completion when AI model is not available.
        
        Args:
            prompt: Original prompt
            context: Optional context
            
        Returns:
            Fallback completion
        """
        language = context.get("language", "python") if context else "python"
        return f"# AI model not available - completion for {language} code\n# Original: {prompt[:50]}..."
    
    def _fallback_explanation(
        self, 
        code: str, 
        language: str, 
        detail_level: str,
        question: Optional[str]
    ) -> str:
        """Fallback explanation when AI model is not available.
        
        Args:
            code: Code to explain
            language: Programming language
            detail_level: Detail level
            question: Optional question
            
        Returns:
            Fallback explanation
        """
        explanation = f"# Code Explanation ({detail_level})\n\n"
        explanation += f"This {language} code:\n```{language}\n{code}\n```\n\n"
        explanation += "AI model not available for detailed explanation."
        
        if question:
            explanation += f"\n\nRegarding your question: {question}\n"
            explanation += "AI model not available to answer specific questions."
        
        return explanation
    
    def _fallback_debug(
        self,
        code: str,
        language: str,
        error_message: Optional[str],
        expected_behavior: Optional[str],
        actual_behavior: Optional[str]
    ) -> str:
        """Fallback debug assistance when AI model is not available.
        
        Args:
            code: Code with issues
            language: Programming language
            error_message: Error message
            expected_behavior: Expected behavior
            actual_behavior: Actual behavior
            
        Returns:
            Fallback debug assistance
        """
        debug_text = f"# Debug Analysis for {language}\n\n"
        debug_text += f"**Code:**\n```{language}\n{code}\n```\n\n"
        
        if error_message:
            debug_text += f"**Error:** {error_message}\n\n"
        if expected_behavior:
            debug_text += f"**Expected:** {expected_behavior}\n\n"
        if actual_behavior:
            debug_text += f"**Actual:** {actual_behavior}\n\n"
        
        debug_text += "AI model not available for detailed debugging analysis."
        return debug_text
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of the AI model.
        
        Returns:
            Dictionary with model status information
        """
        status = {
            "ai_components_available": AI_COMPONENTS_AVAILABLE,
            "ai_manager_available": self.ai_manager is not None,
            "is_initialized": self.is_initialized,
            "model_ready": self.model_ready,
            "max_memory_gb": self.max_memory_gb
        }
        
        if self.ai_manager and hasattr(self.ai_manager, 'get_model_status'):
            try:
                status["ai_manager_status"] = self.ai_manager.get_model_status()
            except Exception as e:
                status["ai_manager_error"] = str(e)
        
        return status
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the AI adapter.
        
        Returns:
            Health check results
        """
        health = {
            "adapter_status": "healthy",
            "ai_available": AI_COMPONENTS_AVAILABLE,
            "model_status": "unknown",
            "timestamp": asyncio.get_event_loop().time()
        }
        
        if not AI_COMPONENTS_AVAILABLE:
            health["adapter_status"] = "degraded"
            health["model_status"] = "unavailable"
            return health
        
        if not self.ai_manager:
            health["adapter_status"] = "degraded"
            health["model_status"] = "no_manager"
            return health
        
        try:
            if await self._ensure_model_ready():
                health["model_status"] = "ready"
            else:
                health["adapter_status"] = "degraded"
                health["model_status"] = "not_ready"
        except Exception as e:
            health["adapter_status"] = "unhealthy"
            health["model_status"] = "error"
            health["error"] = str(e)
        
        return health