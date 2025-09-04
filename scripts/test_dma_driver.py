import pytest
import logging

@pytest.mark.dma
class TestDmaDriver:
    def setup_method(self):
        self.logger = logging.getLogger("TestDmaDriver")
        self.test_result = False

    def test_dma_functionality(self, debug_uart):
        # 发送DMA初始化命令
        self.logger.info("Sending dma_init command")
        response = debug_uart.send_command("dma_test")
        self.test_result = "OK" in response
        assert self.test_result, "DMA driver initialization failed"

    def teardown_method(self):
        # 记录测试结果
        if self.test_result:
            self.logger.info("DMA driver test passed")
        else:
            self.logger.error("DMA driver test failed")