import copy
import json
from os import name
import os
import time
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
        data = []

        industry_referers = get_industry_referers(context)

        try:
            for referer in industry_referers:
                industry_payload = capture_payload(referer, context)
                print(industry_payload)
                has_next = True
                next_cursor = ''
                empty_payload_processed = False

                while has_next:
                    if industry_payload == {} and not empty_payload_processed:
                        # This is the first time we're encountering an empty industry_payload
                        print(has_next)
                        has_next, next_cursor, industry_payload, search_page_headlines_dict = make_api_call(industry_payload, referer, has_next, next_cursor, search_page_headlines_dict, context)
                        print(next_cursor)
                        empty_payload_processed = True
                        print("Finished processing empty payload")
                    elif industry_payload != {}:
                        # This is for non-empty industry_payload
                        print(has_next)
                        has_next, next_cursor, industry_payload, search_page_headlines_dict = make_api_call(industry_payload, referer, has_next, next_cursor, search_page_headlines_dict, context)
                        print(next_cursor)
                        print("Finished processing non-empty payload")
                    else:
                        # This is for subsequent empty industry_payload occurrences
                        break

                print(f"End of processing: {referer}")
        except Exception as e:
            print(f"Error fetching URLs from API: {e}")
            return []
            
        for headline, headline_link in search_page_headlines_dict.items():
            process_headline(context, headline, headline_link, data)

        browser.close()
        return data

def capture_payload(referer, context):
    page = context.new_page()
    api_url = "https://prd-api.mckinsey.com/api/insightsgrid/articles"
    payload = {}

    # Listen for network events
    def handle_request(request):
        nonlocal payload
        if api_url in request.url and request.method == 'POST':  
            # Extract and print the post data (payload)
            post_data = request.post_data
            if post_data:
                payload = json.loads(post_data)
                #print("Captured Payload:", json.dumps(payload, indent=4))

    # Attach the network event handler to intercept requests
    page.on("request", handle_request)

    # Navigate to the desired website
    page.goto(referer)  # Replace with the site that triggers the API call

    # Optionally wait for the API call to complete (adjust timeout as needed)
    page.wait_for_timeout(5000)

    # Close the browser
    page.close()

    return payload

def get_industry_referers(context):
    industry_referers = []
    base_url = "https://www.mckinsey.com"
    industries_url = f"{base_url}/industries"
    page = context.new_page()
    page.goto(industries_url, wait_until='domcontentloaded')
    page.wait_for_timeout(5000)

    # Scrape all industry links
    industry_link_elements = page.query_selector_all('a[href^="/industries/"]')
    
    for element in industry_link_elements:
        industry_href = element.get_attribute('href')

        if industry_href:
            url = urllib.parse.urljoin(base_url, industry_href)
            parsed_url = urllib.parse.urlparse(url)
            path_parts = parsed_url.path.split('/')
            # Remove 'how-we-help-clients' and insert 'our-insights'
            if 'how-we-help-clients' in path_parts:
                path_parts[path_parts.index('how-we-help-clients')] = 'our-insights'

            # Reconstruct the URL
            filtered_path = '/'.join(path_parts)
            industry_url = f"{parsed_url.scheme}://{parsed_url.netloc}{filtered_path}"

            # Add the reconstructed URL to the list
            industry_referers.append(industry_url)
            # industry_section = None

            #if 'how-we-help-clients' in path_parts:
            #    industry_index = path_parts.index('how-we-help-clients') + 1
            #     if industry_index < len(path_parts):
            #         industry_section = path_parts[industry_index]
    print(industry_referers)

    page.close()
    
    return industry_referers


