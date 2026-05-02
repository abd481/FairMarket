# SYNC VERSION 

# from playwright.sync_api import sync_playwright
# import csv


# def clean(text):
#     return text.replace("\n", " ").replace("\xa0", " ").strip() if text else None


# def safe_text(locator) : 
#     try :  
#         return clean(locator.inner_text()) 
#     except : 
#        return None 


# async def extract_amenities(page, config):
#     try:
#         # Wait for the amenities section to load
#         await page.wait_for_selector(
#             config["detail"]["amenities"]["section"],
#             timeout=5000
#         )
        
#         # Look for the "More amenities" button using the specific class
#         show_more_button = page.locator('div._3fa26637[aria-label="More amenities"]')
        
#         # Check if button exists
#         button_count = await show_more_button.count()
        
#         if button_count > 0:
#             print("Found 'More amenities' button, clicking...")
#             await show_more_button.first.click()
            
#             # Wait for the amenities to expand
#             await asyncio.sleep(0.8)  # Give it time to animate/load
#         else:
#             print("No 'More amenities' button (all amenities already visible)")
        
#         # Now extract ALL amenities (both visible + expanded)
#         section = page.locator(config["detail"]["amenities"]["section"]).locator("..")
#         items = section.locator(config["detail"]["amenities"]["items"])
        
#         # Get all text contents
#         amenities = await items.all_text_contents()
        
#         # Clean up: remove empty strings and strip whitespace
#         amenities = [a.strip() for a in amenities if a.strip()]
        
#         # Remove duplicates (sometimes happens after expansion)
#         amenities = list(dict.fromkeys(amenities))
        
#         print(f"✅ Found {len(amenities)} amenities")
#         return amenities
        
#     except Exception as e:
#         print(f"❌ Error in extract_amenities: {e}")
#         import traceback
#         traceback.print_exc()  # Print full error for debugging
#         return None

# def extract_details(page, link, config):
#     page.goto(link, wait_until="domcontentloaded")

#     data = {}

#     for key, selector in config["detail"]["fields"].items():
#         try:
#             data[key] = safe_text(page.locator(selector).first)
#         except:
#             data[key] = None

#     data["Amenities"] = extract_amenities(page, config)
#     data["Link"] = link

#     return data


# def scrape(config, max_pages=2):

#     with sync_playwright() as p:
#         browser = p.firefox.launch(headless=True)
#         page = browser.new_page()

#         all_links = set()
#         data = []

#         # 1. LISTING
#         for i in range(1, max_pages + 1):

#             url = config["base_url"] + config["listing"]["pagination_url"].format(page=i)
#             page.goto(url, wait_until="domcontentloaded")

#             cards = page.locator(config["listing"]["cards"])

#             for card in cards.all():
#              try:
#                 href = card.locator(
#                     config["listing"]["link_selector"]
#                 ).first.get_attribute("href")

#                 if href:
#                     all_links.add(config["base_url"] + href)

#              except:
#                 continue
#             print(f"Page {i} done → links so far: {len(all_links)}")
        

#         # 2. DETAILS
#         detail_page = browser.new_page()

#         detail_page.route(
#             "**/*.{png,jpg,jpeg,webp}",
#             lambda route: route.abort()
#         )

#         for link in all_links:
#             data.append(extract_details(detail_page, link, config))

   
#         # 3. SAVE
#         if data:
#             with open("output.csv", "w", newline="", encoding="utf-8") as f:
#                 writer = csv.DictWriter(f, fieldnames=data[0].keys())
#                 writer.writeheader()
#                 writer.writerows(data)

#         browser.close()
#         detail_page.close()
#         return data 
    


'ASYNC VERSION'
'ASYNC VERSION'
from playwright.async_api import async_playwright
import asyncio
import csv
import random


def clean(text):
    return text.replace("\n", " ").replace("\xa0", " ").strip() if text else None


def safe_text(locator):
    try:
        return clean(locator.inner_text())
    except:
        return None
