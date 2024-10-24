import copy
from os import name
import os
from playwright.sync_api import sync_playwright
import requests
import pdfplumber

def scrape_moodys_insights():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
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
        
        data = []
        url_template = "https://www.moodys.com/web/en/us/insights/all.html"
    
        paginate(url_template, context, data)
        browser.close()

        return data

def paginate(url_template, context, data, start_page=1):
    url = url_template
    page_number = start_page
    scraped_urls = set()  # Set to store scraped URLs

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
            if headline_link not in scraped_urls:
                process_headline(context, headline, headline_link, data, search_page_headlines_dict)
                scraped_urls.add(headline_link)  # Add the URL to the set to avoid duplicates
            else:
                print(f"Skipping already processed URL: {headline_link}")

        try:
            # Ensure the next button is visible
            next_button = page.query_selector('a.btn.load-more-button')
            if next_button and next_button.is_visible():
                print(f"Scraping page {page_number + 1}")
                next_button.click()
                page.wait_for_load_state('networkidle')  # Wait for the new content to load
            else:
                # No more pages, break the loop
                print("No more pages.")
                break
            
            page_number += 1

        except Exception as e:  
            print(f"An error occurred during pagination on page {page_number}: {e}")

            # Retry if the error is related to page closure
            if "Target page, context or browser has been closed" in str(e):
                print("Reopening the page due to an unexpected close.")
                page = context.new_page()  # Reopen the page in case of unexpected close
                page.goto(url, wait_until='networkidle')
            else:
                break  # If it's not a page close error, exit the loop

    page.close()


def process_page(page):
    search_page_headlines_dict = {}
    # Extracting headlines and links on the current page
    search_headlines = page.query_selector_all('.card-insight')

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
        entry = {}

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
            nonlocal is_404_error, entry
            # Handle request failures, such as NS_ERROR_UNKNOWNHOST
            if request.failure:  # Ensure failure object exists
                if "NS_ERROR_UNKNOWNHOST" in request.failure:
                    print(f"Request failed: {request.url} due to {request.failure}")
                elif request.failure == "net::ERR_ABORTED" and request.url == url:
                    is_404_error = True  # Consider it a 404 if the main URL fails to load
                elif request.failure == "net::ERR_NAME_NOT_RESOLVED":
                    is_404_error = True  # Consider it a 404 if the main URL fails to load

        headline_link_page.on("response", handle_response)
        headline_link_page.on("requestfailed", handle_request_failure)

        try:
            headline_link_page.goto(headline_link, wait_until='domcontentloaded')

            if is_pdf_redirected and pdf_link:
                if is_404_error:
                    # Extract the end_url from the original headline link
                    pdf_link = pdf_link.replace('https://www.moodys.com', '')
                    # Construct the new link by prepending the correct base URL
                    #new_link = '' + end_url
                    print(f"Trying further amended link: {pdf_link}")

                    # Reset 404 error flag
                    is_404_error = False
                    
                # Use Playwright's expect_download to handle PDF download
                pdf_filename = sanitise_filename(pdf_link)
                print(pdf_filename)
                try:
                    download_pdf(pdf_link, pdf_filename)
               
                    extracted_text = extract_text_from_pdf(pdf_filename)
                    os.remove(pdf_filename)
                    entry = {"headline": headline, "link": pdf_filename, "content": extracted_text}

                except Exception as pdf_error:
                    print(f"Error while downloading or processing the PDF: {pdf_error}")
                    entry = {"headline": headline, "link": pdf_link, "message": "Error handling PDF"}

            elif is_404_error:
                # Extract the end_url from the original headline link
                url = headline_link.replace('https://www.moodys.com/', 'https://www.moodys.com/web/en/us/insights')
                    
                # Construct the new link by prepending the correct base URL
                print(f"Trying new link: {url}")

                # Reset 404 error flag
                is_404_error = False
                # Attempt to navigate to the new link
                headline_link_page.goto(url, wait_until='domcontentloaded')

                if is_404_error:
                    # Extract the end_url from the original headline link
                    url = headline_link.replace('https://www.moodys.com', '')
                    # Construct the new link by prepending the correct base URL
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
                        entry = {"headline": headline, "link": headline_link, "message": "404 Page Not Found"}
                        raise Exception(f"404 Page Not Found after multiple retries for {headline_link}")    
            else:
                # If no PDF detected and no 404, capture the page content (in case of HTML response)
                headline_link_page_content = headline_link_page.content()
                entry = {"headline": headline, "link": headline_link, "content": headline_link_page_content}

        except Exception as e:
            print(f"Error during page load for {headline}: {e}")
            entry = {"headline": headline, "link": headline_link, "message": str(e)}

        data.append(entry) #saves after processing so data is captured even if script stops partway through 

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

def sanitise_filename(text):
    #parsed_url = urllib.parse.urlparse(text)
    return "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in text)[:50]

if __name__ == "__main__":
    data = scrape_moodys_insights()