import pytest
import logging

class PWMTester:
    def __init__(self, debug_uart):
        self.debug_uart = debug_uart
        self.logger = logging.getLogger("PWM_Tester")
        self.test_result = False

    def run_pwm_test(self):
        """执行 PWM 初始化测试"""
        self.logger.info("开始 PWM 初始化测试...")
        response = self.debug_uart.send_command("pwm_init")
        self.test_result = "OK" in response
        self.logger.info(f"测试结果: {'PASSED' if self.test_result else 'FAILED'}")
        return self.test_result

@pytest.fixture(scope="module")
def pwm_tester(debug_uart):
    """PWM 测试 fixture"""
    tester = PWMTester(debug_uart)
    yield tester
    tester.logger.info("PWM 测试完成")

@pytest.mark.pwm
def test_pwm_initialization(pwm_tester):
    assert pwm_tester.run_pwm_test(), "PWM 初始化失败"