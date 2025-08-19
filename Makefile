all: build

build:
	make -C .arceos A=$(PWD)/shell PLATFORM=aarch64-phytium-pi FEATURES="driver-ramdisk,bus-pci"

clean:
	make -C .arceos A=$(PWD)/shell clean
