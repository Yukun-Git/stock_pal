import { Routes, Route } from 'react-router-dom';
import { Layout, Button, Dropdown, MenuProps } from 'antd';
import { UserOutlined, LogoutOutlined } from '@ant-design/icons';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import PrivateRoute from '@/components/PrivateRoute';
import HomePage from './pages/HomePage';
import BacktestPage from './pages/BacktestPage';
import LoginPage from './pages/LoginPage';
import './App.css';

const { Header, Content, Footer } = Layout;

function AppHeader() {
  const { user, isAuthenticated, logout } = useAuth();

  const menuItems: MenuProps['items'] = [
    {
      key: 'logout',
      label: '退出登录',
      icon: <LogoutOutlined />,
      onClick: logout,
    },
  ];

  return (
    <Header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      background: '#001529',
      padding: '0 50px'
    }}>
      <div style={{ color: 'white', fontSize: '20px', fontWeight: 'bold' }}>
        📈 股票回测系统
      </div>

      {isAuthenticated && user && (
        <Dropdown menu={{ items: menuItems }} placement="bottomRight">
          <Button type="text" style={{ color: 'white' }}>
            <UserOutlined /> {user.nickname || user.username}
          </Button>
        </Dropdown>
      )}
    </Header>
  );
}

function AppContent() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <AppHeader />

      <Content style={{ padding: '24px 50px' }}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<HomePage />} />
          <Route
            path="/backtest"
            element={
              <PrivateRoute>
                <BacktestPage />
              </PrivateRoute>
            }
          />
        </Routes>
      </Content>

      <Footer style={{ textAlign: 'center', background: '#f0f2f5' }}>
        Stock Backtest System ©2024 - 散户量化交易回测平台
      </Footer>
    </Layout>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
