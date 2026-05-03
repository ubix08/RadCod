"""
Deep Search Agent - Research business domains.

Uses Tavily API for comprehensive web research.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from src.orchestrator.skills import load_skill

logger = logging.getLogger("radcod.deep_search")


@dataclass
class ResearchResult:
    """Result from deep research."""
    domain: str
    industry_overview: Dict[str, Any] = field(default_factory=dict)
    best_practices: List[Dict[str, Any]] = field(default_factory=list)
    competitor_analysis: List[Dict[str, Any]] = field(default_factory=list)
    recommended_stack: Dict[str, List[str]] = field(default_factory=dict)
    compliance_notes: List[str] = field(default_factory=list)
    additional_resources: List[str] = field(default_factory=list)


class DeepSearchAgent:
    """
    Research agent that gathers comprehensive information about business domains.
    
    Uses Tavily API for web search and research.
    """
    
    def __init__(self, tavily_api_key: str = None):
        self.api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        self.skill = load_skill("deep_search")
        logger.info("DeepSearch Agent initialized.")
    
    def _load_skill(self) -> str:
        """Get skill - now uses shared loader."""
        return self.skill  # Already loaded in __init__
    
    def research(self, business_description: str) -> ResearchResult:
        """
        Perform comprehensive research on a business domain.
        
        Args:
            business_description: Description of the business to research
            
        Returns:
            ResearchResult with comprehensive research findings
        """
        try:
            # Import here to avoid issues if tavily not installed
            from tavily import TavilyClient
            
            client = TavilyClient(api_key=self.api_key)
            
            # Multi-query research approach
            queries = [
                f"{business_description} industry overview trends 2024",
                f"{business_description} best practices software",
                f"{business_description} competitors SaaS",
                f"{business_description} technology stack recommendation",
            ]
            
            all_results = []
            for query in queries:
                result = client.search(
                    query=query,
                    max_results=5,
                    include_answer=True,
                    include_raw_content=False
                )
                all_results.append({
                    "query": query,
                    "results": result.get("results", [])
                })
            
            # Parse into structured format
            # This is a simplified version - real implementation would
            # use LLM to structure the results
            
            research = ResearchResult(
                domain=business_description,
                industry_overview={"query": queries[0], "results": all_results[0]},
                best_practices=[{"source": r} for r in all_results[1].get("results", [])],
                competitor_analysis=[{"source": r} for r in all_results[2].get("results", [])],
                recommended_stack={"backend": ["FastAPI", "Django"], "frontend": ["React"]},
                additional_resources=[q["query"] for q in all_results]
            )
            
            logger.info(f"Research completed for: {business_description}")
            return research
            
        except ImportError:
            logger.warning("Tavily not installed - returning mock research")
            return ResearchResult(
                domain=business_description,
                industry_overview={"status": "unavailable", "note": "Install tavily package"},
                best_practices=[],
                competitor_analysis=[],
                recommended_stack={"backend": ["Choose based on requirements"], "frontend": []}
            )
        except Exception as e:
            logger.error(f"Research failed: {e}")
            return ResearchResult(
                domain=business_description,
                industry_overview={"error": str(e)},
                best_practices=[],
                competitor_analysis=[]
            )
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Simple web search.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of search results
        """
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=self.api_key)
            result = client.search(
                query=query,
                max_results=max_results,
                include_answer=True,
                include_raw_content=False
            )
            return result.get("results", [])
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def research_and_format(self, business_description: str) -> str:
        """
        Research and format as markdown for coding agent.
        
        Args:
            business_description: Business domain description
            
        Returns:
            Markdown formatted research findings
        """
        result = self.research(business_description)
        
        md = f"# Research: {result.domain}\n\n"
        
        md += "## Industry Overview\n"
        md += f"- {result.industry_overview}\n\n"
        
        md += "## Best Practices\n"
        for bp in result.best_practices[:3]:
            md += f"- {bp}\n"
        md += "\n"
        
        md += "## Recommended Tech Stack\n"
        for category, tools in result.recommended_stack.items():
            md += f"- {category}: {', '.join(tools)}\n"
        md += "\n"
        
        return md