import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

class SearchTools:
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            print("⚠️ Warning: TAVILY_API_KEY is missing in .env")
            self.client = None
        else:
            self.client = TavilyClient(api_key=self.api_key)

    def search_web(self, query: str, max_results: int = 5) -> str:
        """
        Performs a web search using Tavily API.
        
        Args:
            query (str): The search query (e.g., "FastAPI vs Flask 2026").
            max_results (int): Number of results to return.
            
        Returns:
            str: A formatted summary of search results.
        """
        if not self.client:
            return "❌ Search Error: API Key not configured."

        try:
            print(f"🔎 Searching for: {query}")
            results = self.client.search(
                query=query, 
                search_depth="advanced", 
                max_results=max_results
            )
            
            # Format the output nicely for the LLM to read
            formatted_results = []
            for result in results.get('results', []):
                title = result.get('title', 'No Title')
                url = result.get('url', '#')
                content = result.get('content', 'No Content')
                formatted_results.append(f"TITLE: {title}\nURL: {url}\nCONTENT: {content}\n{'-'*30}")
            
            return "\n".join(formatted_results)

        except Exception as e:
            return f"❌ Search Failed: {str(e)}"

# Standalone execution for testing
if __name__ == "__main__":
    tool = SearchTools()
    print(tool.search_web("Bitcoin price today"))