import copy
from os import name
import os
from playwright.sync_api import sync_playwright
import requests
import pdfplumber
import urllib.parse
import fitz  # PyMuPDF

def scrape_moodys_insights():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        #browser = p.firefox.launch(headless=True) 
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
            },
            {
                'name': 'OneTrustConsentShare_GLOBAL',
                'value': 'optboxclosed=true&optboxexpiry=2024-10-04T14:04:38.852Z&isGpcEnabled=0&datestamp=Fri+Oct+11+2024+16:26:30+GMT+0100+(British+Summer+Time)&version=202409.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=51304710-7c7d-4672-a80d-6cabc82a6c41&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=1:1,2:1,3:1,4:1&geolocation=GB&AwaitingReconsent=false',
                'domain': '.deloitte.com',
                'path': '/'
            }
        ])
        
        data = []
        url_template = "https://www.moodys.com/web/en/us/insights/all.html"
        # global industry 
        # industry = 'medical devices'
        # search_url_template = get_search_url(industry)
        paginate(url_template, context, data)
        browser.close()
        # for entry in data:
        #     print(entry["headline"])
        return data

def paginate(url_template, context, data, start_page=1):
    url = url_template
    page_number = start_page
    page = context.new_page()

    for attempt in range(3):  # Retry up to 3 times
        try:
            page.goto(url, wait_until='networkidle')
            break  # Exit the loop if successful
        except Exception as e:
            print(f"Error loading page {page_number} on attempt {attempt + 1}: {e}")

    while True:

        # Process the page content
        search_page_headlines_dict = process_page(page)

        # If no results are found, stop the process
        if not search_page_headlines_dict:
            print(f"No results found on page {page_number}. Stopping.")
            break

        # Iterate through the headlines and process individual links
        for headline, headline_link in search_page_headlines_dict.items():
            process_headline(context, headline, headline_link, data, search_page_headlines_dict)

        try:
            # Check if there is a "Next" button
            next_button = page.query_selector('a.btn.load-more-button')
            #next_button.scroll_into_view_if_needed()

            if next_button:
                print(f"Scraping page {page_number+1}")

                # Click the "Next" button
                next_button.click()

            else:
                    # No more pages, break the loop
                print("No more pages.")
                break

        except Exception as e:  
            print(f"An error occurred: {e}")

                    # Wait for the next page to load (you can use wait_for_selector for an element unique to the next page)
                    #page.wait_for_selector('.card-insight')


        page_number += 1
        page.close()


def process_page(page):
    search_page_headlines_dict = {}
    # Extracting headlines and links on the current page
    search_headlines = page.query_selector_all('.card-insight')

    #print(search_headlines)

    # Loop through the elements and extract the text and href attribute
    for headline in search_headlines:
        text = headline.query_selector('h5').inner_text().strip()  # Get the link text
        link_element = headline.query_selector('a.btn-quick-link')
        end_url = link_element.get_attribute('href').strip()   # Get the href attribute
        link = 'https://www.moodys.com' + str(end_url)
        print(f"Text: {text}, Link: {link}")    # Print both
        if text and link:  # Ensure both text and href exist
            search_page_headlines_dict[text] = link  # Use .strip() to remove extra whitespace
    
    return search_page_headlines_dict

