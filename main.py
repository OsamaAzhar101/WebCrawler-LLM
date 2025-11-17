import asyncio

from crawl4ai import AsyncWebCrawler
from dotenv import load_dotenv

from config import BASE_URL, CSS_SELECTOR, REQUIRED_KEYS, BUSINESS_URLS, CSS_SELECTORS, DEFAULT_CSS_SELECTOR

from utils.data_utils import (
    save_venues_to_csv,
    save_businesses_to_csv,
)

from utils.scraper_utils import (
    fetch_and_process_page,
    fetch_and_process_business_page,
    get_browser_config,
    get_llm_strategy,
    get_llm_strategy_for_businesses,
    get_css_selector_for_url,
)

from utils.product_scraper import scrape_product

load_dotenv()


async def crawl_businesses():
    """
    Main function to crawl business data from Western Australian town directories.
    """
    # Initialize configurations
    browser_config = get_browser_config()
    llm_strategy = get_llm_strategy_for_businesses()
    session_id = "business_crawl_session"

    # Initialize state variables
    all_businesses = []
    seen_names = set()

    # Start the web crawler context
    async with AsyncWebCrawler(config=browser_config) as crawler:
        for url in BUSINESS_URLS:
            print(f"\n{'='*60}")
            print(f"Scraping: {url}")
            print(f"{'='*60}\n")
            
            # Get the appropriate CSS selector for this URL
            css_selector = get_css_selector_for_url(url, CSS_SELECTORS, DEFAULT_CSS_SELECTOR)
            print(f"Using CSS selector: {css_selector}")
            
            # Fetch and process data from the URL
            businesses = await fetch_and_process_business_page(
                crawler,
                url,
                css_selector,
                llm_strategy,
                session_id,
                REQUIRED_KEYS,
                seen_names,
            )

            # Add the businesses from this URL to the total list
            all_businesses.extend(businesses)

            # Pause between requests to be polite and avoid rate limits
            await asyncio.sleep(3)

    # Save the collected businesses to a CSV file
    if all_businesses:
        save_businesses_to_csv(all_businesses, "western_australia_businesses.csv")
        print(f"\n{'='*60}")
        print(f"Saved {len(all_businesses)} businesses to 'western_australia_businesses.csv'.")
        print(f"{'='*60}\n")
    else:
        print("No businesses were found during the crawl.")

    # Display usage statistics for the LLM strategy
    llm_strategy.show_usage()

async def crawl_venues():
    """
    Main function to crawl venue data from the website.
    """
    # Initialize configurations
    browser_config = get_browser_config()
    llm_strategy = get_llm_strategy()
    session_id = "venue_crawl_session"

    # Initialize state variables
    page_number = 1
    all_venues = []
    seen_names = set()

    # Start the web crawler context
    # https://docs.crawl4ai.com/api/async-webcrawler/#asyncwebcrawler
    async with AsyncWebCrawler(config=browser_config) as crawler:
        while True:
            # Fetch and process data from the current page
            venues, no_results_found = await fetch_and_process_page(
                crawler,
                page_number,
                BASE_URL,
                CSS_SELECTOR,
                llm_strategy,
                session_id,
                REQUIRED_KEYS,
                seen_names,
            )

            if no_results_found:
                print("No more venues found. Ending crawl.")
                break  # Stop crawling when "No Results Found" message appears

            if not venues:
                print(f"No venues extracted from page {page_number}.")
                break  # Stop if no venues are extracted

            # Add the venues from this page to the total list
            all_venues.extend(venues)
            page_number += 1  # Move to the next page

            # Pause between requests to be polite and avoid rate limits
            await asyncio.sleep(2)  # Adjust sleep time as needed

    # Save the collected venues to a CSV file
    if all_venues:
        save_venues_to_csv(all_venues, "complete_venues.csv")
        print(f"Saved {len(all_venues)} venues to 'complete_venues.csv'.")
    else:
        print("No venues were found during the crawl.")

    # Display usage statistics for the LLM strategy
    llm_strategy.show_usage()


async def scrape_single_product():
    """
    Prompts user for a product URL and scrapes product details.
    """
    url = input("Enter the product URL: ")
    product = await scrape_product(url)
    if product:
        print("Product details found:")
        print(product)
    else:
        print("No product details could be extracted.")


async def main():
    """
    Entry point of the script.
    """
    print("Choose an option:")
    print("1. Crawl venues")
    print("2. Scrape a single product")
    print("3. Crawl Western Australian businesses")
    choice = input("Enter 1, 2, or 3: ")
    if choice == "1":
        await crawl_venues()
    elif choice == "2":
        await scrape_single_product()
    elif choice == "3":
        await crawl_businesses()
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    asyncio.run(main())
