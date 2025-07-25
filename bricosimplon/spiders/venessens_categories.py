import scrapy
from bricosimplon.items import CategoryItem
from urllib.parse import urljoin
import re # Bibiothèque regex pour extraire l'ID de la catégorie

class VenessensCategoriesSpider(scrapy.Spider):
    name = "venessens_categories"
    allowed_domains = ["venessens-parquet.com"]
    start_urls = ["https://venessens-parquet.com"]

    # Ordre des colonnes dans le CSV exporté
    custom_settings = {
        'FEED_EXPORT_FIELDS': [
            "unique_id",
            "id_uppercat",
            "category_id",
            "name",
            "url",
            "is_page_list"
        ]
    }

    # Catégories principales avec leur id html
    category_parents = {
        'menu-item-1623': "Les Parquets d’Intérieur",
        'menu-item-1622': "Les Parquets d’Extérieur",
        'menu-item-1627': "Les Parquets à Motif",
        'menu-item-4596': "L'Habillage Mural Latho",
        'menu-item-1626': "Les Accessoires"
    }

    def parse(self, response):
        # On boucle sur chaque menu principal (catégorie parente)
        for menu_id, name in self.category_parents.items():
            # On extrait l'ID numérique du menu (ex: "menu-item-1623" devient "1623")
            match_parent = re.search(r'(\d+)', menu_id)
            category_id = f"cat_id_{match_parent.group(1)}" if match_parent else menu_id
            url = urljoin(response.url, response.css(f'#{menu_id} > a::attr(href)').get())


            # Item pour la catégorie principale (page d’accueil comme parent)
            item = CategoryItem()
            item['unique_id'] = f"venessens.welcome.{category_id}"
            item['id_uppercat'] = "welcome_venessens"
            item['category_id'] = category_id
            item['name'] = name
            item['url'] = url
            item['is_page_list'] = 0
            yield item

            # Sélecteur CSS pour trouver tous les liens vers les sous-catégories
            links = response.css(f'#{menu_id} li.menu-item a.elementor-item')

            # On boucle sur tous les liens trouvés
            for link in links:
                sub_name = link.css('::text').get().strip()
                sub_url = urljoin(response.url, link.css('::attr(href)').get())

                # On remonte dans le DOM pour récupérer la classe CSS contenant l’ID numérique (ex: menu-item-505)
                li_class = link.xpath('ancestor::li[1]/@class').get()
                match_child = re.search(r'menu-item-(\d+)', li_class)
                sub_id = f"cat_id_{match_child.group(1)}" if match_child else "unknown"

                # On crée l’item pour la sous-catégorie
                sub_item = CategoryItem()
                sub_item['name'] = sub_name
                sub_item['url'] = sub_url
                sub_item['category_id'] = sub_id
                sub_item['id_uppercat'] = category_id
                sub_item['unique_id'] = f"venessens.{category_id}.{sub_id}"
                sub_item['is_page_list'] = 1

                yield sub_item