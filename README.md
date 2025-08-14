Arceos driver test

整个测试环境由两块开发板组成，一个作为测试板，其上运行Linux，另一块作为目标板，其上运行Arceos。

测试板通过USB和目标板的调试串口进行通信。

#### 生成测试镜像

```sh
git clone --recursive https://github.com/shzhxh/driver-test.git
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

```sh
# 安装测试依赖
python3 -m venv ~/.venv
source ~/.venv/bin/activate
pip3 install ./scripts/requests.txt
deactivate

# 运行测试
source ~/.venv/bin/activate
pytest -m uart # 日志记录在pytest-uart.log
deactivate
```