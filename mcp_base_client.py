"""
Abstract base class for MCP clients

This module defines the abstract interface that all MCP clients should implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class MCPBaseClient(ABC):
    """Abstract base class for MCP clients"""
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to the MCP server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """
        Disconnect from the MCP server.
        """
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from the server.
        
        Returns:
            List[Dict[str, Any]]: List of tool information dictionaries
                Each dict should contain: name, description, inputSchema
        """
        pass
    
    @abstractmethod
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """
        Call a tool on the server.
        
        Args:
            name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            str: Result of the tool call
        """
        pass
    
    @abstractmethod
    async def list_prompts(self) -> List[Dict[str, Any]]:
        """
        List available prompts from the server.
        
        Returns:
            List[Dict[str, Any]]: List of prompt information dictionaries
                Each dict should contain: name, description, arguments
        """
        pass
    
    @abstractmethod
    async def get_prompt(self, name: str, arguments: Dict[str, str] = None) -> str:
        """
        Get a prompt from the server.
        
        Args:
            name: Name of the prompt to get
            arguments: Arguments to pass to the prompt (optional)
            
        Returns:
            str: The prompt content
        """
        pass