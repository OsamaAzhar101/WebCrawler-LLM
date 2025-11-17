import json
import os
from typing import List, Set, Tuple
from urllib.parse import urlparse 

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    LLMExtractionStrategy,
    LLMConfig,  # <-- Add this line
)

from models.business import Business
from models.venue import Venue  # Add this import
from utils.data_utils import (
    is_complete_business, 
    is_duplicate_business,
    is_complete_venue,  # Add this import
    is_duplicate_venue,  # Add this import
)

def get_llm_strategy_for_companies() -> LLMExtractionStrategy:
    """
    Returns the configuration for the language model extraction strategy for companies.
    """
    return LLMExtractionStrategy(
        llm_config=LLMConfig(
            # provider="groq/deepseek-r1-distill-llama-70b",
            provider="llama-3.1-70b-versatile",  # <-- Update to a supported model
            api_token=os.getenv("GROQ_API_KEY"),
        ),
        schema={
            "type": "object",
            "properties": {
                "company_name": {"type": "string"},
                "mobile_phone": {"type": "string"},
                "ceo_phone": {"type": "string"},
                "website_url": {"type": "string"},
                "direct_page_link": {"type": "string"},
                "address": {"type": "string"},
            },
            "required": [
                "company_name",
                "mobile_phone",
                "ceo_phone",
                "website_url",
                "direct_page_link",
                "address",
            ],
        },
        extraction_type="schema",
        instruction=(
            "Extract for each company: 'company_name', 'mobile_phone', 'ceo_phone', "
            "'website_url', 'direct_page_link' (the URL of the company listing), and 'address' "
            "from the following content. If any field is not available, use an empty string. "
            "Ensure all data is accurate and up-to-date."
        ),
        input_format="markdown",
        verbose=True,
    )

async def fetch_and_process_company_page(
    crawler: AsyncWebCrawler,
    url: str,
    css_selector: str,
    llm_strategy: LLMExtractionStrategy,
    session_id: str,
    required_keys: List[str],
    seen_names: Set[str],
) -> List[dict]:
    """
    Fetches and processes a single page of company data.
    """
    print(f"Loading URL: {url}...")

    result = await crawler.arun(
        url=url,
        config=CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=llm_strategy,
            css_selector=css_selector,
            session_id=session_id,
        ),
    )

    if not (result.success and result.extracted_content):
        print(f"Error fetching URL {url}: {result.error_message}")
        return []

    extracted_data = json.loads(result.extracted_content)
    if not extracted_data:
        print(f"No companies found on {url}.")
        return []

    print("Extracted data:", extracted_data)

    complete_companies = []
    for company in extracted_data:
        # Mark incomplete fields with empty strings
        for key in required_keys:
            if key not in company or company[key] is None:
                company[key] = ""

        if not company.get("company_name"):
            continue

        if company["company_name"] in seen_names:
            print(f"Duplicate company '{company['company_name']}' found. Skipping.")
            continue

        # Add direct page link if not present
        if not company.get("direct_page_link"):
            company["direct_page_link"] = url

        seen_names.add(company["company_name"])
        complete_companies.append(company)

    if not complete_companies:
        print(f"No complete companies found on {url}.")
        return []

    print(f"Extracted {len(complete_companies)} companies from {url}.")
    return complete_companies



def get_browser_config() -> BrowserConfig:
    """
    Returns the browser configuration for the crawler.

    Returns:
        BrowserConfig: The configuration settings for the browser.
    """
    # https://docs.crawl4ai.com/core/browser-crawler-config/
    return BrowserConfig(
        browser_type="chromium",  # Type of browser to simulate
        headless=False,  # Whether to run in headless mode (no GUI)
        verbose=True,  # Enable verbose logging
    )


def get_llm_strategy() -> LLMExtractionStrategy:
    """
    Returns the configuration for the language model extraction strategy.
    """
    return LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="groq/deepseek-r1-distill-llama-70b",
            api_token=os.getenv("GROQ_API_KEY"),
        ),
        schema=Venue.model_json_schema(),
        extraction_type="schema",
        instruction=(
            "Extract all venue objects with 'name', 'location', 'price', 'capacity', "
            "'rating', 'reviews', and a 1 sentence description of the venue from the "
            "following content."
        ),
        input_format="markdown",
        verbose=True,
    )


def get_llm_strategy_for_businesses() -> LLMExtractionStrategy:
    """
    Returns the configuration for the language model extraction strategy for businesses.
    """
    return LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="groq/deepseek-r1-distill-llama-70b",
            api_token=os.getenv("GROQ_API_KEY"),
        ),
        schema=Business.model_json_schema(),
        extraction_type="schema",
        instruction=(
            "Extract all business information including 'name', 'address', 'phone', and 'email' "
            "from the following content. If any field is not available, use an empty string. "
            "Look for business listings, directory entries, or contact information sections."
        ),
        input_format="markdown",
        verbose=True,
    )

def get_css_selector_for_url(url: str, selectors_dict: dict, default: str) -> str:
    """
    Returns the appropriate CSS selector based on the URL domain.

    Args:
        url (str): The URL to scrape.
        selectors_dict (dict): Dictionary mapping domains to CSS selectors.
        default (str): Default selector if no match found.

    Returns:
        str: The CSS selector to use.
    """
    domain = urlparse(url).netloc
    for key, selector in selectors_dict.items():
        if key in domain:
            return selector
    return default


