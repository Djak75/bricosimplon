from ..items import ProductItem
import scrapy
import csv
import os

class ProductsSpider(scrapy.Spider):
    """
    Spider to crawl product data from the venessens-parquet.com website.
    It loads URLs from a pre-generated CSV file (containing subcategory pages)
    and scrapes product details (ID, name, price, category, URL).
    """
    name = "products_spider"
    allowed_domains = ["venessens-parquet.com"]
    start_urls = []

    def __init__(self):
        """
        Initialize the spider.
        Loads all URLs from the categories.csv file where is_page_list = 1,
        which correspond to product listing pages.
        """
        # Chargement des URLs depuis le CSV
        csv_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'categories.csv')
        self.start_urls = []

        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['is_page_list'] == '1':
                    self.start_urls.append(row['url'])

        # Initialisation complémentaire
        self.products = {
            'parquets_interieur': [],
            'parquets_exterieur': [],
            'habillage_mural': [],
            'accessoires': []
        }
        self.skipped_products_count = 0

    def parse(self, response):
        """
        Parse the product listing page.
        Extracts product links and paginates if needed.
        """
        category = self.determine_category(response.url)
        product_links = response.css('a.woocommerce-LoopProduct-link.woocommerce-loop-product__link::attr(href)').getall()
        for product_link in product_links:
            yield response.follow(product_link, callback=self.parse_product_page, meta={'category': category})
        next_page = response.css('a.next.page-numbers::attr(href)').get()
        if next_page and next_page.startswith('https://venessens-parquet.com/collection'):
            yield response.follow(next_page, self.parse)

    def parse_product_page(self, response):
        """
        Parse a product detail page.
        Extracts the product ID, name, price, category, and URL.
        """
        category = response.meta['category']
        product_id = response.css('div.elementor-shortcode span.reference::text').get()
        name = response.css('h1.product_title::text').get()
        price = response.css('div.elementor-shortcode span.prix::text').get()
        
        item = ProductItem()
        item['product_id'] = product_id
        item['name'] = name
        item['category'] = category
        item['price'] = price
        item['url'] = response.url
        yield item

    def determine_category(self, url):
        """
        Determine the product category based on the URL.
        Uses a mapping to match URL patterns to human-readable category names.
        """
        category_mapping = {
            'parquets-dinterieur': 'Les_Parquets_Interieur',
            'parquets-exterieur': 'Les_Parquets_Extérieur',
            'habillage-mural': 'Habillage_Mural_Latho',
            'accessoires': 'Les_Accessoires'
        }
        for pattern, category in category_mapping.items():  
            if pattern in url:
                return category
        return "Autre catégorie"
