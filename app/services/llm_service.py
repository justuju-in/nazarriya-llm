import logging
from typing import List, Dict, Any, Optional
import tiktoken

from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with OpenAI LLM"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.chat_model = ChatOpenAI(
            model=settings.openai_model,
            openai_api_key=settings.openai_api_key,
            max_tokens=settings.max_tokens,
            temperature=0.7
        )
        
        # Initialize tokenizer for counting tokens
        try:
            self.tokenizer = tiktoken.encoding_for_model(settings.openai_model)
        except:
            # Fallback to default tokenizer
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        logger.info(f"LLM service initialized with model: {settings.openai_model}")
    
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string"""
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            logger.warning(f"Error counting tokens: {str(e)}")
            # Rough estimation: 1 token ≈ 4 characters
            return len(text) // 4
    
    def generate_response(
        self, 
        query: str, 
        context: List[str], 
        history: Optional[List[Dict[str, str]]] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a response using the LLM with context"""
        try:
            # Prepare system message
            system_prompt = self._create_system_prompt(context)
            
            # Prepare conversation history
            messages = [SystemMessage(content=system_prompt)]
            
            # Add conversation history if provided
            if history:
                for msg in history:
                    if msg.get("role") == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg.get("role") == "assistant":
                        messages.append(SystemMessage(content=msg["content"]))
            
            # Add current query
            messages.append(HumanMessage(content=query))
            
            # Generate response
            response = self.chat_model.invoke(messages)
            
            logger.info(f"Generated response with {len(response.content)} characters")
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
    
    def _create_system_prompt(self, context: List[str]) -> str:
        """Create a system prompt with the provided context"""
        context_text = "\n\n".join([f"Context {i+1}: {ctx}" for i, ctx in enumerate(context)])
        
        system_prompt = f"""You are a helpful AI assistant with access to the following context information. 
Use this context to provide accurate and helpful responses. If the context doesn't contain enough information 
to answer a question, say so clearly.

{context_text}

Instructions:
1. Base your answers on the provided context
2. Be concise but informative
3. If you're unsure about something, acknowledge the limitation
4. Cite specific parts of the context when relevant
5. Maintain a helpful and professional tone

Please provide your response based on the context above."""
        
        return system_prompt
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            "model": settings.openai_model,
            "embedding_model": settings.openai_embedding_model,
            "max_tokens": settings.max_tokens,
            "temperature": 0.7
        }
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> Dict[str, Any]:
        """Estimate the cost of a request (approximate)"""
        # These are approximate costs per 1K tokens (as of 2024)
        costs = {
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03}
        }
        
        model = settings.openai_model
        if model not in costs:
            model = "gpt-3.5-turbo"  # Default fallback
        
        input_cost = (input_tokens / 1000) * costs[model]["input"]
        output_cost = (output_tokens / 1000) * costs[model]["output"]
        total_cost = input_cost + output_cost
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost_usd": round(input_cost, 6),
            "output_cost_usd": round(output_cost, 6),
            "total_cost_usd": round(total_cost, 6),
            "model": model
        }
