import copy
from os import name
import os
from playwright.sync_api import sync_playwright
import requests
import pdfplumber
import urllib.parse
import fitz  # PyMuPDF



def scrape_mckinsey_insights():
        # Launch browser for further scraping
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            extra_http_headers={
                'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
            },
            accept_downloads=True
        )
    # Initialize an empty dictionary for storing headline URLs
    search_page_headlines_dict = {}
    has_next = True
    next_cursor = ''
    data = []

    industry_links = get_industry_links()

#get referer in

    # Fetch URLs via API calls until there's no more data
    while has_next:
        try:
            has_next, next_cursor, search_page_headlines_dict = make_api_call(referer, has_next, next_cursor, search_page_headlines_dict)
        except Exception as e:
            print(f"Error fetching URLs from API: {e}")
            return []
        
    for headline, headline_link in search_page_headlines_dict.items():
        process_headline(context, headline, headline_link, data, search_page_headlines_dict)

    browser.close()
    return data

def get_industry_links():
    industry_links = {}
    base_url = "https://www.mckinsey.com"
    industries_url = f"{base_url}/industries"
    page = context.new_page()
    page.goto(industries_url, wait_until='domcontentloaded')

    # Scrape all industry links
    industry_link_elements = page.query_selector_all('a[href^="/industries/"]')
    
    for element in industry_link_elements:
        industry_name = element.inner_text()
        industry_href = element.get_attribute('href')
        if industry_name and industry_href:
            full_url = f"{base_url}{industry_href}"
            industry_links[industry_name.strip()] = full_url
            print(industry_links)

    browser.close()
    
    return industry_links



 



def make_api_call(referer, has_next, next_cursor, search_page_headlines_dict):

    url = "https://prd-api.mckinsey.com/api/insightsgrid/articles"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.mckinsey.com",
        "Referer": referer,  # Dynamically updating the Referer header
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }

    payload = {
        "limit": 1000,
        "afterId": next_cursor,
        "taxonomyAndTags": {
            "taxonomyQueryType": "OR",
            "taxonomyIds": ["7aa6f280-7392-4ef0-94af-f5ca6b805f81", "a78d0556-eff0-44b8-8e5e-339f9f600f1d"],
            "mustHaveTagsQueryType": "OR",
            "mustHaveTags": ["91cfe105-8dad-437c-8734-3d740dcdb437", "887e7cb2-191e-44d5-9ec6-de040b312a25", "a9103a6d-6663-4a30-bf78-9927d74f5df5", "21dc6bd4-9b9a-4de0-a9b8-71f68efef898", "c3f331dd-6683-4c33-9460-e56bb1487f33", "13f7e352-920f-4dd2-9a31-f2c3314eb405", "fa4bb8d5-ea76-4dd9-9530-2c865a87d5e0", "83cf99bc-d256-4e4c-a1bf-d0698ec601e9", "c5b24078-44cd-435c-b265-4e36593a226c"],
            "mustNotHaveTagsQueryType": "OR",
            "mustNotHaveTags": ["a65a9603-c09a-489f-9d77-4afd71c629b3"]
        },
        "excludeItems": ["e0e9832c-72b0-469e-b439-1fb7da310249", "aeee10e3-34a4-4fc9-8770-88856b9df8e4", "0f3d061b-bf1c-4cae-9d1c-21a35459bcf3", "71be4890-0806-43df-af8b-6ee067c9a198", "c23f199c-28df-4102-9a1a-900608064a08", "2072397b-689f-44c3-809c-4652d8a563c8", "c50a56bf-83fe-4fd2-af5c-fed8869c68ee", "b1484c69-6031-49ad-a36f-8a19933c5478"],
        "language": "en",
        "isAlumni": False,
        "filters": []
    }

    print("starting API call")
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()  # This will raise an exception for 4xx or 5xx status codes    
    print(response.status_code)

    if response.status_code == 200:
        data = response.json()
        #print(data)
        posts = data.get('posts', [])
        has_next = data.get('hasNext')
        next_cursor = data.get('nextCursor')
        
        for post in posts:
            title = post.get('title')
            article_url = post.get('url')
            
            if title and article_url:
                full_url = f"https://www.mckinsey.com{article_url}"  # Complete the URL
                search_page_headlines_dict[title] = full_url  # Store title and URL in dictionary

                print(f"Title: {title}")
                print(f"URL: {full_url}")
                print(f"nextCursor: {next_cursor}")
                print("---")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
    
    return has_next, next_cursor, search_page_headlines_dict

    
        
