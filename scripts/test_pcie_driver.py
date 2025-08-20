import pytest
import logging

@pytest.mark.pcie
class TestPcieDriver:
    def setup_method(self):
        self.logger = logging.getLogger("TestPcieDriver")
        self.test_result = False

    def test_pcie_initialization(self, debug_uart):
        # 发送PCIe初始化命令
        self.logger.info("Sending pcie_init command")
        response = debug_uart.send_command("pcie_init")
        self.test_result = "OK" in response
        assert self.test_result, "PCIe driver initialization failed"

    def teardown_method(self):
        # 记录测试结果
        if self.test_result:
            self.logger.info("PCIe driver test passed")
        else:
            self.logger.error("PCIe driver test failed")
        # 可以添加清理命令（如果需要）
        # debug_uart.send_command("pcie_cleanup")