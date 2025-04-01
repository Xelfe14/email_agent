import json
from typing import Dict, List, Any, Optional
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.agents import Tool

def research_company(extracted_info: Dict[str, Any], api_key: str, max_queries: int = 3) -> str:
    """
    Research a company using the WebResearcher class.

    Args:
        extracted_info: Dictionary of extracted entities from email
        api_key: OpenAI API key
        max_queries: Maximum number of search queries to generate

    Returns:
        Research summary about the company
    """
    researcher = WebResearcher(api_key=api_key)
    return researcher.research_company(extracted_info, max_queries=max_queries)

class WebResearcher:
    """
    Performs web research to gather additional context about companies and individuals.
    """

    def __init__(self, api_key: str):
        """
        Initialize the web researcher.

        Args:
            api_key: OpenAI API key
        """
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0,
            api_key=api_key
        )

        # Set up search tool
        self.search_tool = DuckDuckGoSearchResults()

        # Create tools list
        self.tools = [
            Tool(
                name="web_search",
                func=self.search_tool.run,
                description="Search the web for information about companies and people"
            )
        ]

        # Create prompt for query generation
        self.query_prompt = ChatPromptTemplate.from_template("""
        Based on the following information extracted from an email, generate 3 specific search queries that will help find relevant information about the company and its funding context.

        Extracted information:
        {extracted_info}

        Format the result as a JSON list of strings, with each string being a search query.
        Example output: ["company name funding history", "founder name background", "company name competitors"]
        """)

        # Create prompt for research summary
        self.summary_prompt = ChatPromptTemplate.from_template("""
        You are a research assistant for an investment fund. Summarize the following search results about a company that has reached out for potential investment.

        Extracted information about the company:
        {extracted_info}

        Search results:
        {search_results}

        Provide a concise summary with these sections:
        1. Company Overview
        2. Founders Background
        3. Market Analysis
        4. Funding History (if available)
        5. Strengths and Potential Concerns

        Focus on factual information that would be relevant for making an investment decision.
        """)

    def generate_search_queries(self, extracted_info: Dict[str, Any]) -> List[str]:
        """
        Generate search queries based on extracted email information.

        Args:
            extracted_info: Dictionary of extracted entities from email

        Returns:
            List of search queries
        """
        # Format extracted info for prompt
        extracted_info_text = "\n".join([f"{k}: {v}" for k, v in extracted_info.items()])

        # Generate queries
        chain = self.query_prompt | self.llm
        result = chain.invoke({"extracted_info": extracted_info_text})

        # Parse JSON result
        try:
            queries = json.loads(result.content)
            return queries
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            if isinstance(result.content, str):
                return [q.strip() for q in result.content.split(',')]
            return []

    def search_web(self, query: str) -> str:
        """
        Perform web search using the provided query.

        Args:
            query: Search query string

        Returns:
            Search results text
        """
        try:
            results = self.search_tool.run(query)
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return f"Error performing search: {str(e)}"

    def research_company(self, extracted_info: Dict[str, Any], max_queries: int = 3) -> str:
        """
        Research company based on extracted email information.

        Args:
            extracted_info: Dictionary of extracted entities from email
            max_queries: Maximum number of search queries to run

        Returns:
            Research summary text
        """
        # Generate search queries
        queries = self.generate_search_queries(extracted_info)
        queries = queries[:max_queries]  # Limit number of queries

        # Run searches
        all_results = []
        for query in queries:
            results = self.search_web(query)
            all_results.append(f"Query: {query}\nResults: {results}\n")

        combined_results = "\n".join(all_results)

        # Create summary
        extracted_info_text = "\n".join([f"{k}: {v}" for k, v in extracted_info.items()])

        chain = self.summary_prompt | self.llm
        summary = chain.invoke({
            "extracted_info": extracted_info_text,
            "search_results": combined_results
        })

        return summary.content
