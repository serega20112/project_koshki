import logging
import json
from datetime import datetime
from elasticsearch import Elasticsearch

ELASTIC_URL = "http://localhost:9200"
ELASTIC_INDEX = "koshki-logs"

class ElasticsearchHandler(logging.Handler):
    def __init__(self, es_client, index):
        super().__init__()
        self.es = es_client
        self.index = index

    def emit(self, record):
        try:
            doc = json.loads(record.getMessage())
            self.es.index(index=self.index, document=doc)
        except Exception as e:
            print(f"Error sending log to Elasticsearch: {e}")

class AppLogger:
    def __init__(self, name: str, es_client: Elasticsearch, index: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        if not self.logger.handlers:
            es_handler = ElasticsearchHandler(es_client, index)
            self.logger.addHandler(es_handler)

    def _make_log_entry(self, level, logger_class, event, message, params=None):
        return {
            "@timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "logger_class": logger_class,
            "event": event,
            "message": message,
            "params": params or {}
        }

    def info(self, logger_class, event, message, params=None):
        entry = self._make_log_entry("INFO", logger_class, event, message, params)
        self.logger.info(json.dumps(entry))

    def logging(self, logger_class, event, message, params=None):
        entry = self._make_log_entry("LOGGING", logger_class, event, message, params)
        self.logger.info(json.dumps(entry))

    def warning(self, logger_class, event, message, params=None):
        entry = self._make_log_entry("WARNING", logger_class, event, message, params)
        self.logger.warning(json.dumps(entry))


def setup_logger(name: str = "app_logger") -> AppLogger:
    es_client = Elasticsearch(ELASTIC_URL)
    return AppLogger(name, es_client, ELASTIC_INDEX)
