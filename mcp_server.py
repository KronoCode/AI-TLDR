from mcp.server.fastmcp import FastMCP
from tools.browse_internet import browse_internet
from tools.send_email import send_email


mcp = FastMCP("ai-tldr-tools",json_response=True)

@mcp.tool()
def news_tool(search_query : str = "", tbm: str ="") -> str:
    """
    Search the web using SerpAPI.
    
    Use the tbm parameter to specify the type of search.
    The tbm parameter is optional and if not provided, the search will be a classic web search.
    This parameter chosen should exactly match the following values:
    - tbm="nws"  → news search (latest articles, press releases)
    - tbm=""     → classic web search (general information)
    - tbm="shop" → shopping search (products, prices)
    - tbm="isch" → image search
    - tbm="vid"  → video search
    - tbm="fin"  → finance search (stock prices, financial data)
    
    Always pick the most appropriate tbm value based on the user's request.
    Examples:
    - "latest AI news" → tbm="nws"
    - "Tesla stock price" → tbm="fin"
    - "best Python books" → tbm="shop"
    - "what is LangGraph" → tbm=""
    """
    return browse_internet(search_query, tbm)

@mcp.tool()
def send_email_tool(mail_content: str, mail_object: str = "AI TLDR – Daily digest") -> str:
    """Send the TLDR digest to the user's email. Call this last after you have the final content."""
    return send_email(mail_object=mail_object, mail_content=mail_content)

def run_mcp_server():
    mcp.run()