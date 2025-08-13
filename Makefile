all: build

build:
	make -C .arceos A=$(PWD)/shell ARCH=aarch64 PLATFORM=aarch64-phytium-pi FEATURES=driver-ramdisk 

clean:
	make -C .arceos A=$(PWD)/shell ARCH=aarch64 PLATFORM=aarch64-phytium-pi FEATURES=driver-ramdisk clean
