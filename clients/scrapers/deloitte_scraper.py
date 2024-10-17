from os import name
import os
from playwright.sync_api import sync_playwright
import requests
import pdfplumber
import urllib.parse

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
            },
            accept_downloads=True
        )
        context.add_cookies([
            {
                'name': 'OptanonAlertBoxClosed',
                'value': '2024-10-15T19:15:21.618Z',
                'domain': '.www2.deloitte.com',
                'path': '/us/'
            },
            {
                'name': 'OptanonConsent',
                'value': 'interactionCount=0&datestamp=Thu+Oct+17+2024+22%3A03%3A44+GMT%2B0100+(British+Summer+Time)&version=202210.1.0&isGpcEnabled=0&geolocation=GB&isIABGlobal=false&hosts=&consentId=2f5eedc6-c1c5-4d6e-929a-5dedc11004be&landingPath=NotLandingPage&AwaitingReconsent=false&groups=1%3A1%2C2%3A0%2C3%3A0%2C4%3A0',
                'domain': '.www2.deloitte.com',
                'path': '/us/'
            }
        ])
        
        data = []

        industry = 'medical devices'
        searchResultPageUrl = get_search_result_page(industry)

        paginate(searchResultPageUrl, context, data)
    
        browser.close()

        return data

def get_search_result_page(industry):
    # Encode the industry name to be used in the URL
    encoded_industry = urllib.parse.quote(industry)

    # Construct the search result page URL
    search_url = f"https://www2.deloitte.com/us/en/insights/searchresults.html?qr={encoded_industry}&page={{}}"
    
    return search_url


def paginate(searchResultPageUrl, context, data, start_page=1):
    page_number = start_page
    previous_results = None  # To store previous page results
    #searchPageHeadlinesDict = {}
    searchHeadlinesDict = {}

    while True:
        # Format the URL with the current page number
        url = searchResultPageUrl.format(page_number)
        
        # Create a new page in the context for each result page
        page = context.new_page()
        page.goto(url, wait_until='domcontentloaded')

        # # Check for HTTP status code directly in Playwright instead of using requests
        # response = page.goto(url)
        # if response.status != 200:
        #     print(f"Received status {response.status} for page {page_number}. Stopping pagination.")
        #     break
        
        # Process the page content
        searchPageHeadlinesDict = process_page(page)
        #print(f"Headlines found on page {page_number}: {searchPageHeadlinesDict}")
        searchHeadlinesDict.update(searchPageHeadlinesDict)

        # If it's the first page and no results are found, stop the process
        if page_number == 1 and not searchHeadlinesDict:
            print("No results found on page 1. Stopping.")
            break

        # If no results or repeated results on subsequent pages, stop pagination
        if previous_results is not None and page_number != 1 and previous_results == searchHeadlinesDict:
            print(f"No new results or repeated results on page {page_number}. Stopping pagination.")
            break

        # Update the main dictionary with results from the current page
        #searchHeadlinesDict.update(searchPageHeadlinesDict)

        # if not searchHeadlinesDict:  # No results found on the current page
        #     print(f"No results on page {page_number}. Stopping pagination.")
        #     break

        # # Check if the results are the same as the previous page's results
        # if previous_results == searchHeadlinesDict:
        #     print(f"Repeated results on page {page_number}. Stopping pagination.")
        #     break

        # Iterate through the headlines and process individual links
        for headline, headlineLink in searchHeadlinesDict.items():
            process_headline(context, headline, headlineLink, data)

        previous_results = searchHeadlinesDict

        page_number += 1
        page.close()

    
def process_page(page):
    # Extracting headlines and links on the current page
    searchHeadlines = page.query_selector_all('.cmp-di-search-list__headline.cmp-di-search__headline > a')
    searchHeadlinesDict = {}

    # Loop through the elements and extract the text and href attribute
    for headline in searchHeadlines:
        text = headline.text_content().strip()  # Get the link text
        link = 'https://www2.deloitte.com/' + headline.get_attribute('href')   # Get the href attribute
        print(f"Text: {text}, Link: {link}")    # Print both
        if text and link:  # Ensure both text and href exist
            searchHeadlinesDict[text] = link  # Use .strip() to remove extra whitespace
    
    return searchHeadlinesDict


def process_headline(context, headline, headlineLink, data):
    with context.new_page() as headlineLinkPage:
        is_pdf_redirected = False
        pdfLink = ''

        def handle_response(response):
            nonlocal is_pdf_redirected, pdfLink
            # Check if the response is a PDF
            if response.url.endswith('.pdf'):
                is_pdf_redirected = True
                pdfLink = response.url
                print("Intercepted PDF response:", pdfLink)               

        headlineLinkPage.on("response", handle_response)

        try:
            headlineLinkPage.goto(headlineLink, wait_until='domcontentloaded')
            headlineLinkPageContent = headlineLinkPage.content()
            entry = {"headline": headline, "link": headlineLink, "content": headlineLinkPageContent}

        except Exception as e:
            print(f"Error during page load for {headline}: {e}")
            if is_pdf_redirected and pdfLink:
                pdf_filename = f"{sanitise_filename(headline)}.pdf"
                download_pdf(pdfLink, pdf_filename)
                extracted_text = extract_text_from_pdf(pdf_filename)
                os.remove(pdf_filename)
                entry = {"headline": headline, "link": pdfLink, "content": extracted_text}
            else:
                entry = {"headline": headline, "link": headlineLink, "message": "No PDF was found or redirected."}

        data.append(entry) #saves after processing so data is captured even if script stops partway through 

def download_pdf(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            file.write(response.content)
        return save_path
    else:
        raise Exception(f"Failed to download PDF from {url}")
    

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text


def sanitise_filename(text):
    return ''.join(c if c.isalnum() else '_' for c in text)[:50]



if __name__ == "__main__":
    data = scrape_deloitte()