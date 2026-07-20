#!/bin/sh
# Setup Debezium connectors & Elasticsearch cho hệ thống CSDLPT

CONNECT_HOST=${1:-localhost}
CONNECT_URL="http://${CONNECT_HOST}:8083/connectors"
ES_URL="http://elasticsearch:9200"

# Đợi Elasticsearch và Kafka Connect sẵn sàng
until curl -s "$ES_URL/_cluster/health" | grep -q '"status":"green"\|"status":"yellow"'; do sleep 5; done
while [ $(curl -s -o /dev/null -w "%{http_code}" "$CONNECT_URL") -ne 200 ]; do sleep 5; done

# Xoá connectors cũ
connectors=$(curl -s "$CONNECT_URL" | tr -d '[]"' | tr ',' '\n')
for c in $connectors; do
  curl -s -X DELETE "$CONNECT_URL/$c" > /dev/null
done
sleep 2

# Xoá index nhật ký cũ
curl -s -X DELETE "$ES_URL/*nhatkythaotac*" > /dev/null
curl -s -X DELETE "$ES_URL/*NhatKyThaoTac*" > /dev/null
curl -s -X DELETE "$ES_URL/nhat-ky-thao-tac" > /dev/null
sleep 2

# Tạo ingest pipeline (chuyển ThoiGian từ microseconds → milliseconds)
curl -s -X PUT "$ES_URL/_ingest/pipeline/nhatky_pipeline" -H "Content-Type: application/json" -d '{
  "processors": [
    { "script": { "source": "if (ctx.ThoiGian != null) { ctx.ThoiGian = (long)(ctx.ThoiGian / 1000); }" } }
  ]
}' > /dev/null

# Nạp index template (priority 1100)
curl -s -X PUT "$ES_URL/_index_template/nhatky_template" -H "Content-Type: application/json" -d '{
  "index_patterns": ["*nhatkythaotac*", "*NhatKyThaoTac*", "nhat-ky-thao-tac"],
  "priority": 1100,
  "template": {
    "settings": {
      "index.refresh_interval": "1s",
      "index.default_pipeline": "nhatky_pipeline"
    },
    "mappings": {
      "properties": {
        "ThoiGian": { "type": "date", "format": "epoch_millis||strict_date_optional_time" },
        "MaGiaoTac": { "type": "keyword" },
        "MaSV":      { "type": "keyword" },
        "MaLopHP":   { "type": "keyword" },
        "MaCoSo":    { "type": "keyword" },
        "TrangThai": { "type": "keyword" },
        "ChiTiet":   { "type": "text" }
      }
    }
  }
}' > /dev/null
sleep 2

# Tạo sẵn 4 ES index (tổng hợp + riêng từng site)
for idx in nhat-ky-thao-tac hadong.public.nhatkythaotac hoalac.public.nhatkythaotac ngoctruc.public.nhatkythaotac; do
  status=$(curl -s -o /dev/null -w "%{http_code}" "$ES_URL/$idx")
  if [ "$status" != "200" ]; then
    curl -s -X PUT "$ES_URL/$idx" -H "Content-Type: application/json" \
      -d '{"settings":{"number_of_shards":1,"number_of_replicas":1}}' > /dev/null
  fi
done
sleep 1

