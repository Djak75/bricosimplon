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

    
# Reproduction de la logique de nettoyage de la méthode clean_data dans le pipeline

class CleanProductPipeline:
    def process_item(self, item, spider):
        # Nettoyage product_id
        product_id = item.get('product_id')
        if product_id and product_id.startswith('Ref: '):
            product_id = product_id.replace('Ref: ', '')
        item['product_id'] = product_id

        # Nettoyage price
        price = item.get('price')
        if price:
            euro_index = price.find('€')
            if euro_index != -1:
                price = price[:euro_index]
            price = re.sub(r'[^\d.,]', '', price)
            price = price.replace(',', '.')
        item['price'] = price

        # Nettoyage name
        name = item.get('name')
        if name:
            name = name.strip().lower()
        item['name'] = name

        # Filtrage
        if item.get('product_id') == '999999999':
            raise DropItem("Produit ignoré")

        return item
    
# Reproduction de la logique d'exportation en CSV dans le pipeline

class CsvExportPipeline:
    def open_spider(self, spider):
        self.files = {}
        self.writers = {}

    def process_item(self, item, spider):
        category = item.get('category', 'default')
        filename = os.path.join('data', f'{category}.csv')
        if category not in self.files:
            os.makedirs('data', exist_ok=True)
            f = open(filename, 'w', newline='', encoding='utf-8')
            self.files[category] = f
            writer = csv.DictWriter(f, fieldnames=item.keys())
            writer.writeheader()
            self.writers[category] = writer
        self.writers[category].writerow(dict(item))
        return item

    def close_spider(self, spider):
            for f in self.files.values():
                f.close()
    # Fusion des produits en un seul fichier CSV
            fusionner_csv()


# Defintion de la fonction de fusion des fichiers CSV
def fusionner_csv():
    directory_path = 'data'
    # Je récupère tous les noms des fichiers CSV a fusionner 
    csv_files = []
    for fichier in os.listdir(directory_path):
        if fichier.endswith('.csv') and fichier != 'venessens_all_products.csv':
            csv_files.append(fichier)
    # Je crée une liste de dataframes à partir des fichiers CSV
    list_dataframes = []
    for fichier in csv_files:
        file_path = os.path.join(directory_path, fichier)
        df = pd.read_csv(file_path)
        list_dataframes.append(df)
    # Je concatène tous les dataframes en un seul
    combined_df = pd.concat(list_dataframes, ignore_index=True)
    # Je sauvegarde le dataframe combiné dans un nouveau fichier CSV
    combined_df.to_csv(os.path.join(directory_path, 'venessens_all_products.csv'), index=False)

    