import pytest
import logging

class SPITester:
    def __init__(self, debug_uart):
        self.debug_uart = debug_uart
        self.logger = logging.getLogger("SPI_Tester")
        self.test_result = False

    def run_spi_test(self):
        """执行 SPI 初始化测试"""
        self.logger.info("开始 SPI 初始化测试...")
        response = self.debug_uart.send_command("spi_init")
        self.test_result = "OK" in response
        self.logger.info(f"测试结果: {'PASSED' if self.test_result else 'FAILED'}")
        return self.test_result

@pytest.fixture(scope="module")
def spi_tester(debug_uart):
    """SPI 测试 fixture"""
    tester = SPITester(debug_uart)
    yield tester
    tester.logger.info("SPI 测试完成")

@pytest.mark.spi
def test_spi_initialization(spi_tester):
    assert spi_tester.run_spi_test(), "SPI 初始化失败"