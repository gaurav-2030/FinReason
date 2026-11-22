"""Capture screenshots of the running web app (http://localhost:8501) with headless Chrome over the
DevTools protocol, for the Review 3 slides.  Start the app first: bash scripts/start_app.sh
    .venv/bin/python reviews/src/screenshots.py"""
import asyncio
import base64
import json
import subprocess
import tempfile
import time

import urllib.request

import websockets

from common import BUILD, CHROME

PORT = 9337
OUT = BUILD / "shots"


class Tab:
    def __init__(self, ws):
        self.ws, self.n = ws, 0

    async def call(self, method, **params):
        self.n += 1
        my = self.n
        await self.ws.send(json.dumps({"id": my, "method": method, "params": params}))
        while True:
            msg = json.loads(await self.ws.recv())
            if msg.get("id") == my:
                return msg.get("result", {})

    async def js(self, expr):
        r = await self.call("Runtime.evaluate", expression=expr, awaitPromise=True, returnByValue=True)
        return r.get("result", {}).get("value")

    async def wait_text(self, text, timeout=240):
        t0 = time.time()
        while time.time() - t0 < timeout:
            if await self.js(f"document.body.innerText.includes({json.dumps(text)})"):
                return True
            await asyncio.sleep(1)
        return False

    async def shot(self, name, full=True):
        await asyncio.sleep(1.5)
        params = {"format": "png", "captureBeyondViewport": full}
        if full:
            h = await self.js("Math.max(...Array.from(document.querySelectorAll('*')).map(e => e.scrollHeight))")
            params["clip"] = {"x": 0, "y": 0, "width": 1440, "height": min(int(h or 900), 2600), "scale": 1}
        r = await self.call("Page.captureScreenshot", **params)
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"{name}.png").write_bytes(base64.b64decode(r["data"]))
        print("saved", name)

    async def click_text(self, text, selector="button"):
        return await self.js(f"""(() => {{ const b = Array.from(document.querySelectorAll('{selector}'))
            .find(e => e.innerText && e.innerText.includes({json.dumps(text)})); if (b) {{ b.click(); return true; }} return false; }})()""")

    async def goto(self, url, wait_text):
        await self.call("Page.navigate", url=url)
        await self.wait_text(wait_text, 60)
        await asyncio.sleep(4)


async def main():
    profile = tempfile.mkdtemp()
    chrome = subprocess.Popen([CHROME, "--headless=new", f"--remote-debugging-port={PORT}", f"--user-data-dir={profile}",
                               "--window-size=1440,900", "--hide-scrollbars", "about:blank"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):   # wait until Chrome accepts connections (the first start can be slow)
            try:
                tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json").read())
                break
            except OSError:
                await asyncio.sleep(0.5)
        ws = await websockets.connect(next(t for t in tabs if t["type"] == "page")["webSocketDebuggerUrl"], max_size=200 * 2**20)
        tab = Tab(ws)
        await tab.call("Page.enable")
        await tab.call("Emulation.setDeviceMetricsOverride", width=1440, height=900, deviceScaleFactor=2, mobile=False)
        base = "http://localhost:8501"
        await tab.goto(base, "Headline findings")
        await tab.shot("overview", full=False)
        await tab.goto(base + "/ask", "Run the pipeline")
        await tab.shot("ask_home", full=False)
        await tab.click_text("Run the pipeline")
        ok = await tab.wait_text("Context built in", 400)
        print("pipeline complete:", ok)
        await asyncio.sleep(3)
        await tab.js("window.scrollTo(0, 0)")
        await tab.js("""(() => { const el = document.querySelector('.fr-steps');
                         if (el) el.scrollIntoView({block: 'start'}); window.scrollBy(0, -90); })()""")
        await tab.shot("ask_result", full=False)
        for label in ["Code & trace", "Votes"]:
            print(label, await tab.click_text(label, "[role=tab]"))
            await asyncio.sleep(2)
            await tab.shot("ask_" + label.split()[0].lower(), full=False)
        for name, link, wait in [("results", "Results", 8), ("errors", "Errors", 6), ("compare", "Compare", 5),
                                 ("optimization", "Optimization", 5), ("robustness", "Robustness", 5)]:
            print(link, await tab.click_text(link, "a"))
            await asyncio.sleep(wait)
            await tab.shot(name, full=False)
            if name == "results":
                await tab.js("Array.from(document.querySelectorAll('*')).forEach(e => { if (e.scrollHeight > e.clientHeight + 100 && getComputedStyle(e).overflowY !== 'visible') e.scrollTop += 850; }); window.scrollBy(0, 850)")
                await tab.shot("results_2", full=False)
    finally:
        chrome.terminate()


if __name__ == "__main__":
    asyncio.run(main())
