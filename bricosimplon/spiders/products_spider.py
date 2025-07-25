from ..items import ProductItem
import scrapy
import csv
import os
import re

class ProductsSpider(scrapy.Spider):
    name = "products_spider"
    allowed_domains = ["venessens-parquet.com"]
    start_urls = ["https://venessens-parquet.com/"]


    def __init__(self):
        super().__init__()
        self.products = {
            'parquets_interieur': [],
            'parquets_exterieur': [],
            'habillage_mural': [],
            'accessoires': []
        }
        self.skipped_products_count = 0  

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


    def parse_product_page(self, response):
        category = response.meta['category']
        product_id = response.css('div.elementor-shortcode span.reference::text').get()
        name = response.css('h1.product_title::text').get()
        price = response.css('div.elementor-shortcode span.prix::text').get()
        

        item = ProductItem()
        item['product_id'] = product_id #cleaned_product_id (Le neetayge sera fait dans le pipeline)
        item['name'] = name #cleaned_name
        item['category'] = category
        item['price'] = price #cleaned_price
        item['url'] = response.url
        yield item #self.products[category].append(item) 

    def determine_category(self, url):
        category_mapping = {
            'parquets-dinterieur': 'parquets_interieur',
            'parquets-exterieur': 'parquets_exterieur',
            'habillage-mural': 'habillage_mural',
            'accessoires': 'accessoires'
        }
        for pattern, category in category_mapping.items():
            if pattern in url:
                return category