# Tạo Debezium source connectors (ind = index riêng, uni = gộp vào 1 topic)
create_source_connector() {
  site=$1; host=$2; db=$3
  curl -s -X POST "$CONNECT_URL" -H "Content-Type: application/json" \
    -d '{"name":"src-'"$site"'-ind","config":{"connector.class":"io.debezium.connector.postgresql.PostgresConnector","database.hostname":"'"$host"'","database.port":"5432","database.user":"csdlpt_user","database.password":"csdlpt_pass","database.dbname":"'"$db"'","database.server.name":"'"$site"'","topic.prefix":"'"$site"'","table.include.list":"public.nhatkythaotac","plugin.name":"pgoutput","slot.name":"dbz_'"$site"'_ind","publication.name":"dbz_pub_'"$site"'_ind"}}' > /dev/null

  curl -s -X POST "$CONNECT_URL" -H "Content-Type: application/json" \
    -d '{"name":"src-'"$site"'-uni","config":{"connector.class":"io.debezium.connector.postgresql.PostgresConnector","database.hostname":"'"$host"'","database.port":"5432","database.user":"csdlpt_user","database.password":"csdlpt_pass","database.dbname":"'"$db"'","database.server.name":"'"$site"'-uni","topic.prefix":"'"$site"'-uni","table.include.list":"public.nhatkythaotac","plugin.name":"pgoutput","slot.name":"dbz_'"$site"'_uni","publication.name":"dbz_pub_'"$site"'_uni","transforms":"route","transforms.route.type":"org.apache.kafka.connect.transforms.RegexRouter","transforms.route.regex":".*","transforms.route.replacement":"nhat-ky-thao-tac"}}' > /dev/null
}

create_source_connector "hadong"   "postgres_hadong"   "csdlpt_hadong"
create_source_connector "hoalac"   "postgres_hoalac"   "csdlpt_hoalac"
create_source_connector "ngoctruc" "postgres_ngoctruc" "csdlpt_ngoctruc"

# Tạo ES Sink connectors
# es-sink-ind: ghi vào index riêng từng site (metadata refresh 30s để phát hiện topic mới nhanh)
curl -s -X POST "$CONNECT_URL" -H "Content-Type: application/json" \
  -d '{"name":"es-sink-ind","config":{"connector.class":"io.confluent.connect.elasticsearch.ElasticsearchSinkConnector","connection.url":"http://elasticsearch:9200","tasks.max":"1","topics.regex":"(?i).*nhatkythaotac","key.ignore":"true","schema.ignore":"true","transforms":"unwrap","transforms.unwrap.type":"io.debezium.transforms.ExtractNewRecordState","consumer.override.metadata.max.age.ms":"30000"}}' > /dev/null

# es-sink-uni: ghi vào index tổng hợp nhat-ky-thao-tac
curl -s -X POST "$CONNECT_URL" -H "Content-Type: application/json" \
  -d '{"name":"es-sink-uni","config":{"connector.class":"io.confluent.connect.elasticsearch.ElasticsearchSinkConnector","connection.url":"http://elasticsearch:9200","tasks.max":"1","topics":"nhat-ky-thao-tac","key.ignore":"true","schema.ignore":"true","transforms":"unwrap","transforms.unwrap.type":"io.debezium.transforms.ExtractNewRecordState"}}' > /dev/null

echo "[ok] Connectors & ES indices ready"

# Đợi Kibana và tạo Data Views
KIBANA_URL="http://kibana:5601"
KIBANA_READY=false
for i in $(seq 1 36); do
  if [ "$(curl -s -o /dev/null -w '%{http_code}' "$KIBANA_URL/api/status")" = "200" ]; then
    KIBANA_READY=true; break
  fi
  sleep 5
done

if [ "$KIBANA_READY" = true ]; then
  for view in \
    'nhat-ky-thao-tac|NhatKy-Tong' \
    'hadong.public.nhatkythaotac|NhatKy-HaDong' \
    'hoalac.public.nhatkythaotac|NhatKy-HoaLac' \
    'ngoctruc.public.nhatkythaotac|NhatKy-NgocTruc'
  do
    title=$(echo "$view" | cut -d'|' -f1)
    name=$(echo "$view"  | cut -d'|' -f2)
    curl -s -X POST "$KIBANA_URL/api/data_views/data_view" \
      -H "Content-Type: application/json" -H "kbn-xsrf: true" \
      -d "{\"data_view\":{\"title\":\"$title\",\"name\":\"$name\",\"timeFieldName\":\"ThoiGian\"}}" > /dev/null
  done
  echo "[ok] Kibana Data Views ready"
else
  echo "[warn] Kibana không phản hồi — bỏ qua tạo Data Views"
fi
