import os
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import json


screenshot_dir = "web_scraping/screenshots"
log_file = "web_scraping/scrape_log.json"


async def fetch_chapter(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(url)
        await page.wait_for_load_state('load')

        title = await page.title()
        content = await page.locator("#mw-content-text").inner_text()

        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_id = title.replace(" ", "_").replace("/", "-")[:50]
        screenshot_path = os.path.join(screenshot_dir, f"{file_id}_{now}.png")
        await page.screenshot(path=screenshot_path, full_page=True)

        log_data = {
            "url": url,
            "title": title,
            "timestamp": now,
            "screenshot": screenshot_path,
            "text_length": len(content)
        }

        print(f"[+] Scraped: {title}")
        print(f"[+] Screenshot saved: {screenshot_path}")

        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                logs = json.load(f)
        else:
            logs = []

        logs.append(log_data)

        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)

        # with open(os.path.join(SAVE_DIR, f"{file_id}_{now}.txt"), "w", encoding="utf-8") as f:
        #     f.write(content)

        await browser.close()
        return title, content


if __name__ == "__main__":
    url = "https://en.wikisource.org/wiki/The_Gates_of_Morning/Book_1/Chapter_1"
    title,content = asyncio.run(fetch_chapter(url))
    print(f"title: {title}")
    print(f"content: {content}")