/**
 * Admin Failover Page - System failover/replication monitoring
 */

import { useState } from 'react';
import {
  Card, Row, Col, Typography, Button, Space, Tag, Descriptions, Skeleton, Empty, Switch, Result, Alert
} from 'antd';
import {
  ClusterOutlined, SwapOutlined, ReloadOutlined, CheckCircleOutlined,
  CloseCircleOutlined, WarningOutlined, SyncOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { failoverApi } from '@/services/admin/failoverApi';
import { courseApi } from '@/services/admin/courseApi';
import styles from './AdminFailover.module.scss';

const { Title, Text } = Typography;

export default function AdminFailoverPage() {
  const queryClient = useQueryClient();
  const [autoFailoverEnabled, setAutoFailoverEnabled] = useState(false);

  const { data: failoverStatus, isLoading: failoverLoading, refetch: refetchFailover } = useQuery({
    queryKey: ['admin-failover-status'],
    queryFn: failoverApi.getStatus,
  });

  const { data: replicationStatus, isLoading: replLoading, refetch: refetchRepl } = useQuery({
    queryKey: ['admin-replication-status'],
    queryFn: courseApi.getReplicationStatus,
  });

  const manualFailoverMutation = useMutation({
    mutationFn: failoverApi.manualFailover,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-failover-status'] });
    },
  });

  const triggerAutoMutation = useMutation({
    mutationFn: failoverApi.triggerAutoFailover,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-failover-status'] });
    },
  });

  const toggleAutoMutation = useMutation({
    mutationFn: failoverApi.configureAutoFailover,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-failover-status'] });
      setAutoFailoverEnabled(!autoFailoverEnabled);
    },
  });

  const triggerReplMutation = useMutation({
    mutationFn: courseApi.triggerReplication,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-replication-status'] });
    },
  });

  const isLoading = failoverLoading || replLoading;
  const data = failoverStatus || {};

  const sites = data.sites || [];
  const primarySite = sites.find((s) => s.is_primary) || null;
  const aliveSites = sites.filter((s) => s.is_alive);

  const getSiteStatusIcon = (site) => {
    if (site.is_primary) return <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 18 }} />;
    if (!site.is_alive) return <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 18 }} />;
    return <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 18 }} />;
  };

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <div>
          <Title level={3} className={styles.pageTitle}>Giám sát Hệ thống</Title>
          <Text type="secondary">Theo dõi trạng thái failover và replication giữa các site</Text>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => { refetchFailover(); refetchRepl(); }}>Làm mới</Button>
        </Space>
      </div>

      {isLoading ? (
        <Row gutter={[16, 16]}>
          {[1, 2, 3, 4].map((i) => (
            <Col xs={24} md={12} key={i}>
              <Card><Skeleton active /></Card>
            </Col>
          ))}
        </Row>
      ) : (
        <>
          {/* Failover Status */}
          <Card
            title={
              <Space>
                <ClusterOutlined style={{ color: '#1677ff' }} />
                <span>Failover Status</span>
                {data.auto_failover_enabled ? (
                  <Tag color="success">Auto ON</Tag>
                ) : (
                  <Tag color="default">Auto OFF</Tag>
                )}
              </Space>
            }
            extra={
              <Switch
                checkedChildren="Auto ON"
                unCheckedChildren="Auto OFF"
                checked={autoFailoverEnabled}
                onChange={(checked) => toggleAutoMutation.mutate(checked)}
                loading={toggleAutoMutation.isPending}
              />
            }
            className={styles.card}
          >
            {sites.length === 0 ? (
              <Empty description="Không có thông tin site" />
            ) : (
              <>
                {/* Primary Site */}
                <div className={styles.primarySite}>
                  <Title level={5} className={styles.sectionTitle}>
                    <ClusterOutlined style={{ marginRight: 8 }} />
                    Site hiện là Primary
                  </Title>
                  {primarySite ? (
                    <Card className={styles.siteCard}>
                      <Descriptions column={2} size="small">
                        <Descriptions.Item label="Tên site">{primarySite.site_id || primarySite.name}</Descriptions.Item>
                        <Descriptions.Item label="Trạng thái">
                          <Tag color="success">PRIMARY</Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label="Trạng thái hoạt động">
                          {primarySite.is_alive ? (
                            <Tag color="success" icon={<CheckCircleOutlined />}>Online</Tag>
                          ) : (
                            <Tag color="error" icon={<CloseCircleOutlined />}>Offline</Tag>
                          )}
                        </Descriptions.Item>
                      </Descriptions>
                    </Card>
                  ) : (
                    <Alert type="warning" message="Không tìm thấy site primary" />
                  )}
                </div>

                {/* All Sites */}
                <div className={styles.allSites}>
                  <Title level={5} className={styles.sectionTitle}>
                    Tất cả Sites ({aliveSites.length} / {sites.length} alive)
                  </Title>
                  <Row gutter={[12, 12]}>
                    {sites.map((site, idx) => (
                      <Col xs={24} sm={12} md={8} key={idx}>
                        <Card
                          className={`${styles.siteCard} ${site.is_primary ? styles.primaryCard : ''}`}
                          size="small"
                        >
                          <Space>
                            {getSiteStatusIcon(site)}
                            <Text strong>{site.site_id || site.name || `Site ${idx + 1}`}</Text>
                          </Space>
                          <div className={styles.siteInfo}>
                            {site.is_primary && <Tag color="success" style={{ marginBottom: 4 }}>Primary</Tag>}
                            {!site.is_alive && <Tag color="error" style={{ marginBottom: 4 }}>Offline</Tag>}
                          </div>
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </div>

                {/* Actions */}
                <div className={styles.actions}>
                  <Space wrap>
                    <Button
                      type="primary"
                      icon={<SwapOutlined />}
                      onClick={() => triggerAutoMutation.mutate()}
                      loading={triggerAutoMutation.isPending}
                    >
                      Kích hoạt Auto Failover
                    </Button>
                  </Space>
                </div>
              </>
            )}
          </Card>

          {/* Replication Status */}
          <Card
            title={
              <Space>
                <SyncOutlined style={{ color: '#1677ff' }} />
                <span>Replication Status</span>
              </Space>
            }
            className={styles.card}
          >
            {replicationStatus ? (
              <>
                <Descriptions column={2} size="small" bordered>
                  <Descriptions.Item label="Trạng thái">
                    {replicationStatus.pending_events > 0 ? (
                      <Tag color="warning">{replicationStatus.pending_events} pending events</Tag>
                    ) : (
                      <Tag color="success" icon={<CheckCircleOutlined />}>Đồng bộ</Tag>
                    )}
                  </Descriptions.Item>
                  <Descriptions.Item label="Tổng sự kiện">{replicationStatus.total_events ?? '—'}</Descriptions.Item>
                  <Descriptions.Item label="Đã xử lý">{replicationStatus.processed_events ?? '—'}</Descriptions.Item>
                  <Descriptions.Item label="Pending">{replicationStatus.pending_events ?? '—'}</Descriptions.Item>
                </Descriptions>
                <div style={{ marginTop: 16 }}>
                  <Button
                    icon={<SyncOutlined />}
                    onClick={() => triggerReplMutation.mutate()}
                    loading={triggerReplMutation.isPending}
                  >
                    Trigger Replication
                  </Button>
                </div>
              </>
            ) : (
              <Empty description="Không có thông tin replication" />
            )}
          </Card>
        </>
      )}
    </div>
  );
}