def process_headline(context, headline, headline_link, data, search_page_headlines_dict):
    with context.new_page() as headline_link_page:
        is_pdf_redirected = False
        pdf_link = ''
        is_404_error = False 
        url = headline_link

        def handle_response(response):
            nonlocal is_pdf_redirected, pdf_link, is_404_error
            # Check for 404 error
            if response.status == 404 and response.url == url:
                is_404_error = True
                print(f"404 error encountered for {response.url}")

            # Check if the response is a PDF
            elif response.url.endswith('.pdf'):
                is_pdf_redirected = True
                pdf_link = response.url
                print("Intercepted PDF response:", pdf_link)       

        def handle_request_failure(request):
            nonlocal is_404_error
            # Handle request failures, such as NS_ERROR_UNKNOWNHOST
            if request.failure:  # Ensure failure object exists
                if "NS_ERROR_UNKNOWNHOST" in request.failure:
                    print(f"Request failed: {request.url} due to {request.failure}")
                elif request.failure == "net::ERR_ABORTED" and request.url == url:
                    is_404_error = True  # Consider it a 404 if the main URL fails to load

        headline_link_page.on("response", handle_response)
        headline_link_page.on("requestfailed", handle_request_failure)

        try:
            headline_link_page.goto(headline_link, wait_until='domcontentloaded')

            if is_404_error:
                # Extract the end_url from the original headline link
                url = headline_link.replace('https://www.moodys.com/', 'https://www.moodys.com/web/en/us/insights')
                    
                # Construct the new link by prepending the correct base URL
                #new_link = '' + end_url
                print(f"Trying new link: {url}")

                 # Reset 404 error flag
                is_404_error = False
                # Attempt to navigate to the new link
                headline_link_page.goto(url, wait_until='domcontentloaded')

                if is_404_error:
                    # Extract the end_url from the original headline link
                    url = headline_link.replace('https://www.moodys.com', '')
                    # Construct the new link by prepending the correct base URL
                    #new_link = '' + end_url
                    print(f"Trying further amended link: {url}")

                    # Reset 404 error flag
                    is_404_error = False
                    headline_link_page.goto(url, wait_until='domcontentloaded')

                    # If the new link doesn't raise a 404, update the search_headlines_dict
                    if not is_404_error:  # If no 404 after retry
                        is_404_error = False
                        print(f"Updated working link: {url}")
                        search_page_headlines_dict[headline] = url  # Update the dictionary with the new link
                    
                    else: 
                        raise Exception(f"404 Page Not Found after multiple retries for {headline_link}")
                
            headline_link_page_content = headline_link_page.content()
            entry = {"headline": headline, "link": search_page_headlines_dict[headline], "content": headline_link_page_content}

        except Exception as e:
            print(f"Error during page load for {headline}: {e}")

            if is_pdf_redirected and pdf_link:
                # Use Playwright's expect_download to handle PDF download
                try:
                    with pdf_link.expect_download() as download_info:
                        pdf_filename = f"{sanitise_filename(pdf_link)}"
                        print(pdf_filename)
                        #pdf_filename = f"{sanitise_filename(headline)}.pdf"
                        pdf_filename.wait_for_load_state('domcontentloaded')
                        pdf_filename.path(path=pdf_filename)

                        #headline_link_page.pdf(path=pdf_filename)
                        download = download_info.value

                        download.save_as(pdf_filename)
                        #download_pdf(pdf_link, pdf_filename)
                        extracted_text = extract_text_from_pdf(pdf_filename)
                        os.remove(pdf_filename)
                        entry = {"headline": headline, "link": pdf_filename, "content": extracted_text}

                except Exception as pdf_error:
                    print(f"Error while downloading or processing the PDF: {pdf_error}")
                    entry = {"headline": headline, "link": pdf_link, "message": "Error handling PDF"}

                
            elif is_404_error:
                entry = {"headline": headline, "link": headline_link, "message": "404 Page Not Found"}

            else:
                entry = {"headline": headline, "link": headline_link, "message": "No PDF was found or redirected."}

        data.append(entry) #saves after processing so data is captured even if script stops partway through 
        # for entry in data:
        #     print(entry["headline"])

def download_pdf(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            file.write(response.content)
        return save_path
    else:
        raise Exception(f"Failed to download PDF from {url}")
    
def extract_text_from_pdf(pdf_filename):
    text = ""
    with pdfplumber.open(pdf_filename) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

# def extract_text_from_pdf(pdf_filename):
#     text = ""
#     try:
#         # Open the PDF file
#         pdf_document = fitz.open(pdf_filename)
#         # Loop through each page
#         for page_num in range(pdf_document.page_count):
#             page = pdf_document.load_page(page_num)
#             text += page.get_text()  # Extract text from each page
#         pdf_document.close()  # Close the document after extraction
#     except Exception as e:
#         print(f"Error extracting text from {pdf_filename}: {e}")
#     return text

def sanitise_filename(text):
    parsed_url = urllib.parse.urlparse(text)
    pdf_filename = os.path.basename(parsed_url.path)
    return "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in text)[:50]

if __name__ == "__main__":
    data = scrape_moodys_insights()