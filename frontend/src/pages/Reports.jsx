import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  message,
  Space,
  Tag,
  Input,
  Spin,
} from 'antd';
import {
  DownloadOutlined,
  SyncOutlined,
  SearchOutlined,
  FileExcelOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import dayjs from 'dayjs';

const API_BASE_URL = 'http://localhost:5000';

const Reports = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState('');

  const fetchClients = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/clients`);
      setClients(response.data.clients);
    } catch (error) {
      message.error('Failed to fetch reports');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClients();
  }, []);

  const handleDownloadReport = async (clientId) => {
    try {
      message.loading({ content: 'Downloading report...', key: 'download' });
      
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
      
      message.success({ content: 'Report downloaded successfully', key: 'download' });
    } catch (error) {
      message.error({ content: 'Failed to download report', key: 'download' });
      console.error(error);
    }
  };

  const filteredClients = clients.filter((client) =>
    client.client_id.toLowerCase().includes(searchText.toLowerCase())
  );

  const columns = [
    {
      title: 'Client ID',
      dataIndex: 'client_id',
      key: 'client_id',
      sorter: (a, b) => a.client_id.localeCompare(b.client_id),
      render: (text) => (
        <Space>
          <FileExcelOutlined style={{ color: '#52c41a' }} />
          <strong>{text}</strong>
        </Space>
      ),
    },
    {
      title: 'Report Status',
      dataIndex: 'has_report',
      key: 'has_report',
      filters: [
        { text: 'Available', value: true },
        { text: 'Not Available', value: false },
      ],
      onFilter: (value, record) => record.has_report === value,
      render: (hasReport) =>
        hasReport ? (
          <Tag color="success">Available</Tag>
        ) : (
          <Tag color="warning">Not Generated</Tag>
        ),
    },
    {
      title: 'Brokers',
      dataIndex: 'brokers',
      key: 'brokers',
      render: (brokers) => (
        <Space wrap>
          {brokers.map((broker) => (
            <Tag key={broker} color="blue">
              {broker.replace(/_/g, ' ')}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: 'Data Files',
      dataIndex: 'data_files_count',
      key: 'data_files_count',
      sorter: (a, b) => a.data_files_count - b.data_files_count,
    },
    {
      title: 'Generated Date',
      dataIndex: 'report_date',
      key: 'report_date',
      sorter: (a, b) => {
        if (!a.report_date) return 1;
        if (!b.report_date) return -1;
        return new Date(a.report_date) - new Date(b.report_date);
      },
      render: (date) => (date ? dayjs(date).format('MMM DD, YYYY HH:mm') : 'N/A'),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Button
          type="primary"
          icon={<DownloadOutlined />}
          onClick={() => handleDownloadReport(record.client_id)}
          disabled={!record.has_report}
        >
          Download
        </Button>
      ),
    },
  ];

  const reportsAvailable = clients.filter((c) => c.has_report).length;

  return (
    <div>
      <h1>Reports</h1>

      <Card
        title={
          <Space>
            <span>All Reports</span>
            <Tag color="blue">
              {reportsAvailable} / {clients.length} Available
            </Tag>
          </Space>
        }
        extra={
          <Space>
            <Input
              placeholder="Search by Client ID"
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 200 }}
            />
            <Button icon={<SyncOutlined />} onClick={fetchClients} loading={loading}>
              Refresh
            </Button>
          </Space>
        }
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: 50 }}>
            <Spin size="large" />
          </div>
        ) : (
          <Table
            columns={columns}
            dataSource={filteredClients}
            rowKey="client_id"
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `Total ${total} clients`,
            }}
          />
        )}
      </Card>
    </div>
  );
};

export default Reports;
