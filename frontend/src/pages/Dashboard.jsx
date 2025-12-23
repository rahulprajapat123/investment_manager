import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Button, message, Spin } from 'antd';
import {
  UserOutlined,
  FileTextOutlined,
  SyncOutlined,
  DownloadOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

const API_BASE_URL = 'http://localhost:5000';

const Dashboard = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processingJobs, setProcessingJobs] = useState({});

  const fetchClients = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/clients`);
      setClients(response.data.clients);
    } catch (error) {
      message.error('Failed to fetch clients');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClients();
  }, []);

  const handleProcessClient = async (clientId) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/process/${clientId}`);
      const jobId = response.data.job_id;
      
      message.info(`Processing started for ${clientId}`);
      
      setProcessingJobs(prev => ({ ...prev, [clientId]: jobId }));
      
      // Poll for job status
      const interval = setInterval(async () => {
        try {
          const statusResponse = await axios.get(`${API_BASE_URL}/api/jobs/${jobId}`);
          const status = statusResponse.data.status;
          
          if (status === 'completed') {
            clearInterval(interval);
            message.success(`Report generated for ${clientId}`);
            setProcessingJobs(prev => {
              const newJobs = { ...prev };
              delete newJobs[clientId];
              return newJobs;
            });
            fetchClients();
          } else if (status === 'failed') {
            clearInterval(interval);
            message.error(`Processing failed for ${clientId}: ${statusResponse.data.error}`);
            setProcessingJobs(prev => {
              const newJobs = { ...prev };
              delete newJobs[clientId];
              return newJobs;
            });
          }
        } catch (error) {
          clearInterval(interval);
          console.error('Error polling job status:', error);
        }
      }, 2000);
      
    } catch (error) {
      message.error('Failed to start processing');
      console.error(error);
    }
  };

  const handleDownloadReport = async (clientId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/reports/${clientId}`, {
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${clientId}_portfolio.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      message.success('Report downloaded successfully');
    } catch (error) {
      message.error('Failed to download report');
      console.error(error);
    }
  };

  const handleDeleteClient = async (clientId) => {
    try {
      await axios.delete(`${API_BASE_URL}/api/clients/${clientId}`);
      message.success(`Client ${clientId} deleted successfully`);
      fetchClients();
    } catch (error) {
      message.error('Failed to delete client');
      console.error(error);
    }
  };

  const columns = [
    {
      title: 'Client ID',
      dataIndex: 'client_id',
      key: 'client_id',
      sorter: (a, b) => a.client_id.localeCompare(b.client_id),
    },
    {
      title: 'Brokers',
      dataIndex: 'brokers',
      key: 'brokers',
      render: (brokers) => brokers.join(', '),
    },
    {
      title: 'Data Files',
      dataIndex: 'data_files_count',
      key: 'data_files_count',
    },
    {
      title: 'Report Status',
      dataIndex: 'has_report',
      key: 'has_report',
      render: (hasReport, record) => (
        <span style={{ color: hasReport ? '#52c41a' : '#faad14' }}>
          {hasReport ? '✓ Generated' : '⚠ Not Generated'}
        </span>
      ),
    },
    {
      title: 'Last Updated',
      dataIndex: 'report_date',
      key: 'report_date',
      render: (date) => date ? dayjs(date).fromNow() : 'N/A',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button
            type="primary"
            icon={<SyncOutlined spin={processingJobs[record.client_id]} />}
            size="small"
            onClick={() => handleProcessClient(record.client_id)}
            disabled={processingJobs[record.client_id]}
          >
            {processingJobs[record.client_id] ? 'Processing...' : 'Generate Report'}
          </Button>
          {record.has_report && (
            <Button
              type="default"
              icon={<DownloadOutlined />}
              size="small"
              onClick={() => handleDownloadReport(record.client_id)}
            >
              Download
            </Button>
          )}
          <Button
            danger
            icon={<DeleteOutlined />}
            size="small"
            onClick={() => handleDeleteClient(record.client_id)}
          >
            Delete
          </Button>
        </div>
      ),
    },
  ];

  const totalReports = clients.filter(c => c.has_report).length;
  const totalDataFiles = clients.reduce((sum, c) => sum + c.data_files_count, 0);

  return (
    <div>
      <h1>Dashboard</h1>
      
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="Total Clients"
              value={clients.length}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Generated Reports"
              value={totalReports}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Total Data Files"
              value={totalDataFiles}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title="Clients"
        extra={
          <Button icon={<SyncOutlined />} onClick={fetchClients} loading={loading}>
            Refresh
          </Button>
        }
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: 50 }}>
            <Spin size="large" />
          </div>
        ) : (
          <Table
            columns={columns}
            dataSource={clients}
            rowKey="client_id"
            pagination={{ pageSize: 10 }}
          />
        )}
      </Card>
    </div>
  );
};

export default Dashboard;
