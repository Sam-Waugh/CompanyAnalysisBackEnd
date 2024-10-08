from utils.file_handler import save_to_json
from clients.scrapers.deloitte_scraper import scrape_deloitte


data = scrape_deloitte()
titles = data["titles"]
print(titles)

save_to_json(data)