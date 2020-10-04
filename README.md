# pmacct-kafka-elastic
**pmacct-kafka-elastic** is a python script designed to read flow statistics from [Kafka], to process it and to store it into [Elasticsearch].\
Flow statistics is expected to be produced  by [Pmacct] flow collector kafka plugin.\
Script calls bulk api of [Elasticsearch] to store data.\
Prometheus client is used to expose total count of sample processed. Metrics can be scraped at "/metrics" path. Default port is "9003".

It is recommended  to set `kafka_history` and `kafka_history_roundoff` options in sfacct.conf or nfacct.conf to get stamp_updated and stamp_inserted values.

Example:
```
plugins: kafka[kafka]
kafka_history[kafka]: 5m
kafka_history_roundoff[kafka]: m
```
Default index mapping is in the file `new-index-template.json`.

### Runnig the script

Just run:
```
pmacct-kafka-elastic.py
```
Script gets its  configuration from environment variables or from .env file(see .env.example).

### Running script in docker:

```
docker run --env-file .env --name pmacct-kafka-elastic -p 9003:9003 kvitex/pmacct-kafka-elastic 
```

### Variables:

Variable | Description | Example
--- | --- | ---
`KAFKA_BOOTSTRAP_SERVERS` | Kafka botstrap server in host:port format. Where can be several ones, separated by coma  |  **mykafka1:9094**
`KAFKA_TOPIC` | Kafka topic to read from.|  **pmacct.sfacct**
`KAFKA_CONSUMER_GROUP_ID` | Kafka consumer group id. Default value is  kafka2elastic | kafka2elastic
`ELASTIC_HOSTS` | Coma separated list of Elasticseach host:port. Default value for port is '9200'| **es01,es02:9290**
`ELASTIC_USE_SSL` |If 'YES' then SSL will be used to connect Elasticseach hosts. Default is 'NO' |  NO
`ELASTIC_VERIFY_SSL` | Verify SSL certifcate if SSL transport is used. Default 'YES'  | YES
`ELASTIC_INDEX_PREFIX` | Prefix for index name. Full index name is yyyy-MM-dd. Default is 'sflow' | sflow
`ELASTIC_INDEX_TEMPLATE` | File with index mapping. Default is 'new-index-template.json' | new-index-template.json
`ELASTIC_MAX_SAMPLES_PER_SEND` | Maximum number of samples that script caches before store them in  [Elasticsearch]. Defaul value is '1000'  | 1000
`ELASTIC_MAX_TIME_TO_SEND` | Maximum time in seconds, between sending samples to  [Elasticsearch]. Default value is 10 | 10
`PROMETHEUS_CLIENT_PORT` | Prometheus client http server port. Default value is '9003' | 9003

Script is polling Kafka for new messages in topic and store them in memory. It looks for amount of samples were read and time passed from last insert to [Victoria Metrics] operation.\
If amount of samples is greater then `ELASTIC_MAX_SAMPLES_PER_SEND`  or time has passed from last index action in [Elasticsearch] is greater then `ELASTIC_MAX_TIME_TO_SEND` or both, then cached samples are stored in [Elasticsearch], cached samples counter is reset to 0 and timer is set to current timestamp.




[//]:#

[pmacct]: <http://www.pmacct.net/>
[Elasticsearch]: <https://www.elastic.co/> 
[kafka]: <https://kafka.apache.org/>
