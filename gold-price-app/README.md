# gold-price-app（Rocky Linux 9）

一个面向低配置服务器（1C1G）的黄金实时价格查询网站，技术栈：Flask + Gunicorn + Nginx + 原生前端。

## 功能
- 展示 XAU/USD 实时价格
- 展示 24 小时涨跌金额与百分比
- 展示更新时间
- 每 30 秒自动刷新
- 后端 `/api/gold` 接口
- 使用环境变量保存 API Key
- 20 秒内存缓存，降低第三方 API 调用频率
- 基础日志输出
- 启用 CORS

## 目录结构
```text
gold-price-app/
├── app.py
├── requirements.txt
├── .env.example
├── gunicorn.conf.py
├── deploy/
│   ├── gold.service
│   ├── nginx.conf
├── static/
│   ├── style.css
│   └── script.js
├── templates/
│   └── index.html
├── README.md
└── .gitignore
```

## 1) Rocky Linux 9 安装依赖
```bash
sudo dnf update -y
sudo dnf install -y python3 python3-pip python3-venv nginx firewalld
```

> 如果系统无 `python3-venv` 包，可只安装 `python3`，然后使用 `python3 -m venv` 验证。

## 2) 部署项目与虚拟环境
```bash
sudo mkdir -p /opt/gold-price-app
sudo chown -R $USER:$USER /opt/gold-price-app
cp -r ./* /opt/gold-price-app/
cd /opt/gold-price-app

python3 -m venv .venv
source .venv/bin/activate
```

## 3) 安装 Python 依赖
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 4) 配置环境变量
```bash
cp .env.example .env
# 编辑 .env，填入真实 GOLD_API_KEY
```

## 5) 启动 Gunicorn（1 worker）
```bash
source .venv/bin/activate
cd /opt/gold-price-app
.venv/bin/gunicorn -c gunicorn.conf.py app:app
```

## 6) 配置 systemd
1. 拷贝 service 文件：
```bash
sudo cp deploy/gold.service /etc/systemd/system/gold.service
```
2. 根据实际运行用户修改 `User`/`Group`（默认示例为 `nginx`），并确保该用户对 `/opt/gold-price-app` 可读。
3. 重新加载并启动：
```bash
sudo systemctl daemon-reload
sudo systemctl enable gold
sudo systemctl start gold
sudo systemctl status gold --no-pager
```

## 7) 配置 Nginx
1. 写入站点配置：
```bash
sudo cp deploy/nginx.conf /etc/nginx/conf.d/gold.conf
```
2. 测试配置：
```bash
sudo nginx -t
```
3. 启动并重启 Nginx：
```bash
sudo systemctl enable nginx
sudo systemctl restart nginx
```

## 8) 防火墙放行（firewalld）
```bash
sudo systemctl enable firewalld
sudo systemctl start firewalld

sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
sudo firewall-cmd --list-services
```

## 9) HTTPS 证书（Certbot 示例）
```bash
sudo dnf install -y epel-release
sudo dnf install -y certbot python3-certbot-nginx

sudo certbot --nginx -d your-domain.com
```

证书自动续期测试：
```bash
sudo certbot renew --dry-run
```

## 低内存优化说明
- Gunicorn 固定 `workers = 1`
- Flask 关闭 debug
- 只使用进程内 20 秒缓存（无 Redis / Celery）
- 无数据库，减少常驻内存
- 依赖精简（总计 5 个）

## 常用排障命令
```bash
journalctl -u gold -f
sudo tail -f /var/log/nginx/error.log
curl -s http://127.0.0.1:8000/api/gold
```
