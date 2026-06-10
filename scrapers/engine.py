# In the name of Allah, The Most Gracious, The Most Merciful

from playwright.async_api import async_playwright
import asyncio
import random
from dotenv import load_dotenv
from utils.db import get_collection
load_dotenv()

def get_raw_collection():
    return get_collection("raw_listings")


def clean(text):
    """Strip newlines and non-breaking spaces from raw text."""
    return text.replace("\n", " ").replace("\xa0", " ").strip() if text else None


def filter_new_links(all_links: list) -> list:
    """Return only links that don't already exist in the database."""
    raw_collection = get_raw_collection()
    existing = set(
        doc["link"] for doc in raw_collection.find(
            {"link": {"$in": all_links}},
            {"link": 1}
        )
    )
    new_links = [link for link in all_links if link not in existing]
    print(f"🔍 Total: {len(all_links)} | Already in DB: {len(existing)} | New: {len(new_links)}")
    return new_links


async def extract_amenities(page, config):
    """
    Extract amenities from a listing detail page.

    Supports two flows:
      - Button + dialog (Bayut): clicks a button to open a modal, then reads items from it.
      - Fallback (OLX): button_label is null → skips button logic → reads items directly.
    """
    try:
        amenities_config = config["detail"]["amenities"]

        section = page.locator(amenities_config["section_title"])
        if await section.count() == 0:
            return []

        try:
            await section.first.wait_for(timeout=3000)
        except Exception:
            pass

        button_selector = amenities_config.get("button_label")  # None for OLX

        # Bayut flow: button exists → click it → try to read from dialog
        if button_selector:
            btn = page.locator(button_selector)
            if await btn.count() > 0:
                try:
                    await btn.first.scroll_into_view_if_needed()
                    await btn.first.click(force=True)

                    dialog_selector = amenities_config.get("dialog")  # None for OLX
                    if dialog_selector:
                        await page.wait_for_selector(dialog_selector, timeout=3000)
                        items = page.locator(dialog_selector).locator(
                            amenities_config.get("fallback_items", "span")
                        )
                        amenities = await items.all_text_contents()
                        return list(dict.fromkeys([a.strip() for a in amenities if a.strip()]))
                except Exception:
                    pass  # Click failed → fall through to fallback below

        # OLX flow (and Bayut fallback): read items directly from the section container
        container = section.locator("xpath=..")
        items = container.locator(amenities_config.get("fallback_items", "span"))
        amenities = await items.all_text_contents()
        return list(dict.fromkeys([a.strip() for a in amenities if a.strip()]))

    except Exception as e:
        print(f"❌ Error in extract_amenities: {e}")
        return []


