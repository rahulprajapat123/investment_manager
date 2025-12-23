import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Select,
  Upload,
  Button,
  message,
  Alert,
  Space,
  List,
  Tag,
} from 'antd';
import {
  UploadOutlined,
  InboxOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import axios from 'axios';

const { Dragger } = Upload;
const { Option } = Select;

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const UploadPage = () => {
  const [form] = Form.useForm();
  const [fileList, setFileList] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  const uploadProps = {
    multiple: true,
    fileList,
    beforeUpload: (file) => {
      // Check file type
      const isExcel =
        file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
        file.type === 'application/vnd.ms-excel' ||
        file.name.endsWith('.xlsx') ||
        file.name.endsWith('.xls');

      if (!isExcel) {
        message.error(`${file.name} is not an Excel file`);
        return Upload.LIST_IGNORE;
      }

      setFileList((prev) => [...prev, file]);
      return false;
    },
    onRemove: (file) => {
      setFileList((prev) => prev.filter((f) => f.uid !== file.uid));
    },
  };

  const handleSubmit = async (values) => {
    if (fileList.length === 0) {
      message.error('Please select at least one file');
      return;
    }

    setUploading(true);
    setUploadSuccess(false);

    try {
      const formData = new FormData();
      formData.append('client_id', values.client_id);
      
      fileList.forEach((file) => {
        formData.append('files', file);
      });

      const response = await axios.post(`${API_BASE_URL}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      message.success(response.data.message);
      setUploadSuccess(true);
      
      // Reset form
      form.resetFields();
      setFileList([]);
      
      setTimeout(() => setUploadSuccess(false), 5000);
      
    } catch (error) {
      message.error(error.response?.data?.detail || 'Upload failed');
      console.error(error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <h1>Upload Client Data</h1>

      <Alert
        message="Upload Instructions"
        description={
          <div>
            <p>1. Enter the Client ID (e.g., C001, C002, or just 1, 2)</p>
            <p>2. Upload Excel files containing trade data, capital gains, or holdings</p>
            <p>3. Supported file types: .xlsx, .xls</p>
          </div>
        }
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      {uploadSuccess && (
        <Alert
          message="Upload Successful!"
          description="Files uploaded successfully. Go to Dashboard to generate reports."
          type="success"
          showIcon
          icon={<CheckCircleOutlined />}
          closable
          style={{ marginBottom: 24 }}
        />
      )}

      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
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
            <Input
              placeholder="e.g., C001 or 1"
              size="large"
            />
          </Form.Item>

          <Form.Item label="Upload Files">
            <Dragger {...uploadProps} style={{ padding: 20 }}>
              <p className="ant-upload-drag-icon">
                <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
              </p>
              <p className="ant-upload-text">
                Click or drag Excel files to this area to upload
              </p>
              <p className="ant-upload-hint">
                Support for multiple file upload. Only .xlsx and .xls files are accepted.
              </p>
            </Dragger>
          </Form.Item>

          {fileList.length > 0 && (
            <Form.Item label="Selected Files">
              <List
                size="small"
                bordered
                dataSource={fileList}
                renderItem={(file) => (
                  <List.Item
                    actions={[
                      <Button
                        type="text"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={() =>
                          setFileList((prev) => prev.filter((f) => f.uid !== file.uid))
                        }
                      />,
                    ]}
                  >
                    <Space>
                      <Tag color="blue">{file.name}</Tag>
                      <span style={{ color: '#888' }}>
                        {(file.size / 1024).toFixed(2)} KB
                      </span>
                    </Space>
                  </List.Item>
                )}
              />
            </Form.Item>
          )}

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<UploadOutlined />}
              loading={uploading}
              size="large"
              block
            >
              {uploading ? 'Uploading...' : 'Upload Files'}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default UploadPage;
