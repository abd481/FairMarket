' In the name of Allah, the Most Gracious, the Most Merciful  '

# Sync Version
from playwright.sync_api import sync_playwright
import time
import csv
import asyncio 


BASE_URL = 'https://www.bayut.eg'

# Selector for all listing cards on the main page
CARDS = 'li[role="article"]' 


# Clean text from unwanted characters and spaces
def clean(text):
    if not text:
        return None
    return text.replace("\n", " ").replace("\xa0", " ").strip()


# Extract amenities list from the property details page
def extract_amenities(page):
    amenities = []

    try:
        # Find the "Features / Amenities" section header
        section = page.locator('h2:has-text("Features")').locator('..')

        # Get all text elements inside this section
        items = section.locator('div >> text=/./')

        # Count how many items were found
        count = items.count()

        # Loop through each item and extract its text
        for i in range(count):
            text = items.nth(i).inner_text().strip()

            # Keep only valid short texts (to avoid noise)
            if text and len(text) < 50:
                amenities.append(text)

    except:
        # If anything fails, just return what we have (or empty list)
        pass

    return amenities


def scrape(max_pages=2):

    with sync_playwright() as p:
        # Launch browser (headless = faster, no UI)
        browser = p.firefox.launch(headless=True)
        page =  browser.new_page()

        data = []
        all_links = set()  # Use set to avoid duplicate links

        # 1. LISTING PAGES (collect property links)
        for page_num in range(1, max_pages + 1):

            # Build URL for each page
            url = f'{BASE_URL}/en/cairo/properties-for-sale/?page={page_num}'
            page.goto(url, wait_until='domcontentloaded')

            # Small delay to allow content to load
            time.sleep(1)

            # Get all cards (properties)
            cards = page.locator(CARDS)

            # Loop through each card
            for i in range(cards.count()):
                card = cards.nth(i)

                try:
                    # Extract the first link inside the card
                    href = card.locator("a").first.get_attribute("href")
                    if href:
                        # Convert relative link to full link
                        all_links.add(BASE_URL + href)
                except:
                    continue

            print(f"Page {page_num} done → links so far: {len(all_links)}")


        # 2. DETAILS PAGES (extract data from each property)
        for link in all_links:

            # Open a new page for each property
            detail_page = browser.new_page()

            # Block images to speed up loading
            detail_page.route("**/*.{png,jpg,jpeg,webp}", lambda route: route.abort())

            detail_page.goto(link, wait_until='domcontentloaded')

            # Wait until price appears (important for dynamic content)
            detail_page.wait_for_selector('[aria-label*="Price"]')

            # Extract different fields safely
            try:
                price = clean(detail_page.locator('[aria-label*="Price"]').inner_text())
            except:
                price = None

            try:
                location = clean(detail_page.locator('[aria-label*="Property header"]').inner_text())
            except:
                location = None

            try:
                title = clean(detail_page.locator('h1, h2').first.inner_text())
            except:
                title = None

            try : 
                beds = clean(detail_page.locator('[aria-label*="Beds"]').inner_text())
            except : 
                beds = None 

            try : 
                baths = clean(detail_page.locator('[aria-label*="Baths"]').inner_text())
            except : 
                baths = None 

            try : 
                area = clean(detail_page.locator('[aria-label*="Area"]').inner_text())
            except : 
                area = None 
            
            try : 
                type = clean(detail_page.locator('[aria-label*="Type"]').inner_text())
            except:
                type = None

            try : 
                furn = clean(detail_page.locator('[aria-label*="Furnishing"]').inner_text())
            except : 
                furn = None 

            # Extract amenities list using helper function
            amenities = extract_amenities(detail_page)

            # Store all extracted data in dictionary
            data.append({
                'Price': price,
                'Type': type, 
                'Beds': beds, 
                'Baths': baths, 
                'Area': area, 
                'Furnishing': furn, 
                'Location': location,
                'Amenities': amenities,
                'Title': title,
                'Link': link
            })

            # Close the detail page to free memory
            detail_page.close()


        # 3. SAVE DATA TO CSV FILE
        with open('file.csv', mode='w', newline='', encoding='utf-8') as file:
            fieldnames = ["Price", 'Type', 'Beds', 'Baths', 'Area', 'Furnishing', "Location", "Amenities", "Title", "Link"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(data)

        # Close browser after finishing
        browser.close()


if __name__ == "__main__":
    scrape()





































'Async Version'

# In the name of Allah, the Most Gracious, the Most Merciful

from playwright.async_api import async_playwright
import asyncio
import csv
import time

BASE_URL = "https://www.bayut.eg"

# Limit concurrent detail pages
CONCURRENCY_LIMIT = 5
semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)


