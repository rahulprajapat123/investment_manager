import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Layout, Menu, theme } from 'antd';
import { SpeedInsights } from '@vercel/speed-insights/react';
import {
  HomeOutlined,
  UploadOutlined,
  FileTextOutlined,
  DashboardOutlined,
} from '@ant-design/icons';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Reports from './pages/Reports';
import './App.css';

const { Header, Content, Footer, Sider } = Layout;

const menuItems = [
  {
    key: '/',
    icon: <DashboardOutlined />,
    label: 'Dashboard',
  },
  {
    key: '/upload',
    icon: <UploadOutlined />,
    label: 'Upload Data',
  },
  {
    key: '/reports',
    icon: <FileTextOutlined />,
    label: 'Reports',
  },
];

function App() {
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  const [current, setCurrent] = React.useState('/');

  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Layout style={{ minHeight: '100vh' }}>
        <Sider
          breakpoint="lg"
          collapsedWidth="0"
          style={{
            overflow: 'auto',
            height: '100vh',
            position: 'fixed',
            left: 0,
            top: 0,
            bottom: 0,
          }}
        >
          <div
            style={{
              height: 32,
              margin: 16,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontSize: '18px',
              fontWeight: 'bold',
            }}
          >
            📊 Portfolio Analytics
          </div>
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={[current]}
            items={menuItems.map((item) => ({
              ...item,
              onClick: () => setCurrent(item.key),
              label: <Link to={item.key}>{item.label}</Link>,
            }))}
          />
        </Sider>
        <Layout style={{ marginLeft: 200 }}>
          <Header
            style={{
              padding: '0 24px',
              background: colorBgContainer,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <h2 style={{ margin: 0 }}>Portfolio Analytics Platform</h2>
          </Header>
          <Content style={{ margin: '24px 16px 0' }}>
            <div
              style={{
                padding: 24,
                minHeight: 360,
                background: colorBgContainer,
                borderRadius: borderRadiusLG,
              }}
            >
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/upload" element={<Upload />} />
                <Route path="/reports" element={<Reports />} />
              </Routes>
            </div>
          </Content>
          <Footer style={{ textAlign: 'center' }}>
            Portfolio Analytics ©{new Date().getFullYear()} Created with FastAPI + React
          </Footer>
        </Layout>
        <SpeedInsights />
      </Layout>
    </Router>
  );
}

export default App;
