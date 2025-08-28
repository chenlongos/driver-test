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
        response = debug_uart.send_command("mio_init")
        self.test_result = "OK" in response
        assert self.test_result, "Pinmux driver initialization failed"

    def test_pinmux_functionality(self, debug_uart):
        # 发送Pinmux功能测试命令
        self.logger.info("Sending pinmux_test command")
        response = debug_uart.send_command("mio_test")
        self.test_result = "OK" in response
        assert self.test_result, "Pinmux driver functionality test failed"

    def teardown_method(self):
        # 记录测试结果
        if self.test_result:
            self.logger.info("Pinmux driver test passed")
        else:
            self.logger.error("Pinmux driver test failed")
