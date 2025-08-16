import os
import json
import asyncio
from urllib.parse import urlparse
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, LLMExtractionStrategy


def get_default_selector(url: str) -> str | None:
    domain = urlparse(url).netloc.lower()
    if "pakwheels.com" in domain:
        # Example selectors for PakWheels car listings
        return ".search-title, .price, .make-model, .year, .mileage"
    # Add more domain-specific selectors as needed
    return None  # Let user provide selector if not recognized


async def scrape_car_product(url: str, css_selector: str = None) -> dict:
    """
    Scrapes car details from a given URL using LLM extraction.

    Args:
        url (str): The car listing page URL.
        css_selector (str): Optional CSS selector for relevant content.

    Returns:
        dict: Extracted car details.
    """


    browser_config = BrowserConfig(
        browser_type="chromium",
        # headless=True,
        headless=False,
        verbose=False,
    )

    # Generic schema for car extraction
    schema = {
        "name": {"type": "string", "description": "Car name"},
        "brand": {"type": "string", "description": "Car brand"},
        "model": {"type": "string", "description": "Car model"},
        "year": {"type": "string", "description": "Manufacturing year"},
        "price": {"type": "string", "description": "Car price"},
        "mileage": {"type": "string", "description": "Car mileage"},
        "location": {"type": "string", "description": "Location"},
    }



    llm_strategy = LLMExtractionStrategy(
        provider="groq/deepseek-r1-distill-llama-70b",
        api_token=os.getenv("GROQ_API_KEY"),
        schema=schema,
        extraction_type="schema",
        instruction=(
            "Extract all car objects with 'name', 'brand', 'model', 'year', 'price', 'mileage', and 'location' from the following content. "
            "Return empty string for any field not found."
        ),
        input_format="markdown",
        verbose=False,
    )

    # Use default selector if not provided
    if not css_selector:
        css_selector = get_default_selector(url)
    print(f"Using CSS selector: {css_selector}", flush=True)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        await asyncio.sleep(3)
        result = await crawler.arun(
            url=url,
            config=CrawlerRunConfig(
                extraction_strategy=llm_strategy,
                session_id="car_scrape_session",
                css_selector=css_selector,
            ),
        )

        if result.success and result.extracted_content:
            data = json.loads(result.extracted_content)
            return data[0] if isinstance(data, list) and data else data
        else:
            print(f"Error: {result.error_message}")
            return {}

# Example usage:
# import asyncio
# url = "https://www.amazon.ae/MySmile-Whitening-Non-Sensitive-Whitener-Beautiful/dp/B0BB2HT455/ref=..."
# product = asyncio.run(scrape_product(url))
# print(product)