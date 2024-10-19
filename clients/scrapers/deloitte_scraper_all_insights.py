import copy
from os import name
import os
from playwright.sync_api import sync_playwright
import requests
import pdfplumber
import urllib.parse

def scrape_deloitte_insights():
    with sync_playwright() as p:
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
        url_template = "https://www2.deloitte.com/us/en/insights/industry.html"
        # global industry 
        # industry = 'medical devices'
        # search_url_template = get_search_url(industry)
        paginate(url_template, context, data)
        browser.close()
        # for entry in data:
        #     print(entry["headline"])
        return data
    
# def get_search_url(industry):
#     # Encode the industry name to be used in the URL
#     encoded_industry = urllib.parse.quote(industry)
#     # Construct the search result page URL
#     return f"https://www2.deloitte.com/us/en/insights/searchresults.html?qr={encoded_industry}&page={{}}"

def paginate(url_template, context, data, start_page=1):
    page_number = start_page
    previous_results = None  # To store previous page results
    #search_headlines_dict = {}
    while True:
        # Format the URL with the current page number
        url = url_template
        # url = url_template.format(page_number)
        #print(f"Scraping page {page_number}: {url}")
        
        # Create a new page in the context for each result page
        page = context.new_page()
        for attempt in range(3):  # Retry up to 3 times
            try:
                page.goto(url, wait_until='networkidle')
                break  # Exit the loop if successful
            except Exception as e:
                print(f"Error loading page {page_number} on attempt {attempt + 1}: {e}")
        # # Check for HTTP status code directly in Playwright instead of using requests
        # response = page.goto(url)
        # if response.status != 200:
        #     print(f"Received status {response.status} for page {page_number}. Stopping pagination.")
        #     break
        
        # Process the page content
        search_page_headlines_dict = process_page(page)
        if not search_page_headlines_dict:
            print(f"No results on page {page_number}.")
        #print(search_headlines_dict)
        #print()
        #search_headlines_dict.update(search_page_headlines_dict)
        #print(search_headlines_dict)
        #print()
        # If it's the first page and no results are found, stop the process
        if page_number == 1 and not search_page_headlines_dict:
            print("No results found on page 1. Stopping.")
            break
        #print(f"Previous results: {previous_results}")
        #print(f"Current results: {search_headlines_dict}")
        prev_results_normalized = []
        current_results_normalized = []
        # Normalize and compare results to avoid false positives
        if previous_results is not None and int(page_number) != "1":
            # Convert dictionary keys to a sorted list and normalize strings for comparison
            prev_results_normalized = sorted([headline.lower().strip() for headline in previous_results])
            current_results_normalized = sorted([headline.lower().strip() for headline in search_page_headlines_dict])
            print(f"Normalized previous results: {prev_results_normalized}")
            print(f"Normalized current results: {current_results_normalized}")
            
            if prev_results_normalized == current_results_normalized:
                print(f"No new results or repeated results on page {page_number}. Stopping pagination.")
                break
        # Iterate through the headlines and process individual links
        for headline, headline_link in search_page_headlines_dict.items():
            process_headline(context, headline, headline_link, data, search_page_headlines_dict)
        # Make a deep copy of the current results to preserve them for the next iteration
        previous_results = copy.deepcopy(search_page_headlines_dict)
        page_number += 1
        page.close()
    
def process_page(page):
    search_page_headlines_dict = {}
    # Extracting headlines and links on the current page
    search_headlines = page.query_selector_all('.cmp-promo-tracking')

    for element in search_headlines:
            # Extract the 'data-promocontenttype' attribute
            content_type = element.get_attribute('data-promocontenttype')

            # Check if the content type is 'Article' or 'Interactive'
            if content_type in ['Article', 'Interactive']:
    #print(search_headlines)

    # Loop through the elements and extract the text and href attribute
                for headline in search_headlines:
                    text = headline.text_content().strip()  # Get the link text
                    end_url = headline.get_attribute('href')   # Get the href attribute
                    link = 'https://www2.deloitte.com' + end_url
                    print(f"Text: {text}, Link: {link}")    # Print both
                    if text and link:  # Ensure both text and href exist
                        search_page_headlines_dict[text] = link  # Use .strip() to remove extra whitespace
                
                return search_page_headlines_dict

def process_headline(context, headline, headline_link, data, search_page_headlines_dict):
    with context.new_page() as headline_link_page:
        is_pdf_redirected = False
        pdf_link = ''
        is_404_error = False 
        end_url = ''

        def handle_response(response):
            nonlocal is_pdf_redirected, pdf_link, is_404_error, end_url
            # Check for 404 error
            if response.status == 404:
                is_404_error = True
                print(f"404 error encountered for {headline_link}")

            # Check if the response is a PDF
            elif response.url.endswith('.pdf'):
                is_pdf_redirected = True
                pdf_link = response.url
                print("Intercepted PDF response:", pdf_link)       

        headline_link_page.on("response", handle_response)

        try:
            headline_link_page.goto(headline_link, wait_until='domcontentloaded')

            if is_404_error:
                # Extract the end_url from the original headline link
                end_url = headline_link.replace('https://www2.deloitte.com', '')
                # Construct the new link by prepending the correct base URL
                new_link = 'https://www2.deloitte.com/us/en/insights' + end_url
                print(f"Trying new link: {new_link}")

                # Attempt to navigate to the new link
                headline_link_page.goto(new_link, wait_until='domcontentloaded')

                # If the new link doesn't raise a 404, update the search_headlines_dict
                if not is_404_error:  # If no 404 after retry
                    print(f"Updated working link: {new_link}")
                    search_page_headlines_dict[headline] = new_link  # Update the dictionary with the new link

                raise Exception(f"404 Page Not Found for {headline_link}")
            
            headline_link_page_content = headline_link_page.content()
            entry = {"headline": headline, "link": search_page_headlines_dict[headline], "content": headline_link_page_content}

        except Exception as e:
            print(f"Error during page load for {headline}: {e}")
            if is_pdf_redirected and pdf_link:
                pdf_filename = f"{sanitise_filename(headline)}.pdf"
                download_pdf(pdf_link, pdf_filename)
                extracted_text = extract_text_from_pdf(pdf_filename)
                os.remove(pdf_filename)
                entry = {"headline": headline, "link": pdf_link, "content": extracted_text}
                
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
    
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

def sanitise_filename(text):
    return ''.join(c if c.isalnum() else '_' for c in text)[:50]

if __name__ == "__main__":
    data = scrape_deloitte_insights()