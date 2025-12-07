"""AWS Bedrock LLM Service - Integrates with Claude Sonnet via Bedrock."""

import json
import logging
from typing import Optional, List, Dict, Any

import boto3
from botocore.exceptions import ClientError

from app.services.s3_config_loader import get_chatbot_config

logger = logging.getLogger(__name__)


class BedrockLLMService:
    """Service for interacting with AWS Bedrock LLM."""
    
    def __init__(self):
        self._client = None
        self._runtime_client = None
    
    @property
    def config(self):
        """Get current Bedrock configuration."""
        return get_chatbot_config().bedrock
    
    @property
    def client(self):
        """Lazy initialization of Bedrock client."""
        if self._client is None:
            self._client = boto3.client(
                "bedrock",
                region_name=self.config.region
            )
        return self._client
    
    @property
    def runtime_client(self):
        """Lazy initialization of Bedrock runtime client."""
        if self._runtime_client is None:
            self._runtime_client = boto3.client(
                "bedrock-runtime",
                region_name=self.config.region
            )
        return self._runtime_client
    
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> str:
        """Generate text using Claude via Bedrock."""
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature or self.config.temperature
        
        messages = [{"role": "user", "content": prompt}]
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }
        
        if system_prompt:
            request_body["system"] = system_prompt
        
        if stop_sequences:
            request_body["stop_sequences"] = stop_sequences
        
        try:
            response = self.runtime_client.invoke_model(
                modelId=self.config.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response["body"].read())
            
            if "content" in response_body and len(response_body["content"]) > 0:
                return response_body["content"][0]["text"]
            
            logger.warning("Empty response from Bedrock")
            return ""
            
        except ClientError as e:
            logger.error(f"Bedrock API error: {e}")
            raise
    
    def generate_with_conversation(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate text with conversation history."""
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature or self.config.temperature
        
        # Convert to Anthropic message format
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": formatted_messages
        }
        
        if system_prompt:
            request_body["system"] = system_prompt
        
        try:
            response = self.runtime_client.invoke_model(
                modelId=self.config.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response["body"].read())
            
            if "content" in response_body and len(response_body["content"]) > 0:
                return response_body["content"][0]["text"]
            
            return ""
            
        except ClientError as e:
            logger.error(f"Bedrock API error: {e}")
            raise
    
    def get_embeddings(self, text: str) -> List[float]:
        """Get embeddings for text using Titan embedding model."""
        try:
            request_body = {
                "inputText": text
            }
            
            response = self.runtime_client.invoke_model(
                modelId=self.config.embedding_model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response["body"].read())
            return response_body.get("embedding", [])
            
        except ClientError as e:
            logger.error(f"Embedding API error: {e}")
            raise
    
    def get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            embedding = self.get_embeddings(text)
            embeddings.append(embedding)
        return embeddings


# Singleton instance
_bedrock_service: Optional[BedrockLLMService] = None


def get_bedrock_service() -> BedrockLLMService:
    """Get singleton Bedrock service instance."""
    global _bedrock_service
    if _bedrock_service is None:
        _bedrock_service = BedrockLLMService()
    return _bedrock_service
