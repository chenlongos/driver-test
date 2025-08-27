LOG ?= warn

all: build

build:
	make -C .arceos A=$(PWD)/shell PLATFORM=aarch64-phytium-pi FEATURES="driver-ramdisk" LOG=$(LOG)

disasm:
	make -C .arceos A=$(PWD)/shell PLATFORM=aarch64-phytium-pi FEATURES="driver-ramdisk" disasm

clean:
	make -C .arceos A=$(PWD)/shell clean
	rm -rf output/
