# onesphere

OneSphere Open Source MOM(Manufacturing Operation Management) Solution

### 注意

1. MAC系统下开发，将启动参数中增加

```bash
  --limit-memory-hard=0
  ```

2. minio客户端设置

```bash
mc alias set onesphere http://172.17.0.1:9000 minio minio123 
```

--------------------

### 环境变量

```shell
ENV_TIMESCALE_ENABLE: false # 是否打开timescaledb支持
ENV_RUNTIME_ENV: dev # 运行时环境
ENV_ENABLE_SSO: false # 是否启用SSO功能
ENV_ONESHARE_EXPERIMENTAL_ENABLE: false # 是否开启实验性功能
ENV_ONESPHERE_DAQ_WITH_TRACK_CODE_REL: false  # DAQ追踪码使用外键链接
ENV_OSS_BUCKET: oneshare
ENV_OSS_ENDPOINT: 127.0.0.1:9000
ENV_OSS_ACCESS_KEY: minio
ENV_OSS_SECRET_KEY: minio123
ENV_MAX_WORKERS: 8 # 并发获取外部数据时线程池的最大线性数量
ENV_OSS_SECURITY_TRANSPORT: false # 对象存储是否通过SSL连接
ENV_DOWNLOAD_TIGHTENING_RESULT_LIMIT: 1000 #下载拧紧曲线的限制数量
ENV_BACKUP_WITH_MINIO: false #备份还原是否包含minio数据
ENV_PROCESS_PROPOSAL_ANGLE_MARGIN: 3 #给出建议角度范围sigma的margin数值
ENV_PROCESS_PROPOSAL_DURATION: 30 #给出建议角度范围所取的拧紧结果的间隔天数,默认从当天倒退30天范围
```

# 开发环境安装

```shell
git submodule update --init --recursive
sudo apt-get install -y libjpeg-dev libxml2-dev libxslt1-dev libsasl2-dev libldap2-dev libpq-dev build-essential libssl-dev phantomjs
sudo apt-get install -y npm nodejs
sudo npm install -g rtlcss
```