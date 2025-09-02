Arceos driver test

整个测试环境由两块开发板组成，一个作为测试板，其上运行Linux，另一块作为目标板，其上运行Arceos。

测试板通过USB和目标板的调试串口进行通信。

#### 生成测试镜像

```sh
git clone --recursive https://github.com/shzhxh/driver-test.git
cd driver-test
make build  # 生成的测试镜像在shell目录下
```
#### 目标板上运行测试镜像

```sh
# 把测试镜像拷贝到目标板上
scp shell/arceos.img root@192.168.1.100:/boot/
reboot  # 重启目标板，按任意键进入uboot
# 在uboot下执行如下命令
ext4load mmc 0:1 0x90100000 /boot/arceos.img
dcache flush
go 0x90100000
```

#### 测试板上发起测试

被测试板的调试串口和测试串口都要连接在测试板上。

```sh
# 安装测试依赖
git clone https://github.com/shzhxh/driver-test.git
cd driver-test
python3 -m venv ~/.venv
source ~/.venv/bin/activate
pip3 install -r ./scripts/requests.txt
deactivate

# 运行测试。注：要修改scripts/目录下的py文件里的配置，使与实际情况相符。
source ~/.venv/bin/activate
pytest -m uart # 日志记录在pytest-uart.log
pytest -s -m gpio i2c # 注：gpio和i2c测试需要加-s选项
deactivate
```
