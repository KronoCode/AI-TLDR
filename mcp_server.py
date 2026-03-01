# from mcp.server.fastmcp import FastMCP


# mcp = FastMCP("ai-tldr-tools",json_response=True)

# @mcp.tool()
# def news_tool() -> str:
#     """Fetch latest world business news for grounding the newsletter."""
#     return browse_internet()


# @mcp.tool()
# def tldr_tool(level: str = "intermediate",
#               topic: str = "finance_tips",
#               fetched_info: str = "") -> str:
#     """
#     Create a TLDR newsletter based on the data given "fetched_info" for the given level and topic.
#     This tool needs the following arguments: 
#     - level : expertise of the final user
#     - topic : on which topic the newsletter is about
#     - fetched_info : information scraped from the Internet that should be processed, explained and vulgarized.
#     The three arguments are necessary.
#     """
#     return get_tldr(level=level, topic=topic, fetched_info=fetched_info)

# @mcp.tool()
# def summarize_tool(text: str, max_sentences: int = 40) -> str:
#     """
#     Shorten long text to at most max_sentences sentences.
#     This tool needs the following arguments: 
#     - text : the text that needs to be summarized.
#     - max_sentences : how many sentences at maximum the summarized text can have.
#     The two arguments are necessary.
#     """
#     return summarize(text=text, max_sentences=max_sentences)


# @mcp.tool()
# def send_email_tool(mail_content, mail_object: str = "AI TLDR – Daily digest") -> str:
#     """
#     Send the final TLDR by email; content should be the final newsletter body.
#     This tool needs the following arguments: 
#     - mail_object : object of the mail sent to the final user
#     - mail_content : body/content of the mail sent to the final user.
#     The two arguments are necessary.
#     """
#     return send_tldr_email(mail_object=mail_object, mail_content=mail_content)

# def run_mcp_server():
#     mcp.run()