def process_headline(context, headline, headline_link, data, search_page_headlines_dict):
    with context.new_page() as headline_link_page:
        is_pdf_redirected = False
        pdf_link = ''
        is_404_error = False
        entry = {}

        def handle_response(response):
            nonlocal is_pdf_redirected, pdf_link, is_404_error
            if response.status == 404 and response.url == headline_link:
                is_404_error = True
                print(f"404 error encountered for {response.url}")
            elif response.url.endswith('.pdf'):
                is_pdf_redirected = True
                pdf_link = response.url
                print("Intercepted PDF response:", pdf_link)

        headline_link_page.on("response", handle_response)

        try:
            headline_link_page.goto(headline_link, wait_until='domcontentloaded')

            if is_pdf_redirected and pdf_link:
                try:
                    pdf_filename = sanitise_filename(pdf_link)
                    download_pdf(pdf_link, pdf_filename)
                    extracted_text = extract_text_from_pdf(pdf_filename)
                    os.remove(pdf_filename)
                    entry = {"headline": headline, "link": pdf_filename, "content": extracted_text}
                except Exception as pdf_error:
                    print(f"Error while downloading or processing the PDF: {pdf_error}")
                    entry = {"headline": headline, "link": pdf_link, "message": "Error handling PDF"}
            elif is_404_error:
                entry = {"headline": headline, "link": headline_link, "message": "404 Page Not Found"}
            else:
                headline_link_page_content = headline_link_page.content()
                entry = {"headline": headline, "link": headline_link, "content": headline_link_page_content}

        except Exception as e:
            print(f"Error during page load for {headline}: {e}")
            entry = {"headline": headline, "link": headline_link, "message": str(e)}

        data.append(entry)


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
    parsed_url = urllib.parse.urlparse(text)
    return "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in text)[:50]


if __name__ == "__main__":
    data = scrape_mckinsey_insights()
        
# def scrape_mckinsey_insights():
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)
#         #browser = p.firefox.launch(headless=True) 
#         # Create a new browser context with a custom User-Agent
#         context = browser.new_context(
#             user_agent='Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
#             extra_http_headers={
#                 'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
#                 'Accept-Encoding': 'gzip, deflate, br, zstd',
#                 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
#             },
#             accept_downloads=True
#         )
#         # context.add_cookies([
#         #     {
#         #         'name': 'OptanonAlertBoxClosed',
#         #         'value': '2024-10-15T19:15:21.618Z',
#         #         'domain': '.www2.deloitte.com',
#         #         'path': '/us/'
#         #     },
#         #     {
#         #         'name': 'OptanonConsent',
#         #         'value': 'interactionCount=0&datestamp=Thu+Oct+17+2024+22%3A03%3A44+GMT%2B0100+(British+Summer+Time)&version=202210.1.0&isGpcEnabled=0&geolocation=GB&isIABGlobal=false&hosts=&consentId=2f5eedc6-c1c5-4d6e-929a-5dedc11004be&landingPath=NotLandingPage&AwaitingReconsent=false&groups=1%3A1%2C2%3A0%2C3%3A0%2C4%3A0',
#         #         'domain': '.www2.deloitte.com',
#         #         'path': '/us/'
#         #     },
#         #     {
#         #         'name': 'OneTrustConsentShare_GLOBAL',
#         #         'value': 'optboxclosed=true&optboxexpiry=2024-10-04T14:04:38.852Z&isGpcEnabled=0&datestamp=Fri+Oct+11+2024+16:26:30+GMT+0100+(British+Summer+Time)&version=202409.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=51304710-7c7d-4672-a80d-6cabc82a6c41&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=1:1,2:1,3:1,4:1&geolocation=GB&AwaitingReconsent=false',
#         #         'domain': '.deloitte.com',
#         #         'path': '/'
#         #     }
#         # ])
        
#         data = []
#         url_template = "https://www.mckinsey.com/industries/aerospace-and-defense/our-insights"
#         # global industry 
#         # industry = 'medical devices'
#         # search_url_template = get_search_url(industry)
#         paginate(url_template, context, data)
#         browser.close()
#         # for entry in data:
#         #     print(entry["headline"])
#         return data

