# Midscene Python SDK

AI-powered UI automation for Web, Android, and iOS.

## Installation

```bash
pip install midscene
```

## Quick Start

```python
import asyncio
from midscene.web.playwright import PlaywrightAgent

async def main():
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('https://example.com')
        
        agent = PlaywrightAgent(page)
        
        # Use AI to interact with the page
        await agent.ai_tap('click the main heading')
        
        # Query data from the page
        title = await agent.ai_query('What is the page title?')
        print(f"Title: {title}")
        
        await browser.close()

asyncio.run(main())
```

## Features

- **AI-Powered Automation**: Use natural language to describe actions
- **Multiple Platforms**: Support for Web (Playwright), Android, and iOS
- **Data Extraction**: Extract structured data from UI
- **YAML Scripting**: Write automation scripts in YAML format
- **Caching**: Replay scripts with cache for efficiency

## Documentation

See [https://midscenejs.com/](https://midscenejs.com/) for full documentation.

## License

MIT License
