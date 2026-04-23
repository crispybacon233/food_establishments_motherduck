import re
from urllib.parse import unquote

from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup
from datetime import datetime
import time


def get_coordinates(page: Page) -> tuple[float | None, float | None]:
    """
    Get the coordinates of the establishment from the Google Maps page.
    Args:
        page: The Playwright page object.
    Returns:
        A tuple of the latitude and longitude of the establishment.
    """
    html =  page.content()
    soup = BeautifulSoup(html, "html.parser")

    a = soup.find("a", attrs={"aria-label": "Sign in"})
    if not a:
        return None, None

    href: str | None = a.get("href")
    if not href:
        return None, None

    decoded_href = unquote(href)

    match = re.search(r'@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)', decoded_href)
    if not match:
        return None, None

    return float(match.group(1)), float(match.group(2))


def get_google_name(page: Page) -> str | None:
    """Get Google's name for the establishment."""
    try:
        el = page.locator('//h1[@class="DUwDvf lfPIob"]').first
        text = el.text_content(timeout=1000)
        return text.strip() if text else None
    except:
        return None


def get_price(page: Page) -> str | None:
    try:
        print("Getting price...")
        locator = page.locator(".mgr77e").first
        locator.wait_for(state="visible", timeout=3000)
        text = locator.text_content(timeout=3000)
        return text.strip() if text else None
    except:
        return None


def get_category(page: Page) -> str | None:
    try:
        print("Getting category...")
        locator = page.locator(".DkEaL").first
        locator.wait_for(state="visible", timeout=3000)
        text = locator.text_content(timeout=3000)
        return text.strip() if text else None
    except:
        return None


def n_stars_reviews(page: Page) -> tuple[float | None, int | None]:
    try:
        locator = page.locator(".F7nice").first
        locator.wait_for(state="visible", timeout=3000)
        text = locator.inner_text(timeout=3000).strip()

        stars_match = re.search(r"\b(\d\.\d)\b", text)
        reviews_match = re.search(r"\(([\d,]+)\)", text)

        stars = float(stars_match.group(1)) if stars_match else None
        n_reviews = int(reviews_match.group(1).replace(",", "")) if reviews_match else None
        return stars, n_reviews
    except:
        return None, None


def scrape_establishment(establishment_data: dict, page: Page) -> dict:
    """
    Scrape the establishment information from Google Maps.
    Args:
        establishment_data: A dictionary containing the establishment data.
    Returns:
        A dictionary containing the establishment information.
    """
    print('Getting the establishment information...')

    restaurant_name = establishment_data['restaurant_name']
    address = establishment_data['address']
    zip_code = establishment_data['zip_code']
    facility_id = establishment_data['facility_id']

    try:
        coordinates = get_coordinates(page)
        latitude = coordinates[0]
        longitude = coordinates[1]
        print(latitude, longitude)
    except Exception as e:
        print(f"{e}")

    try: 
        google_name = get_google_name(page)
        print('Google name: ', google_name)
    except Exception as e:
        print(f"{e}")
    

    try:
        price = get_price(page)
        print(price)
    except Exception as e:
        print(f"{e}")

    try:
        category = get_category(page)
        print(category)
    except Exception as e:
        print(f"{e}")

    try:
        stars, n_reviews = n_stars_reviews(page)
        print(stars, n_reviews)
    except Exception as e:
        print(f"{e}")

    return {
        'restaurant_name': restaurant_name,
        'zip_code': zip_code,
        'address': address,
        'facility_id': facility_id,
        'latitude': latitude,
        'longitude': longitude,
        'google_name': google_name,
        'average_rating': stars,
        'category': category,
        'price': price,
        'n_reviews': n_reviews,
        'updated_at': datetime.now().date(),
    }


if __name__ == "__main__":
    with sync_playwright() as pw:

        # ==================================================
        # Launch browser
        # ==================================================
        print('Launching browser...')
        browser = pw.chromium.launch(
            headless=True, 
            channel="chrome"
            )
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",)
        page = context.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        # ==================================================
        # This needs to first go to google maps and sit for a bit to load the page
        # otherwise google blocks loading of number of reviews, price, etc.
        # ==================================================
        print('Going to Google Maps...')
        page.goto("https://www.google.com/maps/")
        time.sleep(5)


        # ==================================================
        # Search for the establishment
        # ==================================================
        print('Searching for the establishment...')
        page.goto(
            f"https://www.google.com/maps/search/Burger King 13450 N US 183 HWY Svrd SB Austin TX",
            wait_until="domcontentloaded"
        )
        
        print('Waiting for the page to load...')
        page.wait_for_timeout(5000)

        # print('Taking a screenshot...')
        # page.screenshot(path="debug.png")

        # ==================================================
        # Get the establishment information
        # ==================================================
        # print('Getting the establishment information...')
        # try:
        #     coordinates = get_coordinates(page)
        #     print(coordinates)
        # except Exception as e:
        #     print(f"{e}")

        # name = get_google_name(page)
        # print(name)
            
        # price = get_price(page)
        # print(price)

        # category = get_category(page)
        # print(category)

        # stars, n_reviews = n_stars_reviews(page)
        # print(stars, n_reviews)

        establishment_data = {
            'restaurant_name': 'Burger King',
            'address': '13450 N US 183 HWY Svrd SB Austin TX',
            'zip_code': '78753',
            'facility_id': 1234567890
        }
        scraped_data = scrape_establishment(establishment_data, page)
        print('Scraped data: ', scraped_data)

        browser.close()
        print('Browser closed')