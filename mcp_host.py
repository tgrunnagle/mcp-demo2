"""
MCP Host with LangChain Agent

This module implements a LangChain agent that:
1. Connects to a local LLM via Ollama
2. Discovers tools from MCP servers
3. Processes user prompts using the available tools
"""

import asyncio
import logging
from typing import List, Optional

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_core.tools import BaseTool

from mcp_weather_client import MCPWeatherClient
from mcp_tool_wrapper import discover_mcp_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPLangChainHost:
    """MCP Host that integrates LangChain agents with MCP tools"""
    
    def __init__(self, 
                 ollama_model: str = "llama3.2:3b",
                 ollama_base_url: str = "http://localhost:11434",
                 mcp_server_url: str = "http://localhost:8000"):
        """
        Initialize the MCP LangChain Host
        
        Args:
            ollama_model: Name of the Ollama model to use
            ollama_base_url: Base URL for Ollama API
            mcp_server_url: URL of the MCP weather server
        """
        self.ollama_model = ollama_model
        self.ollama_base_url = ollama_base_url
        self.mcp_server_url = mcp_server_url
        
        # Initialize components
        self.llm = None
        self.mcp_client = None
        self.tools: List[BaseTool] = []
        self.agent_executor = None
        
    async def initialize(self) -> bool:
        """
        Initialize the LLM, MCP client, and discover tools
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing MCP LangChain Host...")
            
            # Initialize Ollama LLM
            logger.info(f"Connecting to Ollama model: {self.ollama_model}")
            self.llm = ChatOllama(
                model=self.ollama_model,
                base_url=self.ollama_base_url,
                temperature=0.1
            )
            
            # Test LLM connection
            try:
                test_response = await self.llm.ainvoke("Hello")
                logger.info("Successfully connected to Ollama")
            except Exception as e:
                logger.error(f"Failed to connect to Ollama: {e}")
                logger.error("Make sure Ollama is running and the model is available")
                return False
            
            # Initialize MCP client
            logger.info(f"Connecting to MCP server: {self.mcp_server_url}")
            self.mcp_client = MCPWeatherClient(self.mcp_server_url)
            
            if not await self.mcp_client.connect():
                logger.error("Failed to connect to MCP server")
                return False
            
            # Discover MCP tools
            logger.info("Discovering MCP tools...")
            self.tools = await discover_mcp_tools(self.mcp_client)
            
            if not self.tools:
                logger.warning("No MCP tools discovered")
            else:
                logger.info(f"Discovered {len(self.tools)} MCP tools:")
                for tool in self.tools:
                    logger.info(f"  - {tool.name}: {tool.description}")
            
            # Create the agent
            await self._create_agent()
            
            logger.info("MCP LangChain Host initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP LangChain Host: {e}")
            return False
    
    async def _create_agent(self):
        """Create the LangChain agent with MCP tools"""
        # Define the prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "You are a helpful assistant with access to weather information tools. "
             "Use the available tools to help users get weather information for different cities. "
             "When using tools, make sure to provide clear and helpful responses based on the tool results. "
             "If a user asks about weather in a city, use the appropriate weather tools to get the information."),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Create the agent
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        
        # Create the agent executor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
    
    async def process_query(self, query: str) -> str:
        """
        Process a user query using the LangChain agent
        
        Args:
            query: User's query/prompt
            
        Returns:
            str: Agent's response
        """
        if not self.agent_executor:
            return "Error: Agent not initialized. Please call initialize() first."
        
        try:
            logger.info(f"Processing query: {query}")
            result = await self.agent_executor.ainvoke({"input": query})
            return result["output"]
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"Error processing query: {str(e)}"
    
    async def shutdown(self):
        """Shutdown the host and disconnect from MCP server"""
        logger.info("Shutting down MCP LangChain Host...")
        if self.mcp_client:
            await self.mcp_client.disconnect()
        logger.info("Shutdown complete")
    
    async def interactive_session(self):
        """Run an interactive session with the agent"""
        print("\n" + "=" * 60)
        print("MCP LangChain Agent - Interactive Session")
        print("=" * 60)
        print("Ask me about weather information for different cities!")
        print("Type 'quit', 'exit', or 'bye' to end the session.")
        print("=" * 60 + "\n")
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                    print("\nGoodbye!")
                    break
                
                if not user_input:
                    continue
                
                print("\nAgent: ", end="")
                response = await self.process_query(user_input)
                print(response)
                
            except KeyboardInterrupt:
                print("\n\nSession interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")


async def main():
    """Main function to run the MCP LangChain Host"""
    host = MCPLangChainHost()
    
    try:
        # Initialize the host
        if not await host.initialize():
            print("Failed to initialize MCP LangChain Host")
            return
        
        # Run interactive session
        await host.interactive_session()
        
    finally:
        # Cleanup
        await host.shutdown()


async def demo_queries():
    """Demo function with example queries"""
    host = MCPLangChainHost()
    
    try:
        if not await host.initialize():
            print("Failed to initialize MCP LangChain Host")
            return
        
        # Example queries
        queries = [
            "What's the weather like in New York?",
            "Can you tell me about the weather in London?",
            "What cities do you have weather information for?",
            "Update the weather for Paris to be sunny with 75°F temperature and 60% humidity",
            "What's the weather in Paris now?"
        ]
        
        print("\n" + "=" * 50)
        print("MCP LangChain Agent - Demo Queries")
        print("=" * 50)
        
        for i, query in enumerate(queries, 1):
            print(f"\n{i}. Query: {query}")
            print("-" * 40)
            response = await host.process_query(query)
            print(f"Response: {response}")
            print()
        
    finally:
        await host.shutdown()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        # Run demo queries
        asyncio.run(demo_queries())
    else:
        # Run interactive session
        asyncio.run(main())