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
    
    def run_pwm_functional_test(self, duty_cycle):
        """执行带占空比参数的PWM测试"""
        if not (1 <= duty_cycle <= 100):
            self.logger.error(f"占空比{ duty_cycle }超出范围(1~100)")
            return False
        
        self.logger.info(f"开始PWM占空比{ duty_cycle }%测试...")
        response = self.debug_uart.send_command(f"pwm_test { duty_cycle }")
        self.test_result = "OK" in response
        self.logger.info(f"占空比{ duty_cycle }%测试结果: {'PASSED' if self.test_result else 'FAILED'}")
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

@pytest.mark.pwm
def test_pwm_functional(pwm_tester):
    assert pwm_tester.run_pwm_functional_test(50), "PWM默认占空比测试失败"

@pytest.mark.parametrize("duty_cycle", [1, 25, 50, 75, 100])
@pytest.mark.pwm
def test_pwm_duty_cycle_variations(pwm_tester, duty_cycle):
    assert pwm_tester.run_pwm_functional_test(duty_cycle), \
        f"PWM占空比{duty_cycle}%测试失败"