# def scroll_main_page(page):
#     # Scroll down incrementally until the bottom of the page is reached
#     scroll_step = 500  # Adjust scroll step size if necessary
#     scroll_pause_time = 1.5  # Adjust this if needed to allow content to load
#     previous_height = page.evaluate("document.body.scrollHeight")

#     while True:
#         for i in range(10):
#         # Scroll by a set amount
#             page.evaluate(f"window.scrollBy(0, {i * scroll_step})")
#             page.keyboard.press("PageDown")

#         # Wait for the page to load new content
#             page.wait_for_timeout(scroll_pause_time * 1000)  # Adjust the timeout based on content load speed

#         # Wait for network to become idle (optional but can help with lazy-loaded content)
#         page.wait_for_load_state("networkidle")

#         # Get the current scroll height after loading new content
#         current_height = page.evaluate("document.body.scrollHeight")

#         if current_height == previous_height:
#             # If the page height has not changed, we reached the bottom
#             break

#         previous_height = current_height

#     # Optionally wait for the "Next" button or content load completion
#     page.wait_for_load_state("networkidle")


# def process_main_page(page):
#     search_page_headlines_dict = {}

#     # Scroll down the main page to load all the content
#     scroll_main_page(page)

#     # Wait for the <a> elements with the correct selector to be visible
#     try:
#         page.wait_for_selector('a[data-component="mdc-c-link"]', timeout=10000)  # 10-second wait
#     except Exception as e:
#         print(f"Error: {e}. Could not find 'a[data-component=\"mdc-c-link\"]' within timeout.")
#         return search_page_headlines_dict

#     # Extract all the <a> elements that match the selector for headlines/links
#     search_headlines = page.query_selector_all('a[data-component="mdc-c-link"]')

#     if not search_headlines:
#         print("No headlines found. Check if the selector is correct.")
#         print(page.content())  # Optionally print the page content to debug
#         return search_page_headlines_dict

#     # Loop through the elements and extract the text and href attribute
#     for headline in search_headlines:
#         end_url = headline.get_attribute('href')  # Get the href attribute
#         text = headline.inner_text().strip()  # Get the link text

#         # Construct the full URL if the link is relative
#         if end_url and not end_url.startswith('http'):
#             link = 'https://www.mckinsey.com' + str(end_url)
#         else:
#             link = end_url

#         print(f"Text: {text}, Link: {link}")  # Print both to verify the output
#         if text and link:  # Ensure both text and link exist
#             search_page_headlines_dict[text] = link
    
#     return search_page_headlines_dict


# def paginate(url_template, context, data, start_page=1):
#     url = url_template
#     page_number = start_page
#     scraped_urls = set()  # Set to store scraped URLs

#     page = context.new_page()

#     for attempt in range(3):  # Retry up to 3 times
#         try:
#             page.goto(url, wait_until='networkidle')
#             break  # Exit the loop if successful
#         except Exception as e:
#             print(f"Error loading page {page_number} on attempt {attempt + 1}: {e}")

#     while True:

#         # Process the page content
#         search_page_headlines_dict = process_main_page(page)

#         # If no results are found, stop the process
#         if not search_page_headlines_dict:
#             print(f"No results found on page {page_number}. Stopping.")
#             break

#         # Iterate through the headlines and process individual links
#         for headline, headline_link in search_page_headlines_dict.items():
#             if headline_link not in scraped_urls:
#                 process_headline(context, headline, headline_link, data, search_page_headlines_dict)
#                 scraped_urls.add(headline_link)  # Add the URL to the set to avoid duplicates
#             else:
#                 print(f"Skipping already processed URL: {headline_link}")

#         try:
#             # Ensure the next button is visible
#             next_button = page.query_selector('mdc-c-button')
#             if next_button and next_button.is_visible():
#                 print(f"Scraping page {page_number + 1}")
#                 next_button.click()
#                 page.wait_for_load_state('networkidle')  # Wait for the new content to load
#             else:
#                 # No more pages, break the loop
#                 print("No more pages.")
#                 break
            
#             page_number += 1

#         except Exception as e:  
#             print(f"An error occurred during pagination on page {page_number}: {e}")

