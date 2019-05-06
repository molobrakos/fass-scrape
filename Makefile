run:
	docker-compose down
	docker-compose build
	touch scrapy.log
	docker-compose run scraper scrapy crawl fass | gzip > fass.jsonl.gz

clean:
	rm -f *.jsonl.gz
	rm -f *.log

