-- ============================================================================
-- 初始测试用户数据
-- ============================================================================
-- 功能: 为系统创建初始测试用户
-- 用途: 开发和测试阶段使用
-- 创建时间: 2025-11-17
-- ============================================================================

\echo '>>> 正在导入初始用户数据...'

-- 插入测试用户
-- 注意: 密码哈希使用 bcrypt (cost factor = 12) 生成
INSERT INTO users (id, username, email, password_hash, nickname, is_active, created_at)
VALUES
    (
        uuid_generate_v4(),
        'admin',
        'admin@stockpal.com',
        '$2b$12$nZJbCruqqhz5uUBY/FhM9e2hwFqlhfP0Jl9TRJHq0rfyd4bI0zXUO',
        '管理员',
        TRUE,
        CURRENT_TIMESTAMP
    ),
    (
        uuid_generate_v4(),
        'test',
        'test@stockpal.com',
        '$2b$12$oUyBy8D2BPcSzivcfOawvuua7ECp1gphkVmaQ9YuLp5kPGsGPX6Tq',
        '测试用户',
        TRUE,
        CURRENT_TIMESTAMP
    ),
    (
        uuid_generate_v4(),
        'demo',
        'demo@stockpal.com',
        '$2b$12$rLuQQjL/g9mqkZWBGwCbRuQftASe4I9gl1Yx.js6kX3J6pSbsXFrG',
        '演示账号',
        TRUE,
        CURRENT_TIMESTAMP
    )
ON CONFLICT (username) DO NOTHING;

\echo '>>> 初始用户数据导入完成'
\echo ''

-- ============================================================================
-- 测试账号信息
-- ============================================================================
-- 用户名: admin    密码: admin123    角色: 管理员
-- 用户名: test     密码: test123     角色: 测试用户
-- 用户名: demo     密码: demo123     角色: 演示账号
-- ============================================================================
