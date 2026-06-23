import os
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from app.core.config import settings
from app.agents.vision import vision_agent

class BrowserControlAgent:
    def __init__(self):
        self.playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None
        self.screenshots_dir = settings.SCREENSHOTS_DIR

    async def start(self):
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=False, # Headless=False enables visual debugging and screenshot checks
                args=["--start-maximized"]
            )
            # Create a context with viewport matching screens
            self.context = await self.browser.new_context(
                viewport={"width": 1280, "height": 800},
                accept_downloads=True
            )
            self.page = await self.context.new_page()

    async def stop(self):
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    def _is_domain_allowed(self, url: str) -> bool:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.split(':')[0]
        if not domain: # Local file or relative
            return True
        return any(domain == allowed or domain.endswith("." + allowed) for allowed in settings.DOMAIN_ALLOWLIST)

    async def navigate(self, url: str) -> dict:
        await self.start()
        
        # Enforce safety check
        if not self._is_domain_allowed(url):
            return {
                "success": False,
                "error": f"Access denied: URL domain is not in the ALLOWLIST config."
            }

        try:
            response = await self.page.goto(url, wait_until="networkidle", timeout=15000)
            status = response.status if response else 200
            return {
                "success": True,
                "status": status,
                "current_url": self.page.url
            }
        except Exception as e:
            return {"success": False, "error": f"Navigation failed: {str(e)}"}

    async def capture_screenshot(self, filename: str) -> str:
        await self.start()
        path = os.path.join(self.screenshots_dir, filename)
        await self.page.screenshot(path=path)
        return path

    async def click(self, selector: str = None, text_match: str = None) -> dict:
        """
        Attempts to click a button or link. Uses Playwright selector primarily,
        but falls back to text-based matching if the primary selector fails.
        """
        await self.start()
        try:
            # If a selector is provided, try to click it
            if selector:
                try:
                    await self.page.click(selector, timeout=5000)
                    return {"success": True, "clicked": selector}
                except Exception:
                    # Selector click failed, fallback to text search
                    pass

            # Fallback text click
            if text_match:
                # Search for buttons, links, inputs containing the text
                locators = [
                    self.page.locator(f"text={text_match}"),
                    self.page.locator(f"button:has-text('{text_match}')"),
                    self.page.locator(f"a:has-text('{text_match}')"),
                    self.page.locator(f"input[type='button'][value='{text_match}']")
                ]
                for loc in locators:
                    if await loc.count() > 0:
                        await loc.first.click(timeout=5000)
                        return {"success": True, "clicked_by_text": text_match}

            # Ultimate self-healing fallback: Scan via OCR and click by coordinates
            screenshot_path = await self.capture_screenshot("temp_click_ocr.png")
            ocr_data = vision_agent.run_ocr(screenshot_path)
            if "words" in ocr_data and text_match:
                # Search words matching text
                for word in ocr_data["words"]:
                    if text_match.lower() in word["text"].lower():
                        # Calculate middle point of word box
                        cx = word["x"] + (word["w"] // 2)
                        cy = word["y"] + (word["h"] // 2)
                        await self.page.mouse.click(cx, cy)
                        return {
                            "success": True, 
                            "clicked_coordinate": (cx, cy), 
                            "warning": "Clicked via visual OCR alignment"
                        }

            return {"success": False, "error": f"Element '{selector or text_match}' not clickable."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def fill(self, selector: str, value: str) -> dict:
        """
        Fills a textbox/form input. Gracefully falls back to placeholder or label search.
        """
        await self.start()
        try:
            try:
                await self.page.fill(selector, value, timeout=5000)
                return {"success": True, "filled": selector}
            except Exception:
                pass
                
            # Fallback search by placeholders
            locators = [
                self.page.locator(f"input[placeholder='{selector}']"),
                self.page.locator(f"input[name='{selector}']"),
                self.page.locator(f"textarea[placeholder='{selector}']")
            ]
            for loc in locators:
                if await loc.count() > 0:
                    await loc.first.fill(value, timeout=5000)
                    return {"success": True, "filled_by_fallback": selector}

            return {"success": False, "error": f"Failed to locate input box for '{selector}'"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_dom_text(self) -> str:
        await self.start()
        try:
            # Scrape main text from visible body
            return await self.page.inner_text("body")
        except Exception:
            return ""

    async def manage_tabs(self, action: str, target: int = None) -> dict:
        """
        Supports creating new tabs or switching between tabs.
        """
        await self.start()
        pages = self.context.pages
        if action == "NEW":
            self.page = await self.context.new_page()
            return {"success": True, "action": "New tab created", "tab_count": len(self.context.pages)}
        elif action == "SWITCH" and target is not None:
            if 0 <= target < len(pages):
                self.page = pages[target]
                await self.page.bring_to_front()
                return {"success": True, "switched_to_tab": target, "url": self.page.url}
            else:
                return {"success": False, "error": "Tab index out of bounds."}
        return {"success": False, "error": "Invalid tab management action."}
        
    async def upload_file(self, selector: str, filepath: str) -> dict:
        await self.start()
        if not os.path.exists(filepath):
            return {"success": False, "error": f"Local file not found: {filepath}"}
        try:
            async with self.page.expect_file_chooser() as fc_info:
                await self.page.click(selector, timeout=5000)
            file_chooser = await fc_info.value
            await file_chooser.set_files(filepath)
            return {"success": True, "uploaded": filepath}
        except Exception as e:
            # Fallback set_input_files directly
            try:
                await self.page.set_input_files(selector, filepath)
                return {"success": True, "uploaded_direct": filepath}
            except Exception as ex:
                return {"success": False, "error": f"Upload failed: {str(e)} | fallback: {str(ex)}"}

browser_agent = BrowserControlAgent()
