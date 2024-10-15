from os import name
import os
from playwright.sync_api import sync_playwright
import requests
import pdfplumber
#from ...utils.file_handler import save_to_json

def scrape_deloitte():
    with sync_playwright() as p:
        # Launch a headless browser

        #browser = p.chromium.launch(headless=False)
        browser = p.firefox.launch(headless=False) 

        # Create a new browser context with a custom User-Agent
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            extra_http_headers={
                'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
            },
            accept_downloads=True
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
        page = context.new_page()
        is_pdf_redirected = False
        pdfLink = ''
                # Listen for response events
        def handle_response(response):
            nonlocal is_pdf_redirected
            nonlocal pdfLink

            # Check if the response is a PDF
            if response.url.endswith('.pdf'):
                is_pdf_redirected = True  # Set flag to indicate PDF redirect

                print("Intercepted PDF response:", response.url)
                pdfLink = response.url
                # You can choose to handle the response here or ignore it
                # For instance, you could save the response to a file
                # with open('output.pdf', 'wb') as f:
                #     f.write(await response.body())
                

        page.on("response", handle_response)

        # def handle_request(route):
        #     if route.request.url.endswith('.pdf'):
        #         print("Intercepted PDF request:", route.request.url)
        #         # Optionally, you can respond with an empty response if you just want to log it
        #         route.abort()  # This aborts the PDF request
        #     else:
        #         route.continue_()

        #   # Create a new page
        # page = context.new_page()
        #page.on("route", handle_request)
            
        def handle_download(download):
            print(f"Download started: {download.url}")
            # Specify where to save the PDF file
            download_path = "downloaded_file.pdf"  # Change the name as needed
            download.save_as(download_path)
            print(f"PDF downloaded and saved as {download_path}")

        page.on("download", handle_download)
            # Optionally save the file if needed
            # download.save_as("path_to_save_file")

        # page.on("download", handle_download)

        # Navigate to the URL
        #page.goto("https://www2.deloitte.com/us/en/insights/industry/dcom/us-gps-crisis-contact-centers-2023.html")
        try:
            page.goto("https://www2.deloitte.com/us/en/insights/industry/dcom/us-gps-crisis-contact-centers-2023.html", wait_until='domcontentloaded')
            #page.goto("https://www2.deloitte.com/content/dam/Deloitte/us/Documents/public-sector/us-gps-crisis-contact-centers-2023.pdf")
        
        except Exception as e:
            print("Error during page load:", e)
            page.goto(pdfLink)

        if is_pdf_redirected:
            print("Aborting page navigation due to PDF response.")
            context.close()  # Close the context

        # Wait for a while to ensure the page loads
        #page.wait_for_timeout(5000)  # Wait for 5 seconds, adjust as needed

        # Extract content you need, e.g., page content
        content = page.content()
        print(content)
        # Navigate to the url
        # page.goto('https://www2.deloitte.com/us/en/insights.html')
        #response = page.goto('https://www2.deloitte.com/us/en/insights/industry/dcom/us-gps-crisis-contact-centers-2023.html')
        #print(response)
        #print(response.request.response())

        # # Wait for the page to load completely
        #page.wait_for_load_state('domcontentloaded')

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
        #page.wait_for_load_state('networkidle')


        #print("page loaded")

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

        data = []
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

        for headline, headlineLink in searchHeadlinesDict.items():
          with context.new_page() as headlineLinkPage:

            
            # is_pdf = False

            # def handle_response(response):
            #     nonlocal is_pdf
            #     if response.url == headlineLink:
            #         content_type = response.headers.get('content-type', '').lower()
            #         if 'application/pdf' in content_type:
            #             is_pdf = True

            # # Add the response listener before navigating to the page
            # headlineLinkPage.on('response', handle_response)

            # # Go to the link
            # headlineLinkPage.goto(headlineLink)

            # # Wait for the page to load fully
            # headlineLinkPage.wait_for_load_state('networkidle')

            # #headlineLinkPage.goto(headlineLink)

            sanitised_headline = sanitise_filename(headline)

            try:
                # Start waiting for a potential download
                # download_promise = headlineLinkPage.wait_for_event('download')

                # Navigate to the link
                #headlineLinkPage.route("**/*", handle_pdf_redirects)
                #headlineLinkPage.on("response", handle_response)
                headlineLinkPage.goto(headlineLink)
                
                print(f"url: {headlineLinkPage.url}")
                
                # Try catching a download event if it is triggered (e.g., PDF download)
                # download = download_promise.value
                # if download:
                #     print(f"Downloading PDF from: {headlineLink}")

                #     # Suggested filename from the download or sanitized headline
                #     pdf_filename = download.suggested_filename or f"{sanitised_headline}.pdf"
                #     pdf_filepath = f"/output/pdf/{pdf_filename}"
                #     print(f"pdf_filepath: {pdf_filepath}")
                #     # Save the downloaded file
                #     download.save_as(pdf_filepath)

                #     # Extract the text from the downloaded PDF
                #     extracted_text = extract_text_from_pdf(pdf_filepath)

                #     # Create an entry for this headline
                #     entry = {"headline": headline, "link": headlineLink, "content": extracted_text}

                #     # Optionally, delete the PDF after processing
                #     os.remove(pdf_filepath)

                # else:
                #     # If no download occurs, handle as a regular webpage
                #     headlineLinkPageContent = headlineLinkPage.content()
                #     entry = {"headline": headline, "link": headlineLink, "content": headlineLinkPageContent}
                headlineLinkPageContent = headlineLinkPage.content()
                entry = {"headline": headline, "link": headlineLink, "content": headlineLinkPageContent}

            except Exception as e:
                # If an error occurs or it's not a PDF link, handle regular webpage content scraping
                print(f"Error or non-download link for {headlineLink}: {e}")
                headlineLinkPage.goto(headlineLink)
                headlineLinkPageContent = headlineLinkPage.content()
                entry = {"headline": headline, "link": headlineLink, "content": headlineLinkPageContent}
                continue

            # if is_pdf:
            #     # Handle as a PDF
            #     print(f"Detected PDF: {headlineLink}")
            #     pdf_filename = f"{sanitised_headline}.pdf"
            #     download_pdf(headlineLink, pdf_filename)

            #     extracted_text = extract_text_from_pdf(pdf_filename)
            #     #text_filename = f"{sanitised_headline}.txt"
            #     #headlineLinkPageContent = extracted_text
            #     entry = {"headline": headline, "link": headlineLink, "content": extracted_text} 
            #     #entry["content"] = extracted_text
            #     os.remove(pdf_filename)  #delete the PDF after processing
            # else:
            #     # Handle regular webpage content scraping
            #     headlineLinkPage.goto(headlineLink)
            #     headlineLinkPageContent = headlineLinkPage.content()
            #     entry = {"headline": headline, "link": headlineLink, "content": headlineLinkPageContent}  # Create dictionary for webpage
            #     #entry["content"] = headlineLinkPageContent 
            
            data.append(entry) #saves after processing so data is captured even if script stops partway through 

            #save_to_json(entry, filename=f"output/{sanitised_headline}.json")            
            #print(headlineLinkPageContent)


        # Close the browser
        browser.close()
        # Return the scraped titles
        #return {"titles": article_titles, "content": searchPageContent}
        return data
    
def is_pdf_url(url):
    return url.lower().endswith('.pdf')
    
    # Function to download PDF file
def download_pdf(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            file.write(response.content)
        return save_path
    else:
        raise Exception(f"Failed to download PDF from {url}")
    
# Function to extract text from the PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

def sanitise_filename(text):
    return ''.join(c if c.isalnum() else '_' for c in text)[:50]  
    

async def handle_response(response):
    if response.status in [301, 302, 303, 307, 308]:
        print(f"Redirect detected from {response} with status {response.status}")
        #route.abort()
        # You could take action here like stopping further actions or re-routing
        
def handle_pdf_redirects(route, request):
    # Check if the new URL contains ".pdf"
    if request.redirected_from:
        print(f"Blocking redirect from {request.redirected_from.url} to {request.url}")
        route.abort()  # Abort the redirect
    if ".pdf" in request.url:
        print(f"Blocking redirect to: {request.url}")
        route.abort()  # Abort the request to prevent the redirect
    else:
        route.continue_()


if __name__ == "__main__":
    data = scrape_deloitte()
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