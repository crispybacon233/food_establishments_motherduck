import marimo

__generated_with = "0.23.1"
app = marimo.App(width="columns")


@app.cell
def _():
    import asyncio
    import re
    from urllib.parse import unquote

    from playwright.async_api import async_playwright
    from bs4 import BeautifulSoup


    return BeautifulSoup, async_playwright, re, unquote


@app.cell
def _(BeautifulSoup, re, unquote):
    async def get_coordinates(page):
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        a = soup.find("a", attrs={"aria-label": "Sign in"})
        if not a:
            return None, None

        href = a.get("href")
        if not href:
            return None, None

        decoded_href = unquote(href)

        match = re.search(r'@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)', decoded_href)
        if not match:
            return None, None

        return float(match.group(1)), float(match.group(2))

    return (get_coordinates,)


@app.cell
async def _(async_playwright, get_coordinates):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(
            f"https://www.google.com/maps/search/Burger King 13450 N US 183 HWY Svrd SB Austin TX",
            wait_until="domcontentloaded"
        )
    
        await page.wait_for_timeout(5000)
    
        try:
            coordinates = await get_coordinates(page)
    
        except Exception as e:
            print(f"{e}")
        await browser.close()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
