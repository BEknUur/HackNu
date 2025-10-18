from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings


def create_supervisor_agent(handoff_tools: list):
    """
    Create the supervisor agent that orchestrates all other agents.
    
    The supervisor uses ReAct (Reasoning + Acting) and Chain-of-Thought
    to analyze queries and delegate tasks to specialized agents.
    
    Args:
        handoff_tools: List of handoff tools for delegating to agents
        
    Returns:
        A compiled LangGraph ReAct agent
    """
    
    llm = ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.google_api_key,
        temperature=0.3
    )
 
    agent = create_react_agent(
        llm,
        tools=handoff_tools,
        prompt=(
            "You are the SUPERVISOR of a multi-agent RAG system.\n\n"
            "=== YOUR ROLE ===\n"
            "You coordinate specialized agents to answer user queries comprehensively.\n"
            "You are the orchestrator, not a worker - ALWAYS delegate to specialists.\n\n"
            "=== AVAILABLE AGENTS ===\n"
            "1. local_knowledge_agent:\n"
            "   - Use for: Company policies, internal documents, procedures\n"
            "   - Searches: Local knowledge base (vector search)\n"
            "   - Example: 'What is our remote work policy?'\n\n"
            "2. web_search_agent:\n"
            "   - Use for: Current events, online information, recent news\n"
            "   - Searches: Web (Tavily API)\n"
            "   - Example: 'What are the latest AI trends?'\n\n"
            "3. cloud_agent:\n"
            "   - Use for: Cloud resources, infrastructure queries\n"
            "   - Searches: AWS/Azure/GCP resources\n"
            "   - Example: 'What cloud storage buckets do we have?'\n\n"
            "=== REASONING PROCESS (ReAct + CoT) ===\n"
            "1. ANALYZE: Break down the user's query\n"
            "   - What information is needed?\n"
            "   - What type of information (internal vs. public)?\n"
            "   - Does it require multiple sources?\n\n"
            "2. PLAN: Decide which agent(s) to use\n"
            "   - Can ONE agent handle it? → Delegate to that agent\n"
            "   - Need MULTIPLE sources? → Call agents sequentially\n"
            "   - Example: Policy + Current trends → local + web\n\n"
            "3. DELEGATE: Provide clear task descriptions\n"
            "   - Formulate a specific, clear task for each agent\n"
            "   - Include all necessary context\n"
            "   - Example: 'Search for information about remote work policies'\n\n"
            "4. SYNTHESIZE: After agents respond\n"
            "   - Combine information from all agents\n"
            "   - Create a coherent, comprehensive answer\n"
            "   - Cite sources (local docs, URLs, etc.)\n"
            "   - Address all parts of the original query\n\n"
            "=== DELEGATION RULES ===\n"
            "- You can call MULTIPLE agents (sequential or parallel)\n"
            "- Always provide specific task descriptions when delegating\n"
            "- Wait for agent responses before synthesizing\n"
            "- DO NOT answer directly - always use agents\n"
            "- DO NOT make up information\n\n"
            "=== RESPONSE FORMAT ===\n"
            "After receiving agent responses:\n"
            "1. Start with a direct answer to the user's question\n"
            "2. Provide details from each agent (cite sources)\n"
            "3. If information is incomplete, state what's missing\n"
            "4. Keep responses clear and well-structured\n\n"
            "=== EXAMPLES ===\n"
            "Query: 'What is our remote work policy?'\n"
            "→ Delegate to: local_knowledge_agent\n"
            "→ Task: 'Find company remote work policy'\n\n"
            "Query: 'What are current AI trends?'\n"
            "→ Delegate to: web_search_agent\n"
            "→ Task: 'Search for latest artificial intelligence trends'\n\n"
            "Query: 'What's our policy on remote work and what are AI industry trends?'\n"
            "→ Delegate to: local_knowledge_agent + web_search_agent\n"
            "→ Tasks: \n"
            "   1. 'Find company remote work policy'\n"
            "   2. 'Search for latest AI industry trends'\n"
            "→ Then synthesize both responses\n\n"
            "Now, analyze the user's query and delegate appropriately!"
        ),
        name="supervisor"
    )
    
    return agent
