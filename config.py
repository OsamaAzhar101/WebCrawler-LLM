# config.py

BASE_URL = "https://www.theknot.com/marketplace/wedding-reception-venues-atlanta-ga"
CSS_SELECTOR = "[class^='info-container']"
# List of URLs to scrape
BUSINESS_URLS = [
    "https://www.katanning.com.au/businesses/",
    "https://www.dumbleyung.wa.gov.au/businessdirectory",
    # Add Wagin URL when available
]

# CSS selectors for different sites (site-specific)
CSS_SELECTORS = {
    "katanning.com.au": "div.business-listing, article.business, div.entry-content",
    "dumbleyung.wa.gov.au": "div.business-item, div.directory-entry, table.business-directory",
}

# CSS_SELECTOR = "[class^='info-container']"
REQUIRED_KEYS = [
    "name",
    "address",
    "phone",
    "email",
]

# Default selector if site-specific not found
DEFAULT_CSS_SELECTOR = "body"