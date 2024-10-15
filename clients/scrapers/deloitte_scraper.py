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
        
        is_pdf_redirected = False
        pdfLink = ''

        searchResultPage = context.new_page()
        industry = 'medical devices'
        searchResultPageUrl = get_search_result_page(industry)
        searchResultPage.goto(searchResultPageUrl)

        #searchHeadlines = searchResultPage.query_selector_all('.cmp-di-search-list__headline.cmp-di-search__headline > a')

        data = []
        searchHeadlinesDict = {}


        def process_page():
            # Extracting headlines and links on the current page
            searchHeadlines = searchResultPage.query_selector_all('.cmp-di-search-list__headline.cmp-di-search__headline > a')

            # Loop through the elements and extract the text and href attribute
            for headline in searchHeadlines:
                #print(headline)
                text = headline.text_content().strip()  # Get the link text
                link = 'https://www2.deloitte.com/' + headline.get_attribute('href')   # Get the href attribute
                print(f"Text: {text}, Link: {link}")    # Print both
                if text and link:  # Ensure both text and href exist
                    searchHeadlinesDict[text] = link  # Use .strip() to remove extra whitespace

        process_page()  # Process the first page

        #PAGINATION DOESN'T WORK - POSSIBLY JUST ADD PAGE NO TO  SEARCHHEADLINES
        # Pagination loop
        while True:
            try:
                # Find all pagination buttons
                pagination_buttons = searchResultPage.query_selector_all('#cmp-di-search-pagination > ul > li:nth-child(2) > button')

                # if not pagination_buttons:
                #     print("No more pagination buttons found.")
                #     break

                # for idx, button in enumerate(pagination_buttons):
                #     button_text = button.text_content().strip()

                #     if "Next" in button_text or button_text.isdigit():  # Either a page number or the Next button
                #         try:
                #             print(f"Navigating to page {button_text}...")
                #             button.click()
                #             searchResultPage.wait_for_load_state('domcontentloaded')

                #             process_page()  # Process the new page

                #             # After loading a new page, re-fetch the pagination buttons again
                #             pagination_buttons = searchResultPage.query_selector_all('#cmp-di-search-pagination > ul > li > button')

                #         except Exception as e:
                #             print(f"Error navigating to page {button_text}: {e}")
                #             break  # Stop looping if an error occurs

                # # If no buttons are found after a page is processed, break the loop
                # if not pagination_buttons:
                #     break


                # Loop through each pagination button
                for idx, button in enumerate(pagination_buttons):
                    try:
                        # Extract the page number or text from the button
                        button_text = button.text_content().strip()
                        print(f"Navigating to page {button_text}...")

                        # Click the pagination button
                        button.click()
                        searchResultPage.wait_for_load_state('domcontentloaded')

                        # Process the content on the new page
                        process_page()

                    except Exception as e:
                        print(f"Error navigating to page {idx + 1}: {e}")
                        break  # Stop looping if an error occurs

                #If there's no more button or pagination, break the loop
                if not pagination_buttons:
                    break

            except Exception as e:
                print(f"Error during pagination: {e}")
                break  # Exit the loop if there's an error during pagination


            #print(searchHeadlinesDict)

        for headline, headlineLink in searchHeadlinesDict.items():
            with context.new_page() as headlineLinkPage:

                # Listen for response events
                def handle_response(response):
                    nonlocal is_pdf_redirected
                    nonlocal pdfLink

                    # Check if the response is a PDF
                    if response.url.endswith('.pdf'):
                        is_pdf_redirected = True  # Set flag to indicate PDF redirect
                        pdfLink = response.url  
                        print("Intercepted PDF response:", pdfLink)               

                headlineLinkPage.on("response", handle_response)

                try:
                    headlineLinkPage.goto(headlineLink, wait_until='domcontentloaded')
                    print(f"url: {headlineLinkPage.url}")

                    headlineLinkPageContent = headlineLinkPage.content()
                    #print(headlineLinkPageContent)
                    entry = {"industry": industry, "headline": headline, "link": headlineLink, "content": headlineLinkPageContent}

                except Exception as e:
                    print(f"Error during page loadfor {headline}: {e}")
                    #headlineLinkPage.goto(pdfLink)

                    if is_pdf_redirected and pdfLink:
                        print(f"PDF found, redirecting to {pdfLink}")
                        pdf_filename = f"{sanitise_filename(headline)}.pdf"
                        # Download the PDF using requests
                        download_pdf(pdfLink, pdf_filename)

                        extracted_text = extract_text_from_pdf(pdf_filename)
                        os.remove(pdf_filename)  #delete the PDF after processing

                        entry = {"industry": industry, "headline": headline, "link": pdfLink, "content": extracted_text} 
                    
                    else:
                        entry = {"industry": industry, "headline": headline, "link": headlineLink, "message": "No PDF was found or redirected."}
            
            data.append(entry) #saves after processing so data is captured even if script stops partway through 

        # Close the browser
        browser.close()
        # Return the scraped titles
        #return {"titles": article_titles, "content": searchPageContent}
        return data
       


def get_search_result_page(industry):
    # Encode the industry name to be used in the URL
    encoded_industry = urllib.parse.quote(industry)

    # Construct the search result page URL
    search_url = f"https://www2.deloitte.com/us/en/insights/searchresults.html?qr={encoded_industry}"

    # Simulate the searchResultPage.goto action
    print(f"searchResultPage.goto('{search_url}')")

    # Optionally return the URL if needed
    return search_url

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