async def extract_details(page, link, config):
    """Navigate to a listing page and extract all configured fields + amenities."""
    try:
        await page.goto(link, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(random.uniform(1.5,2))

        data = {}
        for key, selector in config["detail"]["fields"].items():
            try:
                locator = page.locator(selector).first
                data[key] = clean(await locator.inner_text())
            except Exception:
                data[key] = None

        data["Amenities"] = await extract_amenities(page, config)
        data["Link"] = link
        return data

    except Exception as e:
        print(f"❌ Error scraping {link}: {e}")
        return None


async def scrape_batch(browser, links, config, user_agents):
    """
    Scrape a batch of listing detail pages concurrently.

    Each link gets its own browser context and page to avoid shared state.
    Images are blocked per page to reduce bandwidth and speed up loads.
    """
    tasks = []
    contexts = []

    for link in links:
        context = await browser.new_context(
            user_agent=random.choice(user_agents),
            viewport={
                "width": random.randint(1200, 1920),
                "height": random.randint(700, 1080)
            }
        )
        page = await context.new_page()

        # Must be async — Playwright requires a coroutine handler, not a plain lambda
        async def block_images(route):
            await route.abort()

        await page.route("**/*.{png,jpg,jpeg,webp,gif,svg}", block_images)

        contexts.append(context)
        await asyncio.sleep(random.uniform(0.5,1))

        # Each task captures its own `page` — no shared state between tasks
        tasks.append(extract_details(page, link, config))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for context in contexts:
        await context.close()

    return [r for r in results if r is not None and not isinstance(r, Exception)]


async def scrape(config, max_pages=2):
    """
    Main scraping pipeline:
      1. Collect listing links across paginated pages.
      2. Filter out links already stored in MongoDB.
      3. Scrape detail pages in batches.
      4. Retry any failed links once.
    """
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
    ]

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)

        # ── STEP 1: Collect listing links ────────────────────────────────────
        page = await browser.new_page()
        all_links = []

        for i in range(1, max_pages + 1):
            url = config["base_url"] + config["listing"]["pagination_url"].format(page=i)

            # Retry up to 4 times per page in case of network issues or blocks
            page_loaded = False
            for attempt in range(4):
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page_loaded = True
                    break
                except Exception:
                    if attempt == 3:
                        print(f"⚠️ Skipping page {i} — failed after 4 attempts")
                        break
                    wait = random.uniform(4, 8)
                    print(f"⚠️ Page {i} failed, retrying in {wait:.1f}s (attempt {attempt + 2}/3)...")
                    await asyncio.sleep(wait)

            if not page_loaded:
                continue

            await asyncio.sleep(random.uniform(1, 2))

            cards = await page.locator(config["listing"]["cards"]).all()

            for card in cards:
                try:
                    href = await card.locator(
                        config["listing"]["link_selector"]
                    ).first.get_attribute("href")

                    if href:
                        full_link = config["base_url"] + href
                        if full_link not in all_links:
                            all_links.append(full_link)
                except Exception:
                    continue

            print(f"Page {i} done → total links collected: {len(all_links)}")

        await page.close()

        if not all_links:
            print("❌ No links collected — exiting")
            await browser.close()
            return []

        # ── STEP 2: Filter already-scraped links ─────────────────────────────
        new_links = filter_new_links(all_links)

        if not new_links:
            print("⚠️ No new listings found — all already in DB")
            await browser.close()
            return []

        # ── STEP 3: Scrape detail pages in batches ───────────────────────────
        BATCH_SIZE = 6
        all_data = []
        failed_links = []

        for i in range(0, len(new_links), BATCH_SIZE):
            batch = new_links[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            total_batches = (len(new_links) + BATCH_SIZE - 1) // BATCH_SIZE
            print(f"Scraping batch {batch_num}/{total_batches}...")

            batch_data = await scrape_batch(browser, batch, config, USER_AGENTS)

            scraped_links = {d["Link"] for d in batch_data if d}
            for link in batch:
                if link not in scraped_links:
                    failed_links.append(link)

            all_data.extend(batch_data)
            print(f"Progress: {len(all_data)}/{len(new_links)} scraped | Failed so far: {len(failed_links)}")

            if i + BATCH_SIZE < len(new_links):
                delay = random.uniform(1.5, 1.9)
                print(f"Waiting {delay:.1f}s before next batch...")
                await asyncio.sleep(delay)

        # ── STEP 4: Retry failed links once ──────────────────────────────────
        if failed_links:
            print(f"\n🔄 Retrying {len(failed_links)} failed links...")
            await asyncio.sleep(5)

            for i in range(0, len(failed_links), BATCH_SIZE):
                batch = failed_links[i:i + BATCH_SIZE]
                retry_data = await scrape_batch(browser, batch, config, USER_AGENTS)
                all_data.extend(retry_data)
                print(f"Retry progress: {len(retry_data)}/{len(batch)} recovered")
                await asyncio.sleep(random.uniform(3, 5))

        await browser.close()

        remaining_failed = [l for l in failed_links if l not in {d["Link"] for d in all_data}]
        print(f"\n✅ Done! Collected: {len(all_data)} | Still failed: {len(remaining_failed)}")
        return all_data
