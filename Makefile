LOG ?= warn

all: build

build:
	make -C .arceos A=$(PWD)/shell PLATFORM=aarch64-phytium-pi FEATURES="driver-ramdisk,bus-pci" LOG=$(LOG)

clean:
	make -C .arceos A=$(PWD)/shell clean
	rm -rf output/