#             # Retry if the error is related to page closure
#             if "Target page, context or browser has been closed" in str(e):
#                 print("Reopening the page due to an unexpected close.")
#                 page = context.new_page()  # Reopen the page in case of unexpected close
#                 page.goto(url, wait_until='networkidle')
#             else:
#                 break  # If it's not a page close error, exit the loop

#                     # Wait for the next page to load (you can use wait_for_selector for an element unique to the next page)
#                     #page.wait_for_selector('.card-insight')

#     page.close()

# # def process_page(page):
# #     search_page_headlines_dict = {}

# #     try:
# #         page.wait_for_selector('a[data-component="mdc-c-link"]', timeout=10000)  # Wait for up to 10 seconds
# #     except Exception as e:
# #         print(f"Error: {e}. Could not find 'a[data-component=\"mdc-c-link\"]' within timeout.")
# #         return search_page_headlines_dict

# #     # Extracting headlines and links on the current page
# #     search_headlines = page.query_selector_all('a[data-component="mdc-c-link"]')

# #     #print(search_headlines)

# #     # Loop through the elements and extract the text and href attribute
# #     for headline in search_headlines:
# #         end_url = headline.get_attribute('href').strip()   # Get the href attribute
# #         text = headline.inner_text().strip()  # Get the link text
# #         link = 'https://www.mckinsey.com/industries/aerospace-and-defense/our-insights' + str(end_url)
# #         print(f"Text: {text}, Link: {link}")    # Print both
# #         if text and link:  # Ensure both text and href exist
# #             search_page_headlines_dict[text] = link  # Use .strip() to remove extra whitespace
    
# #     return search_page_headlines_dict

# def process_headline(context, headline, headline_link, data, search_page_headlines_dict):
#     with context.new_page() as headline_link_page:
#         is_pdf_redirected = False
#         pdf_link = ''
#         is_404_error = False 
#         url = headline_link
#         entry = {}

#         def handle_response(response):
#             nonlocal is_pdf_redirected, pdf_link, is_404_error
#             # Check for 404 error
#             if response.status == 404 and response.url == url:
#                 is_404_error = True
#                 print(f"404 error encountered for {response.url}")

#             # Check if the response is a PDF
#             elif response.url.endswith('.pdf'):
#                 is_pdf_redirected = True
#                 pdf_link = response.url
#                 print("Intercepted PDF response:", pdf_link)       

#         def handle_request_failure(request):
#             nonlocal is_404_error, entry
#             # Handle request failures, such as NS_ERROR_UNKNOWNHOST
#             if request.failure:  # Ensure failure object exists
#                 if "NS_ERROR_UNKNOWNHOST" in request.failure:
#                     print(f"Request failed: {request.url} due to {request.failure}")
#                 elif request.failure == "net::ERR_ABORTED" and request.url == url:
#                     is_404_error = True  # Consider it a 404 if the main URL fails to load
#                 elif request.failure == "net::ERR_NAME_NOT_RESOLVED":
#                     is_404_error = True  # Consider it a 404 if the main URL fails to load

#         headline_link_page.on("response", handle_response)
#         headline_link_page.on("requestfailed", handle_request_failure)

#         try:
#             headline_link_page.goto(headline_link, wait_until='domcontentloaded')
#             #headline_link_page.keyboard.press('End')
#             #headline_link_page.scroll

#             if is_pdf_redirected and pdf_link:
#                 if is_404_error:
#                     # Extract the end_url from the original headline link
#                     pdf_link = pdf_link.replace('https://www.mckinsey.com/industries/aerospace-and-defense/our-insights', '')
#                     # Construct the new link by prepending the correct base URL
#                     #new_link = '' + end_url
#                     print(f"Trying further amended link: {pdf_link}")

#                     # Reset 404 error flag
#                     is_404_error = False
                    
#                 # Use Playwright's expect_download to handle PDF download
#                 pdf_filename = sanitise_filename(pdf_link)
#                 #download.save_as(pdf_filename)
#                 print(pdf_filename)
#                 try:
#                     download_pdf(pdf_link, pdf_filename)
#                 # try:
#                 #     with headline_link_page.expect_download() as download_info:
#                 #         print("is pdf 4")
#                 #         download = download_info.value
#                 #         print("is pdf 5")

#                 #         #pdf_filename = f"{sanitise_filename(headline)}.pdf"
#                 #         # pdf_filename.wait_for_load_state('domcontentloaded')
#                 #         # pdf_filename.path(path=pdf_filename)

