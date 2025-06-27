import logging
from elasticsearch import Elasticsearch
from pythonjsonlogger import jsonlogger
import json
import datetime

ELASTIC_URL = "http://localhost:9200"
ELASTIC_INDEX = "koshki-logs"

class ElasticsearchHandler(logging.Handler):
    def __init__(self, es_client, index):
        super().__init__()
        self.es = es_client
        self.index = index

    def emit(self, record):
        try:
            log_entry = self.format(record)
            doc = json.loads(log_entry)
            self.es.index(index=self.index, document=doc)
        except Exception as e:
            print(f"Error sending log to Elasticsearch: {e}")

def setup_logger(name: str = "app_logger") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        es = Elasticsearch(ELASTIC_URL)

        es_handler = ElasticsearchHandler(es, ELASTIC_INDEX)
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(ip)s %(user_agent)s'
        )
        es_handler.setFormatter(formatter)
        logger.addHandler(es_handler)

    return logger
