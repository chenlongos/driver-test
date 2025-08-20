import pytest
import logging

@pytest.mark.fxmac
class TestFxmacDriver:
    def setup_method(self):
        self.logger = logging.getLogger("TestFxmacDriver")
        self.test_result = False

    def test_fxmac_initialization(self, debug_uart):
        # 发送FXMAC初始化命令
        self.logger.info("Sending fxmac_init command")
        response = debug_uart.send_command("fxmac_init")
        self.test_result = "OK" in response
        assert self.test_result, "FXMAC driver initialization failed"

    def teardown_method(self):
        # 记录测试结果
        if self.test_result:
            self.logger.info("FXMAC driver test passed")
        else:
            self.logger.error("FXMAC driver test failed")
        # 可以添加清理命令（如果需要）
        # debug_uart.send_command("fxmac_cleanup")