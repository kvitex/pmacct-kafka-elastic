#!/usr/bin/env python3
from prometheus_client import start_http_server, Counter
from kafka import KafkaConsumer
from json import loads
from json import dumps
from json import load
from dotenv import load_dotenv
from datetime import datetime
from time import time
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import os
import re
import pytz


load_dotenv()
kafka_bootstrap_servers          = os.environ['KAFKA_BOOTSTRAP_SERVERS']
kafka_topic                      = os.environ['KAFKA_TOPIC']
kafka_consumer_group_id          = os.environ.get('KAFKA_CONSUMER_GROUP_ID','kafka2elastic')
elastic_hosts_string             = os.environ.get('ELASTIC_HOSTS', '127.0.0.1:9200')
elastic_use_ssl_string           = os.environ.get('ELASTIC_USE_SSL','NO')
elastic_verify_ssl_string        = os.environ.get('ELASTIC_VERIFY_SSL','YES')
elastic_index_prefix             = os.environ.get('ELASTIC_INDEX_PREFIX', 'sflow')
elastic_index_template           = os.environ.get('ELASTIC_INDEX_TEMPLATE','new-index-template.json')
elastic_max_samples_per_send     = int(os.environ.get('ELASTIC_MAX_SAMPLES_PER_SEND','1000'))
elastic_max_time_to_send         = int(os.environ.get('ELASTC_MAX_TIME_TO_SEND','10'))
prometheus_client_port           = int(os.environ.get('PROMETHEUS_CLIENT_PORT','9003'))
timestmap_template               = os.environ.get('TIMESTAMP_TEMPLATE', '%Y-%m-%d %H:%M:%S')

elastic_index_settings           = {
                                    "number_of_shards": 1,
                                    "number_of_replicas": 0
                                }
elastic_use_ssl    = elastic_use_ssl_string.lower() in ['true','yes']
elastic_verify_ssl = elastic_verify_ssl_string.lower() in ['true','yes']
elastic_hosts       = list(map(lambda x: {'host': x.split(':')[0],
                                          'port': next(iter(x.split(':')[1:]),'9200'),
                                          'use_ssl': elastic_use_ssl,
                                          'verify_certs': elastic_verify_ssl
                                          },
                                        elastic_hosts_string.split(',')))


def nowstamp():
    return str(datetime.now())

def def_by_type(data_type):
    def_value = ''
    if re.search('Int',data_type):
        def_value = 0
    return def_value

def main():
    print(f'{nowstamp()} Connecting to {elastic_hosts}')
    with open(elastic_index_template) as es_template_file:
        es_index_mappings = load(es_template_file)['mappings']
    es = Elasticsearch(elastic_hosts)
    es_index = {
        'settings': elastic_index_settings,
        'mappings': es_index_mappings
    }
    if not es.ping():
        print(f'{nowstamp()} Connection failed')
        exit(1)
    print(f'{nowstamp()} Connected.')
    elastic_index_name = f'{elastic_index_prefix}-{str(datetime.date(datetime.now()))}'
    print(f'{nowstamp()} Connecting to Kafka broker. Bootstrap servers {kafka_bootstrap_servers}')
    consumer = KafkaConsumer(
        kafka_topic, 
        bootstrap_servers=kafka_bootstrap_servers.split(','),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id=kafka_consumer_group_id,
        value_deserializer=lambda x: loads(x.decode('utf-8'))
        )
    print(f'{nowstamp()} Connected')
    samples_counter = Counter('samples_count_total', 'Total number of samples ')
    print(f'{nowstamp()} Starting Prometheus client http server')
    start_http_server(prometheus_client_port)
    es_docs = []
    samples_timer = int(datetime.now().timestamp())
    samples_max_count = 0
    for message in consumer:
        # Adding current timestamp
        message.value['@timestamp'] = int(time() * 1000)
        es_docs.append(message.value)
        samples_counter.inc()
        samples_max_count += 1
        if (samples_max_count >= elastic_max_samples_per_send) or ((int(datetime.now().timestamp()) - samples_timer) > elastic_max_time_to_send):
            elastic_index_name = f'{elastic_index_prefix}-{str(datetime.date(datetime.now()))}'
            # Checking if index is already exists and if not creating new index
            if not es.indices.exists(elastic_index_name):
                print(f'{nowstamp()} Creating index {elastic_index_name}')
                print(f'{nowstamp()} {es.indices.create(index=elastic_index_name, ignore=400, body=es_index)}')
            docs_ok, docs_error = bulk(es, index=elastic_index_name, actions=es_docs, stats_only=True)
            print(f'{nowstamp()} Sent {docs_ok} samples')
            samples_timer = int(datetime.now().timestamp())
            samples_max_count = 0
            es_docs = []
    return

if __name__ == "__main__":
    main()