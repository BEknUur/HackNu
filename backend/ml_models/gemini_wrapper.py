"""
Gemini API Wrapper

Provides a clean interface to interact with Google's Gemini model
for financial advisory and analysis tasks.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiWrapper:
    """Wrapper for Gemini API with financial advisory capabilities."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = 0.7,
        max_tokens: Optional[int] = 8000
    ):
        """
        Initialize Gemini wrapper.
        
        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
            model_name: Model to use (default: gemini-2.0-flash-exp)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
        
        Raises:
            ValueError: If API key is not provided or found in environment
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found. Set it in environment variables "
                "or pass it to the constructor."
            )
        
        genai.configure(api_key=self.api_key)
        
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt: Optional[str] = None
        self.conversation_history: List[Dict[str, str]] = []
        
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
            }
        )
        
        logger.info(f"Gemini wrapper initialized with model: {self.model_name}")
    
    def set_system_prompt(self, system_prompt: str):
        """
        Set the system prompt for the conversation.
        
        Args:
            system_prompt: System-level instructions for the model
        """
        self.system_prompt = system_prompt
        logger.debug("System prompt set")
    
    def generate_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> str:
        """
        Generate a response from Gemini.
        
        Args:
            prompt: User prompt/query
            context: Additional context data to include
            stream: Whether to stream the response
        
        Returns:
            Generated response text
        """
        try:
            # Build the full prompt with context
            full_prompt = self._build_prompt(prompt, context)
            
            # Generate response
            if stream:
                response = self.model.generate_content(full_prompt, stream=True)
                full_response = ""
                for chunk in response:
                    if chunk.text:
                        full_response += chunk.text
                return full_response
            else:
                response = self.model.generate_content(full_prompt)
                return response.text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def generate_with_retry(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> str:
        """
        Generate response with retry logic.
        
        Args:
            prompt: User prompt/query
            context: Additional context data
            max_retries: Maximum number of retry attempts
        
        Returns:
            Generated response text
        """
        for attempt in range(max_retries):
            try:
                return self.generate_response(prompt, context)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
        
        raise RuntimeError("Failed to generate response after retries")
    
    def chat(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        reset_history: bool = False
    ) -> str:
        """
        Have a conversation with the model, maintaining history.
        
        Args:
            message: User message
            context: Additional context
            reset_history: Whether to reset conversation history
        
        Returns:
            Model response
        """
        if reset_history:
            self.conversation_history = []
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Build prompt with history
        prompt = self._build_conversation_prompt(message, context)
        
        # Generate response
        response = self.generate_response(prompt, context)
        
        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return response
    
    def _build_prompt(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build the full prompt with system instructions and context."""
        parts = []
        separator = "\n" + "=" * 80 + "\n"
        
        if self.system_prompt:
            parts.append(self.system_prompt)
            parts.append(separator)
        
        if context:
            parts.append("CONTEXT DATA:")
            for key, value in context.items():
                parts.append(f"\n{key.upper()}:")
                parts.append(str(value))
            parts.append(separator)
        
        parts.append("USER QUERY:")
        parts.append(prompt)
        
        return "\n".join(parts)
    
    def _build_conversation_prompt(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build prompt with conversation history."""
        parts = []
        separator = "\n" + "=" * 80 + "\n"
        
        if self.system_prompt:
            parts.append(self.system_prompt)
            parts.append(separator)
        
        if self.conversation_history:
            parts.append("CONVERSATION HISTORY:")
            for entry in self.conversation_history[-6:]:
                role = entry['role'].upper()
                content = entry['content']
                parts.append(f"\n{role}: {content}")
            parts.append(separator)
        
        if context:
            parts.append("CURRENT CONTEXT:")
            for key, value in context.items():
                parts.append(f"\n{key.upper()}:")
                parts.append(str(value))
            parts.append(separator)
        
        parts.append("USER: " + message)
        
        return "\n".join(parts)
    
    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
        logger.debug("Conversation history reset")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the current conversation history."""
        return self.conversation_history.copy()


# Default financial advisor system prompt
FINANCIAL_ADVISOR_SYSTEM_PROMPT = """You are a professional financial advisor for Zaman Bank, a leading financial institution in Kazakhstan.

YOUR ROLE:
- Analyze user financial data comprehensively and provide personalized insights
- Give actionable, specific advice based on actual user data provided
- Help users understand their spending patterns, savings, and financial health
- Provide recommendations for budgeting, saving, and achieving financial goals
- Consider cultural and regional context (Kazakhstan, KZT/USD/EUR currencies)
- Balance optimism with realism in financial planning

YOUR APPROACH:
1. Start with a clear summary of the user's financial situation
2. Highlight key insights from the data (spending patterns, savings rate, goal progress)
3. Identify areas of concern or opportunity
4. Provide specific, actionable recommendations
5. Prioritize recommendations by impact and feasibility
6. Be encouraging but honest about financial challenges

IMPORTANT GUIDELINES:
- Base all advice ONLY on the provided data - do not make assumptions
- Use specific numbers and percentages from the data
- Format monetary values with appropriate currency symbols
- Be culturally sensitive and avoid Western-centric assumptions
- If data is insufficient, clearly state what additional information would help
- Never recommend specific investment products without proper disclaimers
- Maintain professional, supportive tone throughout

RESPONSE STRUCTURE:
1. Financial Overview (brief summary)
2. Key Insights (3-5 most important findings)
3. Spending Analysis (patterns, categories, trends)
4. Savings & Goals Analysis (progress, feasibility)
5. Recommendations (prioritized, actionable steps)
6. Next Steps (immediate actions user can take)

Remember: You are providing general financial guidance, not regulated financial advice. Always encourage users to consult with licensed financial advisors for major financial decisions."""

