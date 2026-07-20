# Setup Debezium connectors & Elasticsearch cho hệ thống CSDLPT
# Chạy từ máy host (Windows), kết nối vào localhost

$ConnectUrl = "http://localhost:8083/connectors"
$EsUrl      = "http://localhost:9200"
$KibanaUrl  = "http://localhost:5601"

# Kiểm tra dịch vụ
try { Invoke-RestMethod -Uri $ConnectUrl -Method Get | Out-Null }
catch { Write-Host "[error] Kafka Connect chưa sẵn sàng" -ForegroundColor Red; return }

try { Invoke-RestMethod -Uri "$EsUrl/_cluster/health" -Method Get | Out-Null }
catch { Write-Host "[error] Elasticsearch chưa sẵn sàng" -ForegroundColor Red; return }

# Xoá connectors cũ
$connectors = Invoke-RestMethod -Uri $ConnectUrl -Method Get
foreach ($c in $connectors) {
    Invoke-RestMethod -Uri "$ConnectUrl/$c" -Method Delete | Out-Null
}
Start-Sleep -Seconds 2

# Xoá index nhật ký cũ
@("*nhatky*", "*NhatKy*", "nhat-ky-thao-tac") | ForEach-Object {
    Invoke-RestMethod -Uri "$EsUrl/$_" -Method Delete -ErrorAction SilentlyContinue | Out-Null
}
Start-Sleep -Seconds 2

