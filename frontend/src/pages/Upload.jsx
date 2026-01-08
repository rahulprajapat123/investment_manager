import React, { useState } from 'react';
import {
  Card,
  Form,
  Input,
  Select,
  Upload,
  Button,
  message,
  Alert,
  Table,
  Tag,
  Space,
  Divider,
} from 'antd';
import {
  UploadOutlined,
  InboxOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import axios from 'axios';

const { Dragger } = Upload;
const { Option } = Select;

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const UploadPage = () => {
  const [form] = Form.useForm();
  const [fileList, setFileList] = useState([]);
  const [fileBrokerMap, setFileBrokerMap] = useState({});
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  // Auto-detect broker from filename
  const detectBrokerFromFilename = (filename) => {
    const lower = filename.toLowerCase();
    if (lower.includes('zerodha') || lower.includes('kite')) return 'Zerodha';
    if (lower.includes('groww')) return 'Groww';
    if (lower.includes('hdfc') || lower.includes('hdfcsec')) return 'HDFC_Bank';
    if (lower.includes('icici')) return 'ICICI_Direct';
    if (lower.includes('schwab')) return 'Charles_Schwab';
    if (lower.includes('fidelity')) return 'Fidelity';
    if (lower.includes('angel')) return 'Angel_One';
    if (lower.includes('upstox')) return 'Upstox';
    return null; // Unknown
  };

  const uploadProps = {
    multiple: true,
    fileList,
    beforeUpload: (file) => {
      // Check file type - accept Excel, CSV, and PDF files
      const isValidFile =
        file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
        file.type === 'application/vnd.ms-excel' ||
        file.type === 'text/csv' ||
        file.type === 'application/pdf' ||
        file.name.endsWith('.xlsx') ||
        file.name.endsWith('.xls') ||
        file.name.endsWith('.csv') ||
        file.name.endsWith('.pdf');

      if (!isValidFile) {
        message.error(`${file.name} is not a valid Excel, CSV, or PDF file`);
        return Upload.LIST_IGNORE;
      }

      // Add file to list
      setFileList((prev) => [...prev, file]);
      
      // Auto-detect broker
      const detectedBroker = detectBrokerFromFilename(file.name);
      if (detectedBroker) {
        setFileBrokerMap((prev) => ({
          ...prev,
          [file.uid]: detectedBroker,
        }));
      }
      
      return false;
    },
    onRemove: (file) => {
      setFileList((prev) => prev.filter((f) => f.uid !== file.uid));
      setFileBrokerMap((prev) => {
        const newMap = { ...prev };
        delete newMap[file.uid];
        return newMap;
      });
    },
  };

  const handleBrokerChange = (fileUid, broker) => {
    setFileBrokerMap((prev) => ({
      ...prev,
      [fileUid]: broker,
    }));
  };

  const handleSubmit = async (values) => {
    if (fileList.length === 0) {
      message.error('Please select at least one file');
      return;
    }

    // Check if all files have brokers assigned
    const unassignedFiles = fileList.filter((file) => !fileBrokerMap[file.uid]);
    if (unassignedFiles.length > 0) {
      message.error(`Please assign a broker to all files. ${unassignedFiles.length} file(s) not assigned.`);
      return;
    }

    setUploading(true);
    setUploadSuccess(false);

    try {
      // Group files by broker
      const filesByBroker = {};
      fileList.forEach((file) => {
        const broker = fileBrokerMap[file.uid];
        if (!filesByBroker[broker]) {
          filesByBroker[broker] = [];
        }
        filesByBroker[broker].push(file);
      });

      // Upload files for each broker
      const results = [];
      for (const [broker, files] of Object.entries(filesByBroker)) {
        const formData = new FormData();
        formData.append('client_id', values.client_id);
        formData.append('broker', broker);
        
        files.forEach((file) => {
          formData.append('files', file);
        });

        const response = await axios.post(`${API_BASE_URL}/api/upload`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        results.push({ broker, count: files.length });
      }

      // Show success message
      const summary = results.map((r) => `${r.broker}: ${r.count} files`).join(', ');
      message.success(`Successfully uploaded files from ${results.length} platform(s) - ${summary}`);
      setUploadSuccess(true);
      
      // Reset form
      form.resetFields();
      setFileList([]);
      setFileBrokerMap({});
      
      setTimeout(() => setUploadSuccess(false), 5000);
      
    } catch (error) {
      message.error(error.response?.data?.error || error.response?.data?.detail || 'Upload failed');
      console.error(error);
    } finally {
      setUploading(false);
    }
  };

  const fileTableColumns = [
    {
      title: 'File Name',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
      render: (name) => <Tag color="blue">{name}</Tag>,
    },
    {
      title: 'Size',
      dataIndex: 'size',
      key: 'size',
      width: 100,
      render: (size) => `${(size / 1024).toFixed(2)} KB`,
    },
    {
      title: 'Broker/Platform',
      key: 'broker',
      width: 250,
      render: (_, record) => (
        <Select
          value={fileBrokerMap[record.uid]}
          onChange={(value) => handleBrokerChange(record.uid, value)}
          style={{ width: '100%' }}
          size="small"
          placeholder="Select broker"
        >
          <Option value="Zerodha">Zerodha</Option>
          <Option value="Groww">Groww</Option>
          <Option value="HDFC_Bank">HDFC Bank</Option>
          <Option value="ICICI_Direct">ICICI Direct</Option>
          
          <Option value="Charles_Schwab">Charles Schwab</Option>
          <Option value="Fidelity">Fidelity</Option>
          <Option value="Angel_One">Angel One</Option>
          <Option value="Upstox">Upstox</Option>
          <Option value="Other">Other</Option>
        </Select>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      width: 100,
      render: (_, record) => {
        const broker = fileBrokerMap[record.uid];
        if (!broker) {
          return <Tag color="orange">Not Assigned</Tag>;
        }
        return <Tag color="green">Ready</Tag>;
      },
    },
  ];

  const fileTableData = fileList.map((file) => ({
    key: file.uid,
    uid: file.uid,
    name: file.name,
    size: file.size,
  }));

  // Get unique brokers for summary
  const uniqueBrokers = [...new Set(Object.values(fileBrokerMap))];

  return (
    <div>
      <h1>Upload Client Data</h1>

      <Alert
        message="Multi-Platform Upload"
        description={
          <div>
            <p><strong>Upload files from multiple brokers simultaneously:</strong></p>
            <ol>
              <li>Enter the Client ID (e.g., C001)</li>
              <li>Select all files from different platforms at once</li>
              <li>Assign each file to its respective broker (auto-detected when possible)</li>
              <li>Click Upload - all platforms will be processed together</li>
              <li>Reports will aggregate data across all brokers</li>
            </ol>
            <p style={{ marginTop: 8 }}>✓ Supported: .xlsx, .xls, .csv, .pdf files</p>
          </div>
        }
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      {uploadSuccess && (
        <Alert
          message="Upload Successful!"
          description="Files uploaded successfully from all platforms. Go to Dashboard to generate reports."
          type="success"
          showIcon
          icon={<CheckCircleOutlined />}
          closable
          style={{ marginBottom: 24 }}
        />
      )}

      <Card>
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            label="Client ID"
            name="client_id"
            rules={[
              { required: true, message: 'Please enter client ID' },
              {
                pattern: /^(C\d{3,}|\d+)$/,
                message: 'Client ID should be in format C001 or just 1',
              },
            ]}
          >
            <Input placeholder="e.g., C001 or 1" size="large" />
          </Form.Item>

          <Form.Item label="Upload Files from All Platforms">
            <Dragger {...uploadProps} style={{ padding: 20 }}>
              <p className="ant-upload-drag-icon">
                <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
              </p>
              <p className="ant-upload-text">
                Click or drag files to this area to upload
              </p>
              <p className="ant-upload-hint">
                Upload files from multiple brokers at once. The system will auto-detect
                brokers from filenames or you can assign them manually below.
              </p>
            </Dragger>
          </Form.Item>

          {fileList.length > 0 && (
            <>
              <Divider orientation="left">File-Broker Mapping ({fileList.length} files)</Divider>
              
              {uniqueBrokers.length > 0 && (
                <Alert
                  message={`Detected ${uniqueBrokers.length} platform(s): ${uniqueBrokers.join(', ')}`}
                  type="success"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
              )}

              <Table
                dataSource={fileTableData}
                columns={fileTableColumns}
                pagination={false}
                size="small"
                style={{ marginBottom: 16 }}
              />
            </>
          )}

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<UploadOutlined />}
              loading={uploading}
              size="large"
              block
              disabled={fileList.length === 0}
            >
              {uploading
                ? 'Uploading to all platforms...'
                : `Upload ${fileList.length} file(s) from ${uniqueBrokers.length || '?'} platform(s)`}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default UploadPage;
