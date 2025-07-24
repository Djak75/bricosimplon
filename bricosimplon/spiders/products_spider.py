from ..items import ProductItem

import scrapy
import csv
import os

class ProductsSpider(scrapy.Spider):
    name = "products_spider"
    allowed_domains = ["venessens-parquet.com"]
    start_urls = ["https://venessens-parquet.com/"]

    #ferme spider après 6 pages
    #custom_settings = {
    #    'CLOSESPIDER_PAGECOUNT': 10
    #}
    
    def __init__(self):
        super().__init__()
        self.products = {
            'parquets_interieur': [],
            'parquets_exterieur': [],
            'habillage_mural': [],
            'accessoires': []
        }

    def parse(self, response):
        category_links = response.css('div.elementor-element a.elementor-item::attr(href)').getall()
        for link in category_links:
            if link.startswith('https://venessens-parquet.com/collection'):
                yield response.follow(link, self.parse_category_page)

    def parse_category_page(self, response):
        category = self.determine_category(response.url)
        product_links = response.css('a.woocommerce-LoopProduct-link.woocommerce-loop-product__link::attr(href)').getall()
        for product_link in product_links:
            yield response.follow(product_link, callback=self.parse_product_page, meta={'category': category})

        next_page = response.css('a.next.page-numbers::attr(href)').get()
        if next_page and next_page.startswith('https://venessens-parquet.com/collection'):
            yield response.follow(next_page, self.parse_category_page)

    def clean_data(self, product_id, price):
        # clean id
        if product_id and product_id.startswith('Ref: '):
            product_id = product_id.replace('Ref: ', '')
        # clean prix
        if price and price.endswith('€ HT/m²'):
            price = price.replace('€ HT/m²', '').strip()
        return product_id, price
        
    def parse_product_page(self, response):
        category = response.meta['category']
        product_id = response.css('div.elementor-shortcode span.reference::text').get()
        #id2 = response.css('div[class*="elementor-"]::attr(data-elementor-id)').get()
        name = response.css('h1.product_title::text').get()
        price = response.css('div.elementor-shortcode span.prix::text').get()
        product_id, price = self.clean_data(product_id, price)


        item = ProductItem()
        item['product_id'] = product_id if product_id else None
        item['name'] = name if name else None
        item['category'] = category
        item['price'] = price if price else None
        item['url'] = response.url

        self.products[category].append(item)

    def determine_category(self, url):
        category_mapping = {
            'parquets-dinterieur': 'parquets_interieur',
            'parquets-exterieur': 'parquets_exterieur',
            'habillage-mural': 'habillage_mural',
            'accessoires':'accessoires'
        }
        for pattern, category in category_mapping.items():
            if pattern in url:
                return category

    def closed(self, reason):
        self.save_to_csv()

    def save_to_csv(self):
        data_dir = 'data'
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        for category, products in self.products.items():
            if products:
                self._save_category_to_csv(category, products)

    #fonction privée utilisée dans save to csv uniquement
    def _save_category_to_csv(self, category, products):
        filename = os.path.join('data', f'{category}.csv')
        keys = products[0].keys()

        with open(filename, 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(products)
