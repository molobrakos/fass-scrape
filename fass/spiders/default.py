# -*- coding: utf-8 -*-
import scrapy

"""
substances
----------
http://www.fass.se/LIF/substancelist?userType=0&page=B

products
--------
http://www.fass.se/LIF/pharmaceuticallist?userType=0&page=A

ATC
---
http://www.fass.se/LIF/atcregister?userType=0
"""

import re
import datetime

import scrapy
from scrapy.selector import HtmlXPathSelector
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor

from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode, urljoin
import string

from fass.items import Product, Company, Substance

BASE_URL = "http://www.fass.se/LIF"


class DefaultSpider(scrapy.spiders.CrawlSpider):

    name = "fass"
    allowed_domains = ["www.fass.se"]

    start_urls = (
        "http://www.fass.se/LIF/pharmaceuticalliststart",
        "http://www.fass.se/LIF/substanceliststart",
        "http://www.fass.se/LIF/companies",
        "http://www.fass.se/LIF/atcregister")

    def clean_url(self, url):
        url = urljoin(BASE_URL, url)
        url = re.sub(";jsessionid=[^?]*", "", url)
        url = urlsplit(url)
        q = dict(parse_qsl(url.query))
        q = {k: v for k, v in q.items() if k in [
            "userType", "page", "substanceId", "nplId", "organisationId"]}
        q["userType"] = "0"
        return urlunsplit(
            (url.scheme, url.netloc, url.path, urlencode(q), url.fragment))

    def clean_links(self, links):
        for link in links:
            link.url = self.clean_url(link.url)
            yield link

    rules = (
        Rule(LinkExtractor(allow=("/pharmaceuticallist?")),
             process_links="clean_links"),
        Rule(LinkExtractor(allow=("/substancelist?")),
             process_links="clean_links"),
        Rule(LinkExtractor(allow=("/product?")),
             process_links="clean_links",
             callback="parse_product"),
        Rule(LinkExtractor(allow=("/substance?")),
             process_links="clean_links",
             callback="parse_substance"),
        Rule(LinkExtractor(allow=("/companydetails?")),
             process_links="clean_links",
             callback="parse_company"),
    )

    def extract_id(self, url):
        url = urlsplit(url)
        q = dict(parse_qsl(url.query))
        for k, v in q.items():
            if "Id" in k:
                return v
        raise ValueError("No Id found in url: " + url)

    def parse_company(self, response):
        company = Company()
        company["url"] = self.clean_url(response.url)
        company["id"] = self.extract_id(response.url)
        company["name"] = response.css(
            "#readspeaker-article-content .documentstyle h2::text").extract_first()
        return company

    def parse_substance(self, response):
        substance = Substance()
        substance["name"] = response.css("h1::text").extract_first()
        substance["url"] = self.clean_url(response.url)
        substance["id"] = self.extract_id(response.url)
        substance["chemical"] = "".join(response.css(
            ".substance-facts-area h4 + span::text").extract())

        return substance

    def parse_product(self, response):
        product = Product()

        product["text"] = response.css(".fass-content").extract_first()
        
        product["name"] = response.css("h1::text").extract_first()
        product["url"] = self.clean_url(response.url)
        product["id"] = self.extract_id(response.url)

        product["company_id"] = self.extract_id(
            response.css("#product-card #companyname::attr(href)").extract_first())
        product["company_name"] = response.css(
            "#product-card #companyname span::text").extract_first()

        product["atc"] = response.css(
            "#product-card .code a span::text").extract_first()

        product["weight"] = response.css(
            "#product-card .generalinfo .weight::text").extract_first()
        product["available"] = True

        if not product["weight"]:
            product["weight"] = response.css(
                "#product-card .generalinfo .not-available::text").extract_first()
            product["available"] = False

        shape = response.css(
            "#product-card .generalinfo .shape::text").extract_first()
        if shape:
            m = re.search("^\((.*)\)$", shape)
            if m:
                shape = m.group(1).strip()
            product["shape"] = shape

        product["desc"] = "".join(
            response.css("#product-card .desc::text").extract()).strip()

        substances = response.css(
            "#product-card .substance a span::text").extract()
        substances_url = response.css(
            "#product-card .substance a::attr(href)").extract()

        product["substances_ids"] = {} 
        product["substances_ids"] = [ self.extract_id(u)
                                   for u in substances_url ]

        n = product["name"]
        w = product["weight"]

        # replace Foobar ,25 mg -> Foobar 0,25 mg
        n = re.sub(" ,(\d+) ", r" 0,\1 ", n)
        # inconsistently marked up IU vs IE
        n = re.sub(" IU$", " IE", n)
        w = re.sub(" IU$", " IE", w)

        # is already in weight, just remove it from name
        if w in n:
            n = n.replace(", " + w, "")
            product["name"] = n
            product["weight"] = w

        prescription = response.css(
            "#product-info-page .box-header::text").extract_first()
        if (prescription == "Receptfri"):
            product["prescription"] = "otc"
        elif (prescription == "Receptbelagd"):
            if not len(response.css("img[alt~=narkotikaindikation]")):
                product["prescription"] = "yes"
            else:
                product["prescription"] = "narc"
        else:
            product["prescription"] = "?"

        return product