def make_api_call(payload, referer, has_next, next_cursor, search_page_headlines_dict, context):
    print("starting API call")
    url = "https://prd-api.mckinsey.com/api/insightsgrid/articles"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.mckinsey.com",
        "Referer": referer,  # Dynamically updating the Referer header
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }

    # payload = {
    #     "limit": 10000,
    #     "afterId": next_cursor,
    #     "taxonomyAndTags": {
    #         "taxonomyQueryType": "OR",
    #         "taxonomyIds": ["7aa6f280-7392-4ef0-94af-f5ca6b805f81", "a78d0556-eff0-44b8-8e5e-339f9f600f1d"],
    #         "mustHaveTagsQueryType": "OR",
    #         "mustHaveTags": ["91cfe105-8dad-437c-8734-3d740dcdb437", "887e7cb2-191e-44d5-9ec6-de040b312a25", "a9103a6d-6663-4a30-bf78-9927d74f5df5", "21dc6bd4-9b9a-4de0-a9b8-71f68efef898", "c3f331dd-6683-4c33-9460-e56bb1487f33", "13f7e352-920f-4dd2-9a31-f2c3314eb405", "fa4bb8d5-ea76-4dd9-9530-2c865a87d5e0", "83cf99bc-d256-4e4c-a1bf-d0698ec601e9", "c5b24078-44cd-435c-b265-4e36593a226c"],
    #         "mustNotHaveTagsQueryType": "OR",
    #         "mustNotHaveTags": ["a65a9603-c09a-489f-9d77-4afd71c629b3"]
    #     },
    #     "excludeItems": ["e0e9832c-72b0-469e-b439-1fb7da310249", "aeee10e3-34a4-4fc9-8770-88856b9df8e4", "0f3d061b-bf1c-4cae-9d1c-21a35459bcf3", "71be4890-0806-43df-af8b-6ee067c9a198", "c23f199c-28df-4102-9a1a-900608064a08", "2072397b-689f-44c3-809c-4652d8a563c8", "c50a56bf-83fe-4fd2-af5c-fed8869c68ee", "b1484c69-6031-49ad-a36f-8a19933c5478"],
    #     "language": "en",
    #     "isAlumni": False,
    #     "filters": []
    # }
    # Modify the 'limit' value to 10000
    payload['limit'] = 10000
    payload['afterId'] = next_cursor

    # Print the updated payload
    #print("Updated Payload:", json.dumps(payload, indent=4))

    try:
        print("next part API call")
        response = requests.post(url, json=payload, headers=headers)
        time.sleep(3)
        response.raise_for_status()  # This will raise an exception for 4xx or 5xx status codes    
        print(response.status_code)

        if response.status_code == 200:
            data = response.json()
            #print(data)
            posts = data.get('posts', [])
            has_next = data.get('hasNext')
            print(has_next)
            next_cursor = data.get('nextCursor')
            print(next_cursor)
            
            for post in posts:
                title = post.get('title')
                article_url = post.get('url')
                
                if title and article_url:
                    full_url = f"https://www.mckinsey.com{article_url}"  # Complete the URL
                    search_page_headlines_dict[title] = full_url  # Store title and URL in dictionary
                    #print(search_page_headlines_dict[title])

                    print(f"Title: {title}")
                    print(f"URL: {full_url}")
                    print(f"nextCursor: {next_cursor}")
                    print("---")

        elif response.status_code == 400:
            print("Attempting new API call due to 400 response status")
            # Scrape the webpage
            page = context.new_page()
            page_no = 1
            has_more_pages = True
            payload = {}

            while has_more_pages:
                
            #while response is not None:
                url = f"https://www.mckinsey.com/industries/travel-logistics-and-infrastructure/our-insights?UseAjax=true&PresentationId=225AFD08-2381-4FCD-B73F-F68A6859B4FC&ds=A003A89B-1E27-4E36-BF36-6AA47B94BB48&showfulldek=False&hideeyebrows=False&ig_page={page_no}"

                print(f"Attempting new API call: {url}")
                page.goto(url, wait_until='domcontentloaded')

                # Wait for the content to load
                page.wait_for_timeout(3000) 

                # Check if "View more insights" button exists
                view_more_button = page.query_selector('a[aria-label="view more insights"]')
                if view_more_button:

                    # Select all the links on the page
                    link_elements = page.query_selector_all("a[href^='/industries']")

                    if not link_elements:
                        has_more_pages = False  # Stop if there are no more links
                    else:
                        for link in link_elements:
                            title = link.inner_text().strip()
                            article_url = link.get_attribute('href')
                    
                    # response = requests.get(url)
                    # response.raise_for_status()  # This will raise an exception for 4xx or 5xx status codes    

                    # print(response.status_code)
                    # data = response
                    # #print(data)
                    # gets = data.__getattribute__("a.href", [])
                    
                    # for href in gets:
                    #     title = href.get('headline')
                    #     article_url = post.get('href')
                        
                            if title and article_url:
                                full_url = f"https://www.mckinsey.com{article_url}"  # Complete the URL
                                search_page_headlines_dict[title] = full_url  # Store title and URL in dictionary
                                #print(search_page_headlines_dict[title])

                                print(f"Title: {title}")
                                print(f"URL: {full_url}")
                                print(f"nextCursor: {next_cursor}")
                                print("---")

                            else:
                                # If "View more insights" button is not found, close the page and stop scraping
                                print(f"'View more insights' button not found on page {page_no}, closing.")
                                has_more_pages = False
                
                page_no += 1
            page.close()
        else:
            print(f"Unexpected error: {response.status_code}")
            print(response.text)

    except requests.RequestException as e:
        if response.status_code == 400:
            print("Attempting new API call due to 400 response status")
            # Scrape the webpage
            page = context.new_page()
            page_no = 1
            has_more_pages = True
            payload = {}

            while has_more_pages:
                
            #while response is not None:
                url = f"https://www.mckinsey.com/industries/travel-logistics-and-infrastructure/our-insights?UseAjax=true&PresentationId=225AFD08-2381-4FCD-B73F-F68A6859B4FC&ds=A003A89B-1E27-4E36-BF36-6AA47B94BB48&showfulldek=False&hideeyebrows=False&ig_page={page_no}"

                print(f"Attempting new API call: {url}")
                page.goto(url, wait_until='domcontentloaded')

                # Wait for the content to load
                page.wait_for_timeout(3000) 

                # Check if "View more insights" button exists
                view_more_button = page.query_selector('a[aria-label="view more insights"]')
                if view_more_button:

                    # Select all the links on the page
                    link_elements = page.query_selector_all("a[href^='/industries']")

                    if not link_elements:
                        has_more_pages = False  # Stop if there are no more links
                    else:
                        for link in link_elements:
                            title = link.inner_text().strip()
                            article_url = link.get_attribute('href')
                    
                    # response = requests.get(url)
                    # response.raise_for_status()  # This will raise an exception for 4xx or 5xx status codes    

                    # print(response.status_code)
                    # data = response
                    # #print(data)
                    # gets = data.__getattribute__("a.href", [])
                    
                    # for href in gets:
                    #     title = href.get('headline')
                    #     article_url = post.get('href')
                        
                            if title and article_url:
                                full_url = f"https://www.mckinsey.com{article_url}"  # Complete the URL
                                search_page_headlines_dict[title] = full_url  # Store title and URL in dictionary
                                #print(search_page_headlines_dict[title])

                                print(f"Title: {title}")
                                print(f"URL: {full_url}")
                                print(f"nextCursor: {next_cursor}")
                                print("---")

                else:
                    # If "View more insights" button is not found, close the page and stop scraping
                    print(f"'View more insights' button not found on page {page_no}, closing.")
                    has_more_pages = False
                
                page_no += 1
            page.close()
        
        elif response.status_code == 403 and not next_cursor:
            print(f"Forbidden 403 error on API call response status: {e} \nReferer =: {referer} \nPayload: {payload} \nURL: {url} \nhas_next: {has_next}")
            payload = {}
        
        elif response.status_code == 403 and next_cursor:
            print(f"Forbidden 403 error on API call response status but still has next_cursor: {e} \nReferer =: {referer} \nPayload: {payload} \nURL: {url} \nhas_next: {has_next} \nnext_cursor: {next_cursor}")
            payload = {}
            print(f"Stopping this {referer} api calls")

        else:
            print(f"Unexpected error: {response.status_code}")
            print(response.text)

            print(f"Error during API call: {e}")
        
    # except Exception as api_error:
    #         print(f"Error: {api_error} - {response.status_code}")
            
    # else:
    #     print(f"Error: {response.status_code}")
    #     print(response.text)

    return has_next, next_cursor, payload, search_page_headlines_dict

    
        
def process_headline(context, headline, headline_link, data):
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