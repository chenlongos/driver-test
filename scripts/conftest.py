import pytest
import serial
import time

class DebugUART:
    """调试串口管理器，保持长期连接"""
    _instance = None
    
    def __new__(cls, port: str, baudrate: int):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.port = port
            cls._instance.baudrate = baudrate
            cls._instance.ser = None
        return cls._instance
    
    def connect(self) -> bool:
        """建立调试串口连接"""
        if self.ser and self.ser.is_open:
            return True
        
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=2,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            return self.ser.is_open
        except Exception as e:
            print(f"调试串口连接失败: {str(e)}")
            return False
    
    def disconnect(self) -> None:
        """断开调试串口连接"""
        if self.ser and self.ser.is_open:
            self.ser.close()
    
    def send_command(self, command: str) -> bool:
        """发送命令到开发板"""
        if not self.ser or not self.ser.is_open:
            return False
        
        try:
            self.ser.write(f"{command}\r\n".encode())
            time.sleep(0.5)  # 等待命令执行
            return True
        except Exception as e:
            print(f"发送命令失败: {str(e)}")
            return False

@pytest.fixture(scope="session")
def debug_uart():
    """Session 级别的调试串口 fixture，所有测试共享"""
    debug_uart = DebugUART(
        port="/dev/ttyUSB0",
        baudrate=115200,
    )
    debug_uart.connect()  # 在所有测试开始前连接
    yield debug_uart
    debug_uart.disconnect()  # 在所有测试结束后断开