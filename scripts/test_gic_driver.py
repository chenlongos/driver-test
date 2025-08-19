import pytest
import logging

@pytest.mark.gic
class TestGicDriver:
    def setup_method(self):
        self.logger = logging.getLogger("TestGicDriver")
        self.test_result = False

    def test_gic_initialization(self, debug_uart):
        # 发送GIC初始化命令
        self.logger.info("Sending gic_init command")
        response = debug_uart.send_command("gic_init")
        self.test_result = response
        assert self.test_result, "GIC driver initialization failed"

    def teardown_method(self):
        # 记录测试结果
        if self.test_result:
            self.logger.info("GIC driver test passed")
        else:
            self.logger.error("GIC driver test failed")
        # 可以添加清理命令（如果需要）
        # debug_uart.send_command("gic_cleanup")