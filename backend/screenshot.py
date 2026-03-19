from playwright.async_api import async_playwright
import asyncio
import os
import uuid


def screenshot_game(html_content, game_id=None, viewport_width=1024, viewport_height=768, timeout=30000):
    """Capture a screenshot of an HTML game.

    Args:
        html_content: The HTML string to render.
        game_id: Optional game ID for the filename. If None, a UUID is generated.
        viewport_width: Browser viewport width (default 1024).
        viewport_height: Browser viewport height (default 768).
        timeout: Page load timeout in milliseconds (default 30000).

    Returns:
        The path to the saved screenshot, or None on failure.
    """
    screenshot_id = game_id or str(uuid.uuid4())
    screenshot_path = f'screenshots/{screenshot_id}.png'
    os.makedirs('screenshots', exist_ok=True)

    async def capture_screenshot():
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.set_viewport_size({"width": viewport_width, "height": viewport_height})
                await page.set_content(html_content, wait_until='networkidle', timeout=timeout)
                await page.screenshot(path=screenshot_path)
                await browser.close()
                return screenshot_path
        except Exception as e:
            print(f"Screenshot capture failed: {e}")
            return None

    result = asyncio.run(capture_screenshot())
    return result
