# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class BricosimplonPipeline:
    def process_item(self, item, spider):
        return item
    

# bricosimplon/pipelines.py
class CleanProductPipeline:
    def process_item(self, item, spider):
        item['name'] = item['name'].strip().title()
        return item