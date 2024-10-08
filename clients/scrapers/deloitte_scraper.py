from playwright.sync_api import sync_playwright

def scrape_deloitte():
    with sync_playwright() as p:
        # Launch a headless browser

        browser = p.chromium.launch()

        # Create a new browser context with a custom User-Agent
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            extra_http_headers={
                'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
            }
        )
        
        # Open a new page in the context
        page = context.new_page()

        # Navigate to the url
        #page.goto('https://www.deloitte.com/global/en/Industries/automotive.html')
        page.goto('https://www2.deloitte.com/us/en/insights/industry/technology/digital-media-trends-consumption-habits-survey.html#key-themes')
        print(page)
        # Wait to load
        #page.wait_for_selector('.cmp-title__text')
        page.content()
        #page.wait_for_selector('.insight-card__headline')

        #if need to simulate scrolling to get all content
        #page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

        # Scrape titles
        #articles = page.query_selector_all('.insight-card__headline')
        pageContent = page.content()
        #articles = page.query_selector_all('.cmp-title__text')
        #article_titles = [article.inner_text() for article in articles]
        articles = page.query_selector_all('title')
        article_titles = [article.inner_text() for article in articles]

        # Close the browser
        browser.close()

        # Return the scraped titles
        return {"titles": article_titles, "content": pageContent}

if __name__ == "__main__":
    data = scrape_deloitte()
    print("Scraped Articles:")
    for articles in data:
        print(articles)
    # print("Scraped Article Titles:")
    # for article_titles in data:
    #     print(article_titles)
    #print("Scraped Page:")
    #for pageContent in data:
    #    print(pageContent)
