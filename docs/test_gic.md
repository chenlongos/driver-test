测试的原理

- 通过记录计数器中断产生的嘀嗒数来验证gic中断的功能

下载arceos并编译运行

```sh
git clone https://github.com/chenlongos/arceos-driver.git arceos -b phytium-camp
cd arceos
ostool defconfig	# 创建默认配置.project.toml
# 参考phytium/app/test-ddma/.project.toml-example修改.project.toml
ostool run uboot
```

运行结果

- 当ticks的值周期性递增时，表明gic功能正常。否则，gic未生效。

```
Hello, world!
开始周期性获取ticks值...
迭代 1: 当前ticks值 = 2
迭代 2: 当前ticks值 = 102
迭代 3: 当前ticks值 = 202
迭代 4: 当前ticks值 = 302
迭代 5: 当前ticks值 = 402
程序结束，最终ticks值 = 502
```

