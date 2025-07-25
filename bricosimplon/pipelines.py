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
import pandas as pd
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

        # Nettoyage name
        name = adapter.get('name')
        if name:
            adapter['name'] = name.strip().lower()

        # Filtrage
        if adapter.get('product_id') == '999999999':
            raise DropItem("Produit ignoré")

        return item

class CategoryExportPipeline:
    def open_spider(self, spider):
        # Ce pipeline ne doit s'activer que pour le spider des catégories
        if spider.name == 'venessens_categories':
            os.makedirs('data', exist_ok=True)
            self.file = open(os.path.join('data', 'categories.csv'), 'w', newline='', encoding='utf-8')
            # Utilise dynamiquement tous les champs définis dans votre CategoryItem
            self.writer = csv.DictWriter(self.file, fieldnames=CategoryItem.fields.keys())
            self.writer.writeheader()

    def process_item(self, item, spider):
        # Ce pipeline ne s'applique qu'aux CategoryItem
        if not isinstance(item, CategoryItem):
            return item

        # On écrit la ligne seulement si le writer a été initialisé (pour le bon spider)
        if hasattr(self, 'writer'):
            self.writer.writerow(ItemAdapter(item).asdict())
        return item

    def close_spider(self, spider):
        if hasattr(self, 'file'):
            self.file.close()

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
        # Fusion des produits en un seul fichier CSV
        self.fusionner_csv()


    def fusionner_csv(self):
        directory_path = 'data'
        csv_files = [fichier for fichier in os.listdir(directory_path) if fichier.endswith('.csv') 
                     and fichier != 'venessens_all_products.csv' 
                     and fichier != 'categories.csv']

        list_dataframes = []
        for fichier in csv_files:
            file_path = os.path.join(directory_path, fichier)
            df = pd.read_csv(file_path)
            list_dataframes.append(df)

        combined_df = pd.concat(list_dataframes, ignore_index=True)
        combined_df.to_csv(os.path.join(directory_path, 'venessens_all_products.csv'), index=False)