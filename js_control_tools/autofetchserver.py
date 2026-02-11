import asyncio
import re
from typing import Dict, Optional, Tuple, Callable, Set

from playwright.async_api import async_playwright


AUTH_KEYS = ("authorization", "proxy-authorization")


def extract_auth(headers: Dict[str, str]) -> Optional[Tuple[str, str]]:
    for k, v in headers.items():
        if k.lower() in AUTH_KEYS and v.strip():
            return (k, v)
    return None


class AuthHeaderSniffer:
    """
    Async browser tool that watches network requests
    and fires on_found when Authorization appears.

    Provides a sync get_current_channel() wrapper.
    """

    def __init__(
        self,
        url: str,
        on_found: Callable[[str, str, str], None],
        headless: bool = False,
    ):

        if not re.match(r"^https?://", url):
            url = "https://" + url

        self.url = url
        self.on_found = on_found
        self.headless = headless

        self._seen: Set[Tuple[str, str]] = set()

        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

        self._loop: Optional[asyncio.AbstractEventLoop] = None

    # ------------------------------------------------
    # Internal request handler
    # ------------------------------------------------
    async def _on_request(self, req):

        headers = req.headers
        found = extract_auth(headers)

        if not found:
            return

        name, value = found
        key = (name.lower(), value)

        if key in self._seen:
            return

        self._seen.add(key)

        self.on_found(req.url, name, value)

    # ------------------------------------------------
    # Start / Stop
    # ------------------------------------------------
    async def start(self):
        """
        Launch browser and start sniffing.
        Blocks until Ctrl+C.
        """

        self._loop = asyncio.get_running_loop()

        self._playwright = await async_playwright().start()

        self._browser = await self._playwright.chromium.launch(
            headless=self.headless
        )

        self._context = await self._browser.new_context()

        self._page = await self._context.new_page()

        self._page.on("request", self._on_request)

        await self._page.goto(self.url)

        print("\nAuthHeaderSniffer running.")
        print("Interact with page.")
        print("Press CTRL+C to stop.\n")

        try:
            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            pass

        await self.stop()

    async def stop(self):

        if self._context:
            await self._context.close()

        if self._browser:
            await self._browser.close()

        if self._playwright:
            await self._playwright.stop()

        print("Stopped.")

    # ------------------------------------------------
    # Internal async channel detector
    # ------------------------------------------------
    async def _get_current_channel_async(self):
        """
        Extracts the Channel ID directly from the URL.
        More reliable and avoids JS execution errors.
        """
        if not self._page:
            return None

        current_url = self._page.url
        
        # Discord URL Pattern: /channels/[guild_id or @me]/[channel_id]
        # This regex looks for a 17-20 digit number at the end of the URL
        match = re.search(r"channels/(?:@me|\d+)/(\d{17,20})", current_url)
        
        if match:
            channel_id = match.group(1)
            print(f"Captured Channel ID from URL: {channel_id}")
            # We return a tuple to match your previous code structure (Name, ID)
            # Since we only have the ID, we use "Detected Channel" as a placeholder name
            return ("Detected Channel", channel_id)

        return None

    # ------------------------------------------------
    # Public sync wrapper
    # ------------------------------------------------
    # ------------------------------------------------
    # Public sync wrapper (FIXED)
    # ------------------------------------------------
    def get_current_channel(self):
        """
        Sync wrapper.
        Safely asks the background thread to return the URL/Channel ID.
        """
        if not self._loop:
            print("Error: Sniffer loop is not active.")
            return None

        # CRITICAL FIX:
        # Instead of creating a new loop with asyncio.run() (which kills Playwright),
        # we dispatch the task to the EXISTING background loop.
        future = asyncio.run_coroutine_threadsafe(
            self._get_current_channel_async(),
            self._loop
        )

        try:
            # Wait for the result with a timeout so the GUI never freezes
            return future.result(timeout=2)
        except Exception as e:
            print(f"Error retrieving channel from browser: {e}")
            return None

        # Case 3: Same loop (danger zone)
        raise RuntimeError(
            "get_current_channel() cannot be called "
            "from inside the same event loop. "
            "Use await _get_current_channel_async() instead."
        )
