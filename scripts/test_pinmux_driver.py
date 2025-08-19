import pytest
import logging

@pytest.mark.pinmux
class TestPinmuxDriver:
    def setup_method(self):
        self.logger = logging.getLogger("TestPinmuxDriver")
        self.test_result = False

    def test_pinmux_initialization(self, debug_uart):
        # 发送Pinmux初始化命令
        self.logger.info("Sending pinmux_init command")
        response = debug_uart.send_command("pinmux_init")
        self.test_result = response
        assert self.test_result, "Pinmux driver initialization failed"

    def teardown_method(self):
        # 记录测试结果
        if self.test_result:
            self.logger.info("Pinmux driver test passed")
        else:
            self.logger.error("Pinmux driver test failed")
        # 可以添加清理命令（如果需要）
        # debug_uart.send_command("pinmux_cleanup")