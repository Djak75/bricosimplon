import scrapy
from bricosimplon.items import CategoryItem
from urllib.parse import urljoin
import re # Bibiothèque regex pour extraire l'ID de la catégorie

class VenessensCategoriesSpider(scrapy.Spider):
    name = "venessens_categories"
    allowed_domains = ["venessens-parquet.com"]
    start_urls = ["https://venessens-parquet.com"]

    # Catégories principales avec leur id html
    category_parents = {
        'menu-item-1623': "Les Parquets d’Intérieur",
        'menu-item-1622': "Les Parquets d’Extérieur",
        'menu-item-1627': "Les Parquets à Motif",
        'menu-item-4596': "Habillage Mural Latho",
        'menu-item-1626': "Les Accessoires"
    }

    def parse(self, response):
        seen = set()

        # On boucle sur chaque catégorie principale
        for menu_id, parent_name in self.category_parents.items():
            # Sélecteur CSS qui cible les liens dans ce menu spécifique
            links = response.css(f'#{menu_id} li.menu-item a.elementor-item')

            for link in links:
                name = link.css('::text').get().strip()
                url = link.css('::attr(href)').get()
                full_url = urljoin(response.url, url)

                if (name, full_url) in seen:
                    continue  # On ignore les doublons
                seen.add((name, full_url))

                # On récupère le numéro unique de l'élément CSS (ex: menu-item-505)
                li_class = link.xpath('ancestor::li[1]/@class').get()
                match = re.search(r'menu-item-(\d+)', li_class)
                category_id = match.group(1) if match else full_url

                # On remplit notre item
                item = CategoryItem()
                item['name'] = name
                item['url'] = full_url
                item['category_id'] = category_id
                item['parent_category'] = parent_name

                yield item