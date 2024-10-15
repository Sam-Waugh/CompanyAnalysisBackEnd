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
            

        # page.on("download", handle_download)

        # Navigate to the URL
        #page.goto("https://www2.deloitte.com/us/en/insights/industry/dcom/us-gps-crisis-contact-centers-2023.html")
        try:
            page.goto("https://www2.deloitte.com/us/en/insights/industry/dcom/us-gps-crisis-contact-centers-2023.html", wait_until='domcontentloaded')
            #page.goto("https://www2.deloitte.com/content/dam/Deloitte/us/Documents/public-sector/us-gps-crisis-contact-centers-2023.pdf")
        
        except Exception as e:
            print("Error during page load:", e)

        if is_pdf_redirected:
            print(f"PDF found, redirecting to {pdfLink}")
            # Download the PDF using requests
            pdf_filename = "downloaded_file.pdf"
            download_pdf(pdfLink, pdf_filename)
            #context.close()  # Close the context
            #page2 = context.new_page()
            #page2.goto(pdfLink)

        #headlineLink = "https://www2.deloitte.com/content/dam/Deloitte/us/Documents/public-sector/us-gps-crisis-contact-centers-2023.pdf"

            headlineLink = pdfLink
            #print(f"Detected PDF: {headlineLink}")
            pdf_filename = "filename.pdf"
            download_pdf(headlineLink, pdf_filename)

            extracted_text = extract_text_from_pdf(pdf_filename)
            #text_filename = f"{sanitised_headline}.txt"
            #headlineLinkPageContent = extracted_text

            #entry["content"] = extracted_text
            os.remove(pdf_filename)  #delete the PDF after processing

            entry = {"link": headlineLink, "content": extracted_text} 
            
            print(entry)

        else:
            entry = {"message": "No PDF was found or redirected."}

        browser.close()
        # Return the scraped titles
        #return {"titles": article_titles, "content": searchPageContent}
        return entry
    
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
    

# async def handle_response(response):
#     if response.status in [301, 302, 303, 307, 308]:
#         print(f"Redirect detected from {response} with status {response.status}")
#         #route.abort()
#         # You could take action here like stopping further actions or re-routing
        
# def handle_pdf_redirects(route, request):
#     # Check if the new URL contains ".pdf"
#     if request.redirected_from:
#         print(f"Blocking redirect from {request.redirected_from.url} to {request.url}")
#         route.abort()  # Abort the redirect
#     if ".pdf" in request.url:
#         print(f"Blocking redirect to: {request.url}")
#         route.abort()  # Abort the request to prevent the redirect
#     else:
#         route.continue_()

# def handle_download(download):
#     print(f"Download started: {download.url}")
#     # Specify where to save the PDF file
#     download_path = "downloaded_file.pdf"  # Change the name as needed
#     download.save_as(download_path)
#     print(f"PDF downloaded and saved as {download_path}")

#     page.on("download", handle_download)
#     # Optionally save the file if needed
#     # download.save_as("path_to_save_file")


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