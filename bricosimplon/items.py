# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class CategoryItem(scrapy.Item):
    name = scrapy.Field()
    url = scrapy.Field()
    category_id = scrapy.Field()
    id_uppercat = scrapy.Field()  
    unique_id = scrapy.Field()
    is_page_list = scrapy.Field() 

class ProductItem(scrapy.Item):
    name = scrapy.Field()
    price = scrapy.Field()
    url = scrapy.Field()
    product_id = scrapy.Field()
    category = scrapy.Field()
