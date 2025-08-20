import pytest
import logging

@pytest.mark.ixgeb
class TestIxgebDriver:
    def setup_method(self):
        self.logger = logging.getLogger("TestIxgebDriver")
        self.test_result = False

    def test_ixgeb_initialization(self, debug_uart):
        # 发送IXGEB初始化命令
        self.logger.info("Sending ixgeb_init command")
        response = debug_uart.send_command("ixgeb_init")
        self.test_result = "OK" in response
        assert self.test_result, "IXGEB driver initialization failed"

    def teardown_method(self):
        # 记录测试结果
        if self.test_result:
            self.logger.info("IXGEB driver test passed")
        else:
            self.logger.error("IXGEB driver test failed")
        # 可以添加清理命令（如果需要）
        # debug_uart.send_command("ixgeb_cleanup")