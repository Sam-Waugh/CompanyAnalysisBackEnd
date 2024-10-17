    

name = "quotes_404"
start_urls = ["http://quotes.toscrape.com/page/1/"]
handle_httpstatus_list = [404] # to catch 404 with callback
page_number = 1
    
def parse(self, response):

    # stop spider on 404 response
    if response.status == 404: 
        raise CloseSpider('Recieve 404 response')
            
    # stop spider when no quotes found in response
    if len(response.css('div.quote')) == 0:
        raise CloseSpider('No quotes in response')

    quote_item = QuoteItem()
    for quote in response.css('div.quote'):
        quote_item['text'] = quote.css('span.text::text').get()
        quote_item['author'] = quote.css('small.author::text').get()
        quote_item['tags'] = quote.css('div.tags a.tag::text').getall()
        yield quote_item

    # go to next page
    self.page_number += 1
    next_page = f'http://quotes.toscrape.com/page/{self.page_number}/'
    yield response.follow(next_page, callback=self.parse)
