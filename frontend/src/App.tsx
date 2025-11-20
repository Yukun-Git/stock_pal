import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout, Button, Dropdown, MenuProps, Menu } from 'antd';
import { UserOutlined, LogoutOutlined, StarOutlined, LineChartOutlined, ApiOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import PrivateRoute from '@/components/PrivateRoute';
import HomePage from './pages/HomePage';
import WatchlistPage from './pages/WatchlistPage';
import BacktestPage from './pages/BacktestPage';
import DataSourcePage from './pages/DataSourcePage';
import LoginPage from './pages/LoginPage';
import './App.css';

const { Header, Content, Footer } = Layout;

function AppHeader() {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems: MenuProps['items'] = [
    {
      key: 'logout',
      label: '退出登录',
      icon: <LogoutOutlined />,
      onClick: logout,
    },
  ];

  const navItems = [
    { key: '/watchlist', label: '自选股', icon: <StarOutlined /> },
    { key: '/backtest', label: '回测', icon: <LineChartOutlined /> },
    { key: '/datasources', label: '数据源', icon: <ApiOutlined /> },
  ];

  const selectedKey = navItems.find(item => location.pathname.startsWith(item.key))?.key || '';

  return (
    <Header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      background: '#001529',
      padding: '0 50px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '48px' }}>
        <div style={{ color: 'white', fontSize: '20px', fontWeight: 'bold' }}>
          📈 Stock Pal
        </div>

        {isAuthenticated && (
          <Menu
            theme="dark"
            mode="horizontal"
            selectedKeys={[selectedKey]}
            items={navItems}
            onClick={({ key }) => navigate(key)}
            style={{ flex: 1, minWidth: 0, background: 'transparent', border: 'none' }}
          />
        )}
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
  const { isAuthenticated } = useAuth();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <AppHeader />

      <Content style={{ padding: '24px 50px' }}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          {/* Redirect root based on auth status */}
          <Route
            path="/"
            element={
              isAuthenticated ? <Navigate to="/watchlist" replace /> : <HomePage />
            }
          />

          {/* Watchlist Page (New Homepage for authenticated users) */}
          <Route
            path="/watchlist"
            element={
              <PrivateRoute>
                <WatchlistPage />
              </PrivateRoute>
            }
          />

          {/* Backtest Page */}
          <Route
            path="/backtest"
            element={
              <PrivateRoute>
                <BacktestPage />
              </PrivateRoute>
            }
          />

          {/* Data Source Page */}
          <Route
            path="/datasources"
            element={
              <PrivateRoute>
                <DataSourcePage />
              </PrivateRoute>
            }
          />
        </Routes>
      </Content>

      <Footer style={{ textAlign: 'center', background: '#f0f2f5' }}>
        Stock Pal ©2025 - 散户量化交易回测平台
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
