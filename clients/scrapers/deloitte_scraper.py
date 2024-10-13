from os import name
from playwright.sync_api import sync_playwright

def scrape_deloitte():
    with sync_playwright() as p:
        # Launch a headless browser

        #browser = p.chromium.launch(headless=False)
        browser = p.firefox.launch(headless=True) 

        # Create a new browser context with a custom User-Agent
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            extra_http_headers={
                'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
            }
        )
        context.add_cookies([
            # {
            #     'name': 'QSI_HistorySession',
            #     'value': 'https%3A%2F%2Fwww2.deloitte.com%2Fus%2Fen%2Finsights%2Fsearchresults.html%3Fqr%3Dmedical%2520devices~1728822647197',
            #     'domain': 'www2.deloitte.com',
            #     'path': '/'
            # },
            {
                'name': 'OptanonAlertBoxClosed',
                'value': '2024-10-13T12:30:45.330Z',
                'domain': '.www2.deloitte.com',
                'path': '/us/'
            },
            {
                'name': 'OptanonConsent',
                'value': 'isGpcEnabled=0&datestamp=Sun+Oct+13+2024+13%3A30%3A45+GMT%2B0100+(British+Summer+Time)&version=202210.1.0&isIABGlobal=false&hosts=&consentId=0a2e18e1-9824-4a41-9bd8-f255669898ec&interactionCount=1&landingPath=NotLandingPage&groups=1%3A1%2C2%3A1%2C3%3A1%2C4%3A1&geolocation=GB%3BNIR&AwaitingReconsent=false',
                'domain': '.www2.deloitte.com',
                'path': '/us/'
            }
        ])
        
        # Open a new page in the context
        #page = context.new_page()

        # Navigate to the url
        # page.goto('https://www2.deloitte.com/us/en/insights.html')


        # # Wait for the page to load completely
        # page.wait_for_load_state('domcontentloaded')

        # # Handle the cookies popup by clicking the "Accept" button
        # # Use query selector to target the button
        # try:
        #     # Modify the selector according to the page's button (you can use text, CSS class, or button role)
        #     page.locator("text=Accept optional cookies").click(force=True)  # Or use other methods like query_selector or text content
        #     print("Accepted the cookies popup")
        # except Exception as e:
        #     print(f"Could not find the 'Accept' button: {e}")

        # # Click on the search button to make the search bar visible
        # page.click('.cmp-di-header__action-item.cmp-di-header__search')
    

        #  # Find the search bar and enter the search query
        # page.fill('.cmp-di-search__input', 'medical devices')

        # # Press 'Enter' to submit the search
        # page.keyboard.press('Enter')

        # # Wait for the results to load (adjust the wait time if necessary)
        # page.wait_for_load_state('networkidle')


        # # page.evaluate('''() => {
        # #     Object.defineProperty(navigator, 'webdriver', { get: () => false });
        # # }''')

        # searchResultUrl = page.url
        # print(searchResultUrl)
        searchResultPage = context.new_page()
        #searchResultPage.goto(searchResultUrl)
        searchResultPage.goto('https://www2.deloitte.com/us/en/insights/searchresults.html?qr=medical%20devices')

        # Wait for the modal to be visible
        #page.wait_for_selector('.ot-sdk-container', state='visible', timeout=10000)  # Wait for the modal to be visible


        #page.wait_for_selector('.onetrust-accept-btn-handler', state='visible', force=True)
        #page.click('.onetrust-accept-btn-handler')

        # Wait for the page to load completely
        #page.wait_for_load_state('domcontentloaded')

        #page.click('button.accept-cookies-selector')

        # Wait for the modal and "Accept" button to be visible
        # try:
        #     # Wait for the modal to appear and locate the button
        #     page.wait_for_selector("button.onetrust-accept-button-handler", timeout=5000)  # Use the actual selector for the "Accept" button
        #     print("Accepted the cookies popup")

        #     page.click("onetrust-accept-btn-handler")  # Clicking the "Accept" button
        #     print("Accepted the cookies popup")
        # except Exception as e:
        #     print(f"Error handling the modal: {e}")
        #page.goto('https://www.deloitte.com/global/en/Industries/automotive.html')
        #page.goto('https://www2.deloitte.com/us/en/insights/industry/technology/digital-media-trends-consumption-habits-survey.html#key-themes')
        #print(page)
        # Wait to load
        #page.wait_for_selector('.cmp-title__text')   
        #page.wait_for_selector('.insight-card__headline')

        #if need to simulate scrolling to get all content
        #page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

        # Scrape titles
        #articles = page.query_selector_all('.insight-card__headline')
        #searchPageContent = searchResultPage.content()
        

        # Wait for the headline elements to load on the page
        #page.wait_for_selector('.cmp-di-search-list')
        #searchHeadlines = searchResultPage.query_selector_all('#cmp-di-search-page > div.aem-Grid.aem-Grid--10 > div > div > div > ds-is-results-list > ul > li:nth-child(2) > ds-is-insight > div.cmp-di-search-list__content.cmp-di-search-list__content-profile > h2 > a')
        #searchHeadlines = searchResultPage.query_selector_all('#cmp-di-search-page > div.aem-Grid.aem-Grid--10 > div > div > div > ds-is-results-list > ul > li:nth-child(2) > ds-is-insight > div.cmp-di-search-list__content.cmp-di-search-list__content-profile > h2 > a')
        #<h2 class="cmp-di-search-list__headline cmp-di-search__headline"><a href="/us/en/insights/industry/technology/technology-media-and-telecom-predictions/2022/wearable-technology-healthcare.html">Wearable technology in health care</a></h2>
        #print(searchPageContent)
        searchHeadlines = searchResultPage.query_selector_all('.cmp-di-search-list__headline.cmp-di-search__headline > a')
        #print(f"{searchHeadlines}")
        # links = searchResultPage.get_attribute('href', "results") 
        # for link in links:
        #     print(f"Link: {link}")



        # for headline in searchHeadlines:
        #     print(headline.text_content().strip()) 
        # searchHeadlinesText = [headline.inner_text() for headline in searchHeadlines]
        # print(searchHeadlinesText)
        # searchHeadlinesText = [searchHeadline.inner_text() for searchHeadline in searchHeadlines]
        # print(searchHeadlinesText)tio
        #article_titles = [article.inner_text() for article in articles]
        #articles = page.query_selector_all('title')
        #article_titles = [article.inner_text() for article in articles]



        searchHeadlinesDict = {}
        # Loop through the elements and extract the text and href attribute
        for headline in searchHeadlines:
            #print(headline)
            text = headline.text_content().strip()  # Get the link text
            link = 'https://www2.deloitte.com/' + headline.get_attribute('href')   # Get the href attribute
            print(f"Text: {text}, Link: {link}")    # Print both
            if text and link:  # Ensure both text and href exist
                searchHeadlinesDict[text] = link  # Use .strip() to remove extra whitespace

        #print(searchHeadlinesDict)

        for headlineLink in searchHeadlinesDict.values():
            headlineLinkPage = context.new_page()
            headlineLinkPage.goto(headlineLink)
            headlineLinkPageContent = headlineLinkPage.content()
            print(headlineLinkPageContent)


        # Close the browser
        browser.close()
        # Return the scraped titles
        #return {"titles": article_titles, "content": searchPageContent}
        return {"headlines": searchHeadlinesDict}
    

    

if __name__ == "__main__":
    #data = scrape_deloitte()
    #print("Scraped Articles:")
    #Loop through the elements and extract the text and href attribute
    # for headline in searchHeadlinesDict:
    #     #print(headline)
    #     text = headline.text_content().strip()  # Get the link text
    #     link = headline.get_attribute('href')   # Get the href attribute
    #     print(f"Text: {text}, Link: {link}")    # Print both
    # for articles in data:
    #     print(articles)
    # print("Search Headlines:")
    # for searchHeadlines in data:
    #     print(searchHeadlines)
    # print("Scraped Article Titles:")
    # for article_titles in data:
    #     print(article_titles)
    #print("Scraped Page:")
    #for pageContent in data:
    #    print(pageContent)
