import logging
import json
from datetime import datetime
from elasticsearch import Elasticsearch
import inspect

ELASTIC_URL = "http://localhost:9200"
ELASTIC_INDEX = "koshki-logs"


class ElasticsearchHandler(logging.Handler):
    def __init__(self, es_client, index):
        super().__init__()
        self.es = es_client
        self.index = index

    def emit(self, record):
        try:
            if isinstance(record.msg, dict):
                doc = record.msg
            else:
                doc = json.loads(record.msg)

            if "@timestamp" not in doc:
                doc["@timestamp"] = datetime.utcnow().isoformat() + "Z"

            response = self.es.index(index=self.index, document=doc)
            log_id = response.get("_id")
            print(f"[Elasticsearch] Лог записан с ID: {log_id}")
        except Exception as e:
            print(f"[ERROR] Не удалось отправить лог в Elasticsearch: {e}")


class AppLogger:
    def __init__(self, name: str, es_client: Elasticsearch, index: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        if not self.logger.handlers:
            es_handler = ElasticsearchHandler(es_client, index)
            self.logger.addHandler(es_handler)

            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(message)s"
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def _make_log_entry(
        self,
        level,
        logger_class,
        event,
        message,
        params=None,
        summary=None,
        ErrClass=None,
        ErrMethod=None,
    ):
        if ErrClass is None or ErrMethod is None:
            frame = inspect.currentframe()
            try:
                outer_frame = frame.f_back.f_back
                method_name = outer_frame.f_code.co_name
                self_obj = outer_frame.f_locals.get("self")
                class_name = (
                    self_obj.__class__.__name__ if self_obj else logger_class
                )
            finally:
                del frame
        else:
            class_name = ErrClass
            method_name = ErrMethod
        safe_params = {}
        for k, v in (params or {}).items():
            try:
                json.dumps(v)
                safe_params[k] = v
            except TypeError:
                safe_params[k] = str(v)

        return {
            "@timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "logger_class": logger_class,
            "event": event,
            "message": message,
            "summary": summary or "No summary provided",
            "ErrClass": class_name,
            "ErrMethod": method_name,
            "params": safe_params,
        }

        return {
            "@timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "logger_class": logger_class,
            "event": event,
            "message": message,
            "summary": summary or "No summary provided",
            "ErrClass": class_name,
            "ErrMethod": method_name,
            "params": params or {},
        }

    def info(self, logger_class, event, message, params=None, summary=None):
        entry = self._make_log_entry(
            "INFO",
            logger_class,
            event,
            message,
            params=params,
            summary=summary,
        )
        self.logger.info(entry)

    def error(
        self,
        logger_class,
        event,
        message,
        params=None,
        summary=None,
        ErrClass=None,
        ErrMethod=None,
    ):
        self._make_log_entry(
            "ERROR",
            logger_class,
            event,
            message,
            params=params,
            summary=summary,
            ErrClass=ErrClass,
            ErrMethod=ErrMethod,
        )

    def warning(
        self,
        logger_class,
        event,
        message,
        params=None,
        summary=None,
        ErrClass=None,
        ErrMethod=None,
    ):
        entry = self._make_log_entry(
            "WARNING",
            logger_class,
            event,
            message,
            params=params,
            summary=summary,
            ErrClass=ErrClass,
            ErrMethod=ErrMethod,
        )
        self.logger.warning(entry)


def setup_logger(name: str = "app_logger") -> AppLogger:
    es_client = Elasticsearch(ELASTIC_URL)
    return AppLogger(name, es_client, ELASTIC_INDEX)