# Nạp index template (priority 1100)
$template = @{
    index_patterns = @("*nhatky*", "*NhatKy*", "nhat-ky-thao-tac")
    priority = 1100
    template = @{
        settings = @{
            "index.refresh_interval"   = "1s"
            "index.default_pipeline"   = "nhatky_pipeline"
        }
        mappings = @{
            properties = @{
                ThoiGian  = @{ type = "date"; format = "epoch_millis||strict_date_optional_time" }
                MaGiaoTac = @{ type = "keyword" }
                MaSV      = @{ type = "keyword" }
                MaLopHP   = @{ type = "keyword" }
                MaCoSo    = @{ type = "keyword" }
                TrangThai = @{ type = "keyword" }
                ChiTiet   = @{ type = "text" }
            }
        }
    }
}
Invoke-RestMethod -Uri "$EsUrl/_index_template/nhatky_template" -Method Put `
    -Body ($template | ConvertTo-Json -Depth 10) -ContentType "application/json" | Out-Null
Start-Sleep -Seconds 1

# Tạo sẵn 4 ES index (tổng hợp + riêng từng site)
@("nhat-ky-thao-tac", "hadong.public.nhatkythaotac", "hoalac.public.nhatkythaotac", "ngoctruc.public.nhatkythaotac") | ForEach-Object {
    $exists = try { Invoke-RestMethod -Uri "$EsUrl/$_" -Method Get; $true } catch { $false }
    if (-not $exists) {
        Invoke-RestMethod -Uri "$EsUrl/$_" -Method Put `
            -Body '{"settings":{"number_of_shards":1,"number_of_replicas":1}}' `
            -ContentType "application/json" | Out-Null
    }
}

# Hàm tạo Debezium source connectors (ind = index riêng, uni = gộp vào 1 topic)
function New-SourceConnector($Site, $HostName, $DB) {
    $ind = @{
        name = "src-$Site-ind"
        config = @{
            "connector.class"      = "io.debezium.connector.postgresql.PostgresConnector"
            "database.hostname"    = $HostName
            "database.port"        = "5432"
            "database.user"        = "csdlpt_user"
            "database.password"    = "csdlpt_pass"
            "database.dbname"      = $DB
            "database.server.name" = $Site
            "topic.prefix"         = $Site
            "table.include.list"   = "public.nhatkythaotac"
            "plugin.name"          = "pgoutput"
            "slot.name"            = "dbz_${Site}_ind"
            "publication.name"     = "dbz_pub_${Site}_ind"
        }
    }
    Invoke-RestMethod -Uri $ConnectUrl -Method Post `
        -Body ($ind | ConvertTo-Json -Depth 10) -ContentType "application/json" `
        -ErrorAction SilentlyContinue | Out-Null

    $uni = @{
        name = "src-$Site-uni"
        config = @{
            "connector.class"          = "io.debezium.connector.postgresql.PostgresConnector"
            "database.hostname"        = $HostName
            "database.port"            = "5432"
            "database.user"            = "csdlpt_user"
            "database.password"        = "csdlpt_pass"
            "database.dbname"          = $DB
            "database.server.name"     = "$Site-uni"
            "topic.prefix"             = "$Site-uni"
            "table.include.list"       = "public.nhatkythaotac"
            "plugin.name"              = "pgoutput"
            "slot.name"                = "dbz_${Site}_uni"
            "publication.name"         = "dbz_pub_${Site}_uni"
            "transforms"               = "route"
            "transforms.route.type"    = "org.apache.kafka.connect.transforms.RegexRouter"
            "transforms.route.regex"   = ".*"
            "transforms.route.replacement" = "nhat-ky-thao-tac"
        }
    }
    Invoke-RestMethod -Uri $ConnectUrl -Method Post `
        -Body ($uni | ConvertTo-Json -Depth 10) -ContentType "application/json" `
        -ErrorAction SilentlyContinue | Out-Null
}

New-SourceConnector "hadong"   "localhost" "csdlpt_hadong"
New-SourceConnector "hoalac"   "localhost" "csdlpt_hoalac"
New-SourceConnector "ngoctruc" "localhost" "csdlpt_ngoctruc"

# ES Sink: ghi vào index riêng từng site (metadata refresh 30s)
$sinkInd = @{
    name = "es-sink-ind"
    config = @{
        "connector.class"   = "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector"
        "connection.url"    = "http://elasticsearch:9200"
        "tasks.max"         = "1"
        "topics.regex"      = "(?i).*nhatkythaotac"
        "key.ignore"        = "true"
        "schema.ignore"     = "true"
        "transforms"        = "unwrap"
        "transforms.unwrap.type" = "io.debezium.transforms.ExtractNewRecordState"
        "consumer.override.metadata.max.age.ms" = "30000"
    }
}
Invoke-RestMethod -Uri $ConnectUrl -Method Post `
    -Body ($sinkInd | ConvertTo-Json -Depth 10) -ContentType "application/json" `
    -ErrorAction SilentlyContinue | Out-Null

# ES Sink: ghi vào index tổng hợp nhat-ky-thao-tac
$sinkUni = @{
    name = "es-sink-uni"
    config = @{
        "connector.class"   = "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector"
        "connection.url"    = "http://elasticsearch:9200"
        "tasks.max"         = "1"
        "topics"            = "nhat-ky-thao-tac"
        "key.ignore"        = "true"
        "schema.ignore"     = "true"
        "transforms"        = "unwrap"
        "transforms.unwrap.type" = "io.debezium.transforms.ExtractNewRecordState"
    }
}
Invoke-RestMethod -Uri $ConnectUrl -Method Post `
    -Body ($sinkUni | ConvertTo-Json -Depth 10) -ContentType "application/json" `
    -ErrorAction SilentlyContinue | Out-Null

Write-Host "[ok] Connectors & ES indices ready" -ForegroundColor Green

# Tạo Kibana Data Views
$KibanaReady = $false
for ($i = 1; $i -le 36; $i++) {
    try {
        if ((Invoke-WebRequest -Uri "$KibanaUrl/api/status" -UseBasicParsing -TimeoutSec 5).StatusCode -eq 200) {
            $KibanaReady = $true; break
        }
    } catch { }
    Start-Sleep -Seconds 5
}

if ($KibanaReady) {
    @(
        @{ title = "nhat-ky-thao-tac";              name = "NhatKy-Tong"     },
        @{ title = "hadong.public.nhatkythaotac";   name = "NhatKy-HaDong"   },
        @{ title = "hoalac.public.nhatkythaotac";   name = "NhatKy-HoaLac"   },
        @{ title = "ngoctruc.public.nhatkythaotac"; name = "NhatKy-NgocTruc" }
    ) | ForEach-Object {
        $body = @{ data_view = @{ title = $_.title; name = $_.name; timeFieldName = "ThoiGian" } } | ConvertTo-Json
        Invoke-RestMethod -Uri "$KibanaUrl/api/data_views/data_view" -Method Post `
            -Body $body -ContentType "application/json" `
            -Headers @{ "kbn-xsrf" = "true" } -ErrorAction SilentlyContinue | Out-Null
    }
    Write-Host "[ok] Kibana Data Views ready" -ForegroundColor Green
} else {
    Write-Host "[warn] Kibana không phản hồi — bỏ qua tạo Data Views" -ForegroundColor Yellow
}