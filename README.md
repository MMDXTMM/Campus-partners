# 🎓 校园搭子 Campus Buddy

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-green?logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**一个面向大学生的兴趣匹配社交平台**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [项目结构](#-项目结构) • [技术栈](#-技术栈)

</div>

---

## ✨ 功能特性

### 🔐 用户系统
- 三步式注册流程（基础信息 → 兴趣标签 → 偏好设置）
- 安全的密码加密存储（SHA-256 + Salt）
- Token 认证机制

### 🎯 智能匹配
- 基于兴趣标签的随机匹配
- 目标强度、时间节奏、相处模式偏好设置
- 匹配房间实时聊天

### 💬 聊天功能
- 实时消息发送
- 表情输入支持
- 优雅的聊天气泡界面

### ⭐ 信用分体系
- 互评机制（1-5星评价）
- 信用分计算规则：
  - 全部5星评价 → 100分
  - 其他情况 → 最高99分
- 好评率统计展示

### 📅 每日签到
- 连续签到奖励
- 校园币积分系统
- 签到弹窗动画效果

---

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 现代浏览器（Chrome/Firefox/Edge）

### 安装运行

```bash
# 克隆仓库
git clone https://github.com/MMDXTMM/Campus-partners.git
cd Campus-partners

# 运行服务器
python server.py

# 打开浏览器访问
# http://localhost:8080
```

### 测试账号
- 用户名：`test1`
- 密码：`123456`

---

## 📁 项目结构

```
campus-buddy/
├── server.py              # 后端服务主文件
├── templates/
│   └── index.html         # 前端单页应用
├── data/
│   └── campus_buddy.db    # SQLite数据库（自动创建）
├── campus-buddy-plan/     # 产品规划文档
├── register-flow/         # 注册流程设计
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🛠 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | HTML5, CSS3, JavaScript (原生) |
| 后端 | Python HTTPServer |
| 数据库 | SQLite |
| 认证 | Token + SHA-256 |

---

## 📊 数据库设计

| 表名 | 说明 |
|------|------|
| users | 用户信息（昵称、学校、兴趣、信用分等） |
| match_rooms | 匹配房间记录 |
| messages | 聊天消息 |
| ratings | 用户评价 |
| check_ins | 签到记录 |
| tokens | 登录令牌 |

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

<div align="center">

**Made with ❤️ for College Students**

</div>