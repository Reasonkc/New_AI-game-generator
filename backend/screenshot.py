from playwright.async_api import async_playwright
import asyncio
import os

def screenshot_game(html_content):
    blob_id = 'abcd'
    screenshot_path = f'screenshots/{blob_id}.png'
    os.makedirs('screenshots', exist_ok=True)

    # Async function to run Playwright
    async def capture_screenshot():
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_content(html_content, wait_until='networkidle')
            await page.set_viewport_size({"width": 1024, "height": 768})
            await page.screenshot(path=screenshot_path)
            await browser.close()

    # Run the async part
    asyncio.run(capture_screenshot())

    return screenshot_path

# screenshot_game()