#tools.py
from langchain.tools import tool
import requests #for online scrapping
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from rich import print
from dotenv import load_dotenv
load_dotenv()
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

#loading tavily client
tavily=TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

#creating our 1st tool
@tool
def web_search(query : str)-> str: #says that the query parameter is a string and the function will return a string
    """Search the web for recent and reliable information on a topic. Returns Titles, URLs and snippets.""" #telling the model what to do
    results= tavily.search(query=query, max_results=5)

    out=[]

    for r in results['results']: #there is results list inside the results dict of the tavily search result
        out.append(
            f'Title: {r["title"]}\nURL: {r["url"]}\nSnippet: {r["content"][:300]}\n\n'
        )
    return "\n----\n".join(out) #joining the list of results into a single string with a separator


#print(web_search.invoke("what are the recent news of the Nepal floods?")) #to check the working of the first tool

#creating our 2nd tool
@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean text content from a given URL for deeper reading."""
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})

        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:3000]
    except Exception as e:
        return f"Could not scrape URL: {str(e)}"
#print(scrape_url.invoke("https://www.espn.in/football/story/_/id/49266819/lionel-messi-argentina-international-retirement-world-cup-copa-america"))