#                 #         # #headline_link_page.pdf(path=pdf_filename)
#                 #         # download = download_info.value

#                 #         # download.save_as(pdf_filename)
#                 #         #download_pdf(pdf_link, pdf_filename)
#                     extracted_text = extract_text_from_pdf(pdf_filename)
#                     os.remove(pdf_filename)
#                     entry = {"headline": headline, "link": pdf_filename, "content": extracted_text}

#                 except Exception as pdf_error:
#                     print(f"Error while downloading or processing the PDF: {pdf_error}")
#                     entry = {"headline": headline, "link": pdf_link, "message": "Error handling PDF"}

#             elif is_404_error:
#                 # Extract the end_url from the original headline link
#                 url = headline_link.replace('https://www.mckinsey.com', 'https://www.mckinsey.com/industries/aerospace-and-defense/our-insights')
                    
#                 # Construct the new link by prepending the correct base URL
#                 #new_link = '' + end_url
#                 print(f"Trying new link: {url}")

#                 # Reset 404 error flag
#                 is_404_error = False
#                 # Attempt to navigate to the new link
#                 headline_link_page.goto(url, wait_until='domcontentloaded')

#                 if is_404_error:
#                     # Extract the end_url from the original headline link
#                     url = headline_link.replace('https://www.mckinsey.com/industries/aerospace-and-defense/our-insights', '')
#                     # Construct the new link by prepending the correct base URL
#                     #new_link = '' + end_url
#                     print(f"Trying further amended link: {url}")

#                     # Reset 404 error flag
#                     is_404_error = False
#                     headline_link_page.goto(url, wait_until='domcontentloaded')

#                     # If the new link doesn't raise a 404, update the search_headlines_dict
#                     if not is_404_error:  # If no 404 after retry
#                         is_404_error = False
#                         print(f"Updated working link: {url}")
#                         search_page_headlines_dict[headline] = url  # Update the dictionary with the new link
                    
#                     else: 
#                         entry = {"headline": headline, "link": headline_link, "message": "404 Page Not Found"}
#                         raise Exception(f"404 Page Not Found after multiple retries for {headline_link}")    
#             else:
#                 # If no PDF detected and no 404, capture the page content (in case of HTML response)
#                 headline_link_page_content = headline_link_page.content()
#                 entry = {"headline": headline, "link": headline_link, "content": headline_link_page_content}

#         except Exception as e:
#             print(f"Error during page load for {headline}: {e}")
#             entry = {"headline": headline, "link": headline_link, "message": str(e)}
                
#         #     headline_link_page_content = headline_link_page.content()
#         #     entry = {"headline": headline, "link": search_page_headlines_dict[headline], "content": headline_link_page_content}

#         # except Exception as e:
#         #     print(f"Error during page load for {headline}: {e}")    
                
#         # elif is_404_error:

#         # else:
#         #     entry = {"headline": headline, "link": headline_link, "message": "No PDF was found or redirected."}

#         data.append(entry) #saves after processing so data is captured even if script stops partway through 
#         # for entry in data:
#         #     print(entry["headline"])

# def download_pdf(url, save_path):
#     response = requests.get(url)
#     if response.status_code == 200:
#         with open(save_path, 'wb') as file:
#             file.write(response.content)
#         return save_path
#     else:
#         raise Exception(f"Failed to download PDF from {url}")
    
# def extract_text_from_pdf(pdf_filename):
#     text = ""
#     with pdfplumber.open(pdf_filename) as pdf:
#         for page in pdf.pages:
#             text += page.extract_text()
#     return text

# # def extract_text_from_pdf(pdf_filename):
# #     text = ""
# #     try:
# #         # Open the PDF file
# #         pdf_document = fitz.open(pdf_filename)
# #         # Loop through each page
# #         for page_num in range(pdf_document.page_count):
# #             page = pdf_document.load_page(page_num)
# #             text += page.get_text()  # Extract text from each page
# #         pdf_document.close()  # Close the document after extraction
# #     except Exception as e:
# #         print(f"Error extracting text from {pdf_filename}: {e}")
# #     return text

# def sanitise_filename(text):
#     parsed_url = urllib.parse.urlparse(text)
#     #pdf_filename = os.path.basename(parsed_url.path)
#     return "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in text)[:50]

# if __name__ == "__main__":
#     data = scrape_mckinsey_insights()