def clean(text):
    if not text:
        return None
    return text.replace("\n", " ").replace("\xa0", " ").strip()


# Extract amenities (list of features)
async def extract_amenities(page):
    amenities = []
    try:
        section = page.locator('h2:has-text("Features")').locator('..')
        items = section.locator('div >> text=/./')

        count = await items.count()

        for i in range(count):
            text = (await items.nth(i).inner_text()).strip()

            if text and len(text) < 50 and "more" not in text.lower():
                amenities.append(text)
    except:
        pass

    return amenities


# Scrape single property details
async def scrape_details(browser, link):
    async with semaphore:
        page = await browser.new_page()

        # Speed: block images
        await page.route("**/*.{png,jpg,jpeg,webp}", lambda route: route.abort())

        await page.goto(link, wait_until="domcontentloaded")

        try:
            await page.wait_for_selector('[aria-label*="Price"]', timeout=5000)
        except:
            pass

        try:
            price = clean(await page.locator('[aria-label*="Price"]').inner_text())
        except:
            price = None

        try:
            location = clean(await page.locator('[aria-label*="Property header"]').inner_text())
        except:
            location = None

        try:
            title = clean(await page.locator('h1, h2').first.inner_text())
        except:
            title = None

        try:
            beds = clean(await page.locator('[aria-label*="Beds"]').inner_text())
        except:
            beds = None

        try:
            baths = clean(await page.locator('[aria-label*="Baths"]').inner_text())
        except:
            baths = None

        try:
            area = clean(await page.locator('[aria-label*="Area"]').inner_text())
        except:
            area = None

        try:
            type_ = clean(await page.locator('[aria-label*="Type"]').inner_text())
        except:
            type_ = None

        try:
            furn = clean(await page.locator('[aria-label*="Furnishing"]').inner_text())
        except:
            furn = None

        # Amenities
        amenities = await extract_amenities(page)

        await page.close()

        return {
            "Price": price,
            "Type": type_,
            "Beds": beds,
            "Baths": baths,
            "Area": area,
            "Furnishing": furn,
            "Location": location,
            "Amenities": ", ".join(amenities),
            "Title": title,
            "Link": link,
        }


async def scrape(max_pages=3):
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()

        all_links = set()

        # 1. Collect listing links
        for page_num in range(1, max_pages + 1):
            url = f"{BASE_URL}/en/cairo/properties-for-sale/?page={page_num}"

            await page.goto(url, wait_until="domcontentloaded")

            time.sleep(2)

            cards = page.locator('li[role="article"]')
            count = await cards.count()

            for i in range(count):
                try:
                    href = await cards.nth(i).locator("a").first.get_attribute("href")
                    if href:
                        all_links.add(BASE_URL + href)
                except:
                    continue

            print(f"Page {page_num} done → links: {len(all_links)}")

        # 2. Scrape details concurrently
        tasks = [scrape_details(browser, link) for link in all_links]
        results = await asyncio.gather(*tasks)

        # 3. Save CSV
        with open("file2.csv", "w", newline="", encoding="utf-8") as file:
            fieldnames = [
                "Price", "Type", "Beds", "Baths",
                "Area", "Furnishing", "Location",
                "Amenities", "Title", "Link"
            ]

            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(scrape())