async def extract_amenities(page, config):
    try:
        # Some properties have no amenities section at all
        h2 = page.locator('h2:has-text("Features")')
        if await h2.count() == 0:
            return []

        await h2.wait_for(timeout=3000)

        show_more_button = page.locator('[aria-label="More amenities"]')
        button_count = await show_more_button.count()

        if button_count > 0:
            # Scroll button into view before clicking
            await show_more_button.first.scroll_into_view_if_needed()
            await show_more_button.first.click(force=True)
            await page.wait_for_selector("#property-amenity-dialog", timeout=3000)
            items = page.locator("#property-amenity-dialog span")
        else:
            items = page.locator('h2:has-text("Features")').locator("..").locator("span")

        amenities = await items.all_text_contents()
        amenities = list(dict.fromkeys([a.strip() for a in amenities if a.strip()]))

        print(f"✅ Found {len(amenities)} amenities")
        return amenities

    except Exception as e:
        print(f"❌ Error in extract_amenities: {e}")
        return None
    
async def extract_details(page, link, config):
    """Extract details from a single property page"""
    try:
        await page.goto(link, wait_until="domcontentloaded", timeout=20000)
        
        # 🎭 ANTI-DETECTION: Random human-like delay
        await asyncio.sleep(random.uniform(0.5,1))
        
        data = {}

        for key, selector in config["detail"]["fields"].items():
            try:
                locator = page.locator(selector).first
                data[key] = clean(await locator.inner_text())
            except:
                data[key] = None

        data["Amenities"] = await extract_amenities(page, config)
        data["Link"] = link
        
        return data
        
    except Exception as e:
        print(f"Error scraping {link}: {e}")
        return None


async def scrape_batch(browser, links, config, user_agents):
    """Scrape a batch of links concurrently"""
    tasks = []
    
    for link in links:
        # 🎭 ANTI-DETECTION: Rotate user agents
        context = await browser.new_context(
            user_agent=random.choice(user_agents)
        )
        page = await context.new_page()
        
        # 🎭 ANTI-DETECTION: Block images for speed (looks less suspicious)
        await page.route(
            "**/*.{png,jpg,jpeg,webp,gif,svg}",
            lambda route: route.abort()
        )
        
        # Add the scraping task
        tasks.append(extract_details(page, link, config))
    
    # Run all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Clean up contexts
    for context in browser.contexts:
        await context.close()
    
    # Filter out None and exceptions
    return [r for r in results if r is not None and not isinstance(r, Exception)]


async def scrape(config, max_pages=2):
    """Main async scraping function with anti-detection"""
    
    # 🎭 ANTI-DETECTION: List of user agents to rotate
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
    ]
    
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        
        # STEP 1: Collect all listing links
        page = await browser.new_page()
        all_links = set()
        
        for i in range(1, max_pages + 1):
            url = config["base_url"] + config["listing"]["pagination_url"].format(page=i)
            await page.goto(url, wait_until="domcontentloaded")
            
            # 🎭 ANTI-DETECTION: Random delay between listing pages
            await asyncio.sleep(random.uniform(1, 2))
            
            cards = await page.locator(config["listing"]["cards"]).all()

            for card in cards:
                try:
                    href = await card.locator(
                        config["listing"]["link_selector"]
                    ).first.get_attribute("href")

                    if href:
                        all_links.add(config["base_url"] + href)
                except:
                    continue
                    
            print(f"Page {i} done → links so far: {len(all_links)}")
        
        await page.close()
        
        # STEP 2: Scrape details in controlled batches
        # 🎭 ANTI-DETECTION: Small batch size (3-5 concurrent requests)
        BATCH_SIZE = 6  # Adjust based on how aggressive you want to be
        links_list = list(all_links)
        all_data = []
        
        for i in range(0, len(links_list), BATCH_SIZE):
            batch = links_list[i:i + BATCH_SIZE]
            
            print(f"Scraping batch {i // BATCH_SIZE + 1}/{(len(links_list) + BATCH_SIZE - 1) // BATCH_SIZE}...")
            
            batch_data = await scrape_batch(browser, batch, config, USER_AGENTS)
            all_data.extend(batch_data)
            
            print(f"Progress: {len(all_data)}/{len(links_list)}")
            
            # 🎭 ANTI-DETECTION: Random delay between batches
            if i + BATCH_SIZE < len(links_list):  # Don't wait after last batch
                delay = random.uniform(1,2)  # 1-2 seconds
                print(f"Waiting {delay:.1f}s before next batch...")
                await asyncio.sleep(delay)
        
        await browser.close()
        
        # STEP 3: Save to CSV
        if all_data:
            with open("Bayut_Test.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=all_data[0].keys())
                writer.writeheader()
                writer.writerows(all_data)
            
            print(f"\n✅ Done! Scraped {len(all_data)} properties")
        
        return all_data
 