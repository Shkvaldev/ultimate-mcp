import json
import asyncio
from loguru import logger
from urllib.parse import urlencode
from playwright.async_api import Playwright, async_playwright, Route, Request, Response
from playwright_stealth import Stealth

def extract_queries(data):
    try:
        return [keyword['query'] 
                for ranked_list in data['default']['rankedList'] 
                for keyword in ranked_list['rankedKeyword']]
    except Exception as e:
        logger.error("Failed to extract queries, skipping ...")

async def get_related_queries_trends(
        query: str,
        date: str = "today 1-m",
        geo: str = "RU",
        hl: str = "ru-RU",
        gprop: str = "youtube"
    ):
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.connect("ws://127.0.0.1:3000/")
        
        context = await browser.new_context()
        page = await context.new_page()

        intercepted_data = [None] 
        data_received = asyncio.Event()

        async def handle_route(route: Route):
            """Intercepts network requests."""
            request = route.request
            if "trends.google.com/trends/api/widgetdata/relatedsearches" in request.url:
                logger.debug(f"Intercepting request: {request.url}")
                
                await route.continue_()
                
                try:
                    response: Response = await request.response()
                    if response and response.status == 200:
                        response_text = await response.text()
                        
                        if response_text.startswith(")]}',\n"):
                            json_text = response_text[6:]
                        else:
                            json_text = response_text
                        
                        data = json.loads(json_text)
                        logger.debug("Successfully parsed JSON response.")
                        
                        intercepted_data[0] = data
                        data_received.set()
                    else:
                        logger.warning(f"Request failed or no successful response. Status: {response.status if response else 'No Response'}")
                except Exception as e:
                    logger.error(f"Error processing intercepted response: {e}")
            else:
                await route.continue_()

        await context.route("**/*", handle_route)

        try:
            await page.goto("https://google.com", wait_until="networkidle")

            params = {
                'q': query,
                'date': date,
                'geo': geo,
                'hl': hl,  
                'gprop': gprop
            }
            url = f"https://trends.google.com/trends/explore?{urlencode(params)}"
            logger.debug(f"Exploring Trends URL: {url}")

            await page.goto(url, wait_until="networkidle")
            
            await asyncio.wait_for(data_received.wait(), timeout=30.0) 
            logger.info("Data successfully intercepted and processed.")
            
            return extract_queries(intercepted_data[0]) 

        except asyncio.TimeoutError:
            logger.error("Timeout: Did not receive the expected API response within the time limit.")
            return None
        except Exception as e:
            logger.error(f"An error occurred during page interaction: {e}")
            return None
        finally:
            await context.close()
            await browser.close()
            logger.debug("Browser context and connection closed.")
