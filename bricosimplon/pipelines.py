# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import re
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
import csv
import os
# Importer les classes d'items pour vérifier leur type
from .items import CategoryItem, ProductItem


class DuplicatesCategoryPipeline:
    def __init__(self):
        self.seen = set()

    def process_item(self, item, spider):
        # Ce pipeline ne s'applique qu'aux CategoryItem
        if not isinstance(item, CategoryItem):
            return item

        adapter = ItemAdapter(item)
        key = (adapter.get('name'), adapter.get('url'))

        if key in self.seen:
            raise DropItem(f"Doublon de catégorie détecté : {key}")
        else:
            self.seen.add(key)
            return item

class CleanProductPipeline:
    def process_item(self, item, spider):
        # Ce pipeline ne s'applique qu'aux ProductItem
        if not isinstance(item, ProductItem):
            return item

        adapter = ItemAdapter(item)

        # Nettoyage product_id
        product_id = adapter.get('product_id')
        if product_id and product_id.startswith('Ref: '):
            adapter['product_id'] = product_id.replace('Ref: ', '')

        # Nettoyage price
        price = adapter.get('price')
        if price:
            euro_index = price.find('€')
            if euro_index != -1:
                price = price[:euro_index]
            price = re.sub(r'[^\d.,]', '', price)
            adapter['price'] = price.replace(',', '.')

        # Nettoyage name
        name = adapter.get('name')
        if name:
            adapter['name'] = name.strip().lower()

        # Filtrage
        if adapter.get('product_id') == '999999999':
            raise DropItem("Produit ignoré")

        return item

class CsvExportPipeline:
    def open_spider(self, spider):
        self.files = {}
        self.writers = {}
        # Créer le dossier de données s'il n'existe pas
        os.makedirs('data', exist_ok=True)

    def process_item(self, item, spider):
        # Ce pipeline ne s'occupe que de l'export des ProductItem
        if not isinstance(item, ProductItem):
            # Pour tout autre type d'item (ex: CategoryItem), on le laisse passer
            # pour que d'autres pipelines ou l'exporteur de Scrapy le gèrent.
            return item
        
        adapter = ItemAdapter(item)
        category = adapter.get('category', 'default')
        filename = os.path.join('data', f'{category}.csv')

        if category not in self.files:
            # Utiliser 'w' pour écrire un nouveau fichier à chaque fois
            f = open(filename, 'w', newline='', encoding='utf-8')
            self.files[category] = f
            writer = csv.DictWriter(f, fieldnames=adapter.field_names())
            writer.writeheader()
            self.writers[category] = writer

        self.writers[category].writerow(adapter.asdict())
        
        return item

    def close_spider(self, spider):
        for f in self.files.values():
            f.close()