# talentum-monad-bot

Talentum Monad 测试网领水机器人，每日自动领取 0.3 个 MON 测试代币。如果领取失败，将自动进行重试。

请注意：**此脚本旨在免去每日手动领取水源的繁琐，但并不能跳过 Talentum 领水的条件限制**。领水钱包地址必须满足以下必要条件：

1. 完成任意 10 个 Talentum 任务
2. 在其他 EVM 链的资产大于 20 美元

## 系统要求：

- Python 3.10+

## 使用教程

### 1. 克隆项目并安装依赖包

首先，克隆项目并安装所需的依赖包：

```bash
git clone https://github.com/fachebot/talentum-monad-bot.git
cd talentum-monad-bot
pip3 install -r requirements.txt
```

### 2. 初始化配置文件

复制示例配置文件以进行初始化：

```bash
cp config/keys.json.simple config/keys.json
cp config/proxy.json.simple config/proxy.json
cp config/tokens.json.simple config/tokens.json
```

### 3. 配置 Talentum 账号

有两种方式可以配置 Talentum 账号的登录鉴权信息：

1. **通过网页登录：**
   - 在浏览器中登录 Talentum 账号。
   - 使用浏览器开发者工具查看任意 `https://monad-api.talentum.id/api` 请求中的 authorization 信息。
   - 将该信息填写到 `config/tokens.json` 文件中。这种方式无需提供私钥更安全，但操作较为繁琐。
2. **自动获取鉴权信息**
   - 将一个或多个以太坊账号的私钥填写到 `config/keys.json` 文件中。
   - 执行命令 `python3 login.py`，系统将自动进行登录并将用户鉴权的 **Bearer Token** 保存到 `config/tokens.json` 文件中。这种方法更便捷。

### 4. 领取测试 MON 代币

执行以下命令以自动为 `config/tokens.json` 文件中配置的所有账号领取测试代币：

```bash
python3 faucet.py
```

可以在服务器后台运行，如果遇到领取失败的情况，系统将自动进行重试。保证每个账号每天都能领取到 0.3 个 MON 测试代币。

## 贡献
欢迎任何形式的贡献，您可以通过提交 Issues 或 Pull Requests 来参与项目的改进。

## 许可证
此项目遵循 MIT 许可证，详细信息请参见 LICENSE 文件。