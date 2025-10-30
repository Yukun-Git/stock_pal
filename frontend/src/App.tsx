import { Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import HomePage from './pages/HomePage';
import BacktestPage from './pages/BacktestPage';
import './App.css';

const { Header, Content, Footer } = Layout;

function App() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{
        display: 'flex',
        alignItems: 'center',
        background: '#001529',
        padding: '0 50px'
      }}>
        <div style={{ color: 'white', fontSize: '20px', fontWeight: 'bold' }}>
          📈 股票回测系统
        </div>
      </Header>

      <Content style={{ padding: '24px 50px' }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/backtest" element={<BacktestPage />} />
        </Routes>
      </Content>

      <Footer style={{ textAlign: 'center', background: '#f0f2f5' }}>
        Stock Backtest System ©2024 - 散户量化交易回测平台
      </Footer>
    </Layout>
  );
}

export default App;
