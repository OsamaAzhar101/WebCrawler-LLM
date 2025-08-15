import os
import json
import asyncio
from urllib.parse import urlparse
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, LLMExtractionStrategy


def get_default_selector(url: str) -> str | None:
    domain = urlparse(url).netloc.lower()
    if "amazon." in domain:
        # Prioritize price selectors first, then others
        return (
            ".a-price .a-offscreen, "
            ".aok-offscreen, "
            "#corePriceDisplay, "
            "#corePriceDisplay_desktop_feature_div, "
            "#priceblock_ourprice, "
            "#priceblock_dealprice, "
            "#priceblock_saleprice, "
            "#titleSection, "
            "#bylineInfo"
        )
    return None

async def scrape_product(url: str) -> dict:
    """
    Scrapes product details from a given URL using LLM extraction.

    Args:
        url (str): The product page URL.

    Returns:
        dict: Extracted product details (Price, Product Name, Title, Brand).
    """
    browser_config = BrowserConfig(
        browser_type="chromium",
        # headless=True,
        headless=False,
        verbose=False,
    )

    # Define a generic schema for product extraction
    schema = {
        "title": {"type": "string", "description": "Product title"},
        "name": {"type": "string", "description": "Product name"},
        "brand": {"type": "string", "description": "Brand name"},
        "price": {"type": "string", "description": "Product price"},
    }

    llm_strategy = LLMExtractionStrategy(
        provider="groq/deepseek-r1-distill-llama-70b",
        api_token=os.getenv("GROQ_API_KEY"),
        schema=schema,
        extraction_type="schema",
        instruction=(
            "Extract the product's title, name, brand, and price from the following content. "
            "Return empty string for any field not found."
        ),
        input_format="markdown",
        verbose=False,
    )

    css_selector = get_default_selector(url)
    print(f"Using CSS selector: {css_selector}", flush=True)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        await asyncio.sleep(3)  # Add a 3 second delay after page load

        result = await crawler.arun(
            url=url,
            config=CrawlerRunConfig(
                extraction_strategy=llm_strategy,
                session_id="product_scrape_session",
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