async def check_no_results(
    crawler: AsyncWebCrawler,
    url: str,
    session_id: str,
) -> bool:
    """
    Checks if the "No Results Found" message is present on the page.

    Args:
        crawler (AsyncWebCrawler): The web crawler instance.
        url (str): The URL to check.
        session_id (str): The session identifier.

    Returns:
        bool: True if "No Results Found" message is found, False otherwise.
    """
    # Fetch the page without any CSS selector or extraction strategy
    result = await crawler.arun(
        url=url,
        config=CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            session_id=session_id,
        ),
    )

    if result.success:
        if "No Results Found" in result.cleaned_html:
            return True
    else:
        print(
            f"Error fetching page for 'No Results Found' check: {result.error_message}"
        )

    return False


async def fetch_and_process_business_page(
    crawler: AsyncWebCrawler,
    url: str,
    css_selector: str,
    llm_strategy: LLMExtractionStrategy,
    session_id: str,
    required_keys: List[str],
    seen_names: Set[str],
) -> List[dict]:
    """
    Fetches and processes a single page of business data.

    Args:
        crawler (AsyncWebCrawler): The web crawler instance.
        url (str): The URL to fetch.
        css_selector (str): The CSS selector to target the content.
        llm_strategy (LLMExtractionStrategy): The LLM extraction strategy.
        session_id (str): The session identifier.
        required_keys (List[str]): List of required keys in the business data.
        seen_names (Set[str]): Set of business names that have already been seen.

    Returns:
        List[dict]: A list of processed businesses from the page.
    """
    print(f"Loading URL: {url}...")

    # Fetch page content with the extraction strategy
    result = await crawler.arun(
        url=url,
        config=CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=llm_strategy,
            css_selector=css_selector,
            session_id=session_id,
        ),
    )

    if not (result.success and result.extracted_content):
        print(f"Error fetching URL {url}: {result.error_message}")
        return []

    # Parse extracted content
    extracted_data = json.loads(result.extracted_content)
    if not extracted_data:
        print(f"No businesses found on {url}.")
        return []

    print("Extracted data:", extracted_data)

    # Process businesses
    complete_businesses = []
    for business in extracted_data:
        # Remove error key if it's False
        if business.get("error") is False:
            business.pop("error", None)

        # Check if business has at least name and one contact method
        if not business.get("name"):
            continue

        # Mark incomplete fields with empty strings
        for key in required_keys:
            if key not in business or business[key] is None:
                business[key] = ""

        if is_duplicate_business(business["name"], seen_names):
            print(f"Duplicate business '{business['name']}' found. Skipping.")
            continue

        # Add business to the list
        seen_names.add(business["name"])
        complete_businesses.append(business)

    if not complete_businesses:
        print(f"No complete businesses found on {url}.")
        return []

    print(f"Extracted {len(complete_businesses)} businesses from {url}.")
    return complete_businesses


async def fetch_and_process_page(
    crawler: AsyncWebCrawler,
    page_number: int,
    base_url: str,
    css_selector: str,
    llm_strategy: LLMExtractionStrategy,
    session_id: str,
    required_keys: List[str],
    seen_names: Set[str],
) -> Tuple[List[dict], bool]:
    """
    Fetches and processes a single page of venue data.

    Args:
        crawler (AsyncWebCrawler): The web crawler instance.
        page_number (int): The page number to fetch.
        base_url (str): The base URL of the website.
        css_selector (str): The CSS selector to target the content.
        llm_strategy (LLMExtractionStrategy): The LLM extraction strategy.
        session_id (str): The session identifier.
        required_keys (List[str]): List of required keys in the venue data.
        seen_names (Set[str]): Set of venue names that have already been seen.

    Returns:
        Tuple[List[dict], bool]:
            - List[dict]: A list of processed venues from the page.
            - bool: A flag indicating if the "No Results Found" message was encountered.
    """
    url = f"{base_url}?page={page_number}"
    print(f"Loading page {page_number}...")

    # Check if "No Results Found" message is present
    no_results = await check_no_results(crawler, url, session_id)
    if no_results:
        return [], True  # No more results, signal to stop crawling

    # Fetch page content with the extraction strategy
    result = await crawler.arun(
        url=url,
        config=CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,  # Do not use cached data
            extraction_strategy=llm_strategy,  # Strategy for data extraction
            css_selector=css_selector,  # Target specific content on the page
            session_id=session_id,  # Unique session ID for the crawl
        ),
    )

    if not (result.success and result.extracted_content):
        print(f"Error fetching page {page_number}: {result.error_message}")
        return [], False

    # Parse extracted content
    extracted_data = json.loads(result.extracted_content)
    if not extracted_data:
        print(f"No venues found on page {page_number}.")
        return [], False

    # After parsing extracted content
    print("Extracted data:", extracted_data)

    # Process venues
    complete_venues = []
    for venue in extracted_data:
        # Debugging: Print each venue to understand its structure
        print("Processing venue:", venue)

        # Ignore the 'error' key if it's False
        if venue.get("error") is False:
            venue.pop("error", None)  # Remove the 'error' key if it's False

        if not is_complete_venue(venue, required_keys):
            continue  # Skip incomplete venues

        if is_duplicate_venue(venue["name"], seen_names):
            print(f"Duplicate venue '{venue['name']}' found. Skipping.")
            continue  # Skip duplicate venues

        # Add venue to the list
        seen_names.add(venue["name"])
        complete_venues.append(venue)

    if not complete_venues:
        print(f"No complete venues found on page {page_number}.")
        return [], False

    print(f"Extracted {len(complete_venues)} venues from page {page_number}.")
    return complete_venues, False  # Continue crawling
