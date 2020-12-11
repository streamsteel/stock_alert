# 股票持仓推送

![Stock Wechat Bot](https://github.com/streamsteel/stock_alert/workflows/Stock%20Wechat%20Bot/badge.svg?branch=master)

## 使用方法

```text
使用 Github Actions
```

## Munual
### Fork 到自己的仓库

然后克隆到本地

```bash
git clone xxx
```

### 修改告警时间

打开 `.github/workflows/auto_eight.yml`，将其中的 `cron: '0 0 0 * *'` 改为你想要的时间(注意：该处是UTC时间，北京时间比其多八个小时)

### 设置自己的 Server酱 url

打开 `Setting > Secrets`，添加一个 `SERVERCHANURL` 参数，就是你自己的 Server酱 的 api

### git push

Enjoy yourself~