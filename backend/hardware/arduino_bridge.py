import serial
import threading
import queue
import time
import struct
import logging
from typing import Dict, Optional, Callable
from dataclasses import dataclass
import json

@dataclass
class SensorReading:
    """Container for Arduino sensor data"""
    timestamp: float
    temperature: float  # Celsius
    humidity: float     # Percentage
    smoke_ppm: float    # Parts per million
    co_ppm: float       # Carbon monoxide
    flame_detected: bool
    ir_value: int       # IR sensor raw value
    
class ArduinoBridge:
    """Manages communication with Arduino sensor arrays"""
    
    SENSOR_PACKET_SIZE = 24  # bytes
    SYNC_BYTE = 0xAA
    END_BYTE = 0x55
    
    def __init__(self, port: str = '/dev/ttyACM0', baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn: Optional[serial.Serial] = None
        self.data_queue = queue.Queue(maxsize=1000)
        self.is_running = False
        self.read_thread: Optional[threading.Thread] = None
        self.callback: Optional[Callable] = None
        self.logger = logging.getLogger(__name__)
        self.last_heartbeat = time.time()
        self.error_count = 0
        self.total_readings = 0
        
    def connect(self) -> bool:
        """Establish connection with Arduino"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1.0,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            # Clear any buffered data
            self.serial_conn.reset_input_buffer()
            self.serial_conn.reset_output_buffer()
            
            # Send initialization command
            self.send_command("INIT")
            time.sleep(2)  # Wait for Arduino to initialize
            
            # Request sensor configuration
            self.send_command("CONFIG")
            
            self.logger.info(f"Connected to Arduino on {self.port}")
            return True
            
        except serial.SerialException as e:
            self.logger.error(f"Failed to connect to Arduino: {e}")
            return False
    
    def start_monitoring(self) -> None:
        """Start continuous sensor monitoring"""
        if not self.serial_conn or not self.serial_conn.is_open:
            raise RuntimeError("Arduino not connected")
        
        self.is_running = True
        self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.read_thread.start()
        self.logger.info("Started Arduino sensor monitoring")
    
    def _read_loop(self) -> None:
        """Continuous reading loop for sensor data"""
        buffer = bytearray()
        
        while self.is_running:
            try:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.read(self.serial_conn.in_waiting)
                    buffer.extend(data)
                    
                    # Process complete packets
                    while len(buffer) >= self.SENSOR_PACKET_SIZE:
                        if buffer[0] == self.SYNC_BYTE:
                            packet = buffer[:self.SENSOR_PACKET_SIZE]
                            if packet[-1] == self.END_BYTE:
                                self._process_packet(packet)
                                self.total_readings += 1
                            buffer = buffer[self.SENSOR_PACKET_SIZE:]
                        else:
                            # Sync lost, find next sync byte
                            try:
                                sync_idx = buffer.index(self.SYNC_BYTE)
                                buffer = buffer[sync_idx:]
                            except ValueError:
                                buffer.clear()
                
                # Check heartbeat
                if time.time() - self.last_heartbeat > 5:
                    self.send_command("HEARTBEAT")
                    self.last_heartbeat = time.time()
                    
                time.sleep(0.01)  # Small delay to prevent CPU spinning
                
            except Exception as e:
                self.logger.error(f"Error in read loop: {e}")
                self.error_count += 1
                if self.error_count > 10:
                    self.reconnect()
    
    def _process_packet(self, packet: bytes) -> None:
        """Parse and process sensor data packet"""
        try:
            # Unpack binary data (matching Arduino struct)
            unpacked = struct.unpack('<BfffffBHB', packet)
            
            reading = SensorReading(
                timestamp=time.time(),
                temperature=unpacked[1],
                humidity=unpacked[2],
                smoke_ppm=unpacked[3],
                co_ppm=unpacked[4],
                flame_detected=bool(unpacked[6]),
                ir_value=unpacked[7]
            )
            
            # Add to queue
            if not self.data_queue.full():
                self.data_queue.put(reading)
            
            # Call callback if registered
            if self.callback:
                self.callback(reading)
            
            # Check for critical values
            self._check_critical_values(reading)
            
        except struct.error as e:
            self.logger.error(f"Failed to parse packet: {e}")
    
    def _check_critical_values(self, reading: SensorReading) -> None:
        """Check for critical sensor readings requiring immediate attention"""
        if reading.smoke_ppm > 300:
            self.logger.warning(f"HIGH SMOKE LEVEL: {reading.smoke_ppm} ppm")
        
        if reading.co_ppm > 50:
            self.logger.warning(f"DANGEROUS CO LEVEL: {reading.co_ppm} ppm")
        
        if reading.flame_detected:
            self.logger.warning("FLAME DETECTED BY IR SENSOR")
        
        if reading.temperature > 60:
            self.logger.warning(f"HIGH TEMPERATURE: {reading.temperature}°C")
    
    def send_command(self, command: str) -> None:
        """Send command to Arduino"""
        if self.serial_conn and self.serial_conn.is_open:
            cmd_bytes = f"${command}\n".encode('utf-8')
            self.serial_conn.write(cmd_bytes)
            self.logger.debug(f"Sent command: {command}")
    
    def calibrate_sensors(self) -> bool:
        """Initiate sensor calibration sequence"""
        self.logger.info("Starting sensor calibration...")
        self.send_command("CALIBRATE")
        
        # Wait for calibration to complete
        time.sleep(10)
        
        # Request calibration results
        self.send_command("CAL_STATUS")
        return True
    
    def get_latest_reading(self) -> Optional[SensorReading]:
        """Get the most recent sensor reading"""
        try:
            # Get all available readings and return the latest
            reading = None
            while not self.data_queue.empty():
                reading = self.data_queue.get_nowait()
            return reading
        except queue.Empty:
            return None
    
    def reconnect(self) -> bool:
        """Attempt to reconnect to Arduino"""
        self.logger.info("Attempting to reconnect to Arduino...")
        self.disconnect()
        time.sleep(2)
        
        if self.connect():
            self.start_monitoring()
            return True
        return False
    
    def disconnect(self) -> None:
        """Disconnect from Arduino"""
        self.is_running = False
        
        if self.read_thread:
            self.read_thread.join(timeout=5)
        
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        
        self.logger.info("Disconnected from Arduino")
    
    def get_statistics(self) -> Dict:
        """Get communication statistics"""
        return {
            "total_readings": self.total_readings,
            "error_count": self.error_count,
            "queue_size": self.data_queue.qsize(),
            "connected": bool(self.serial_conn and self.serial_conn.is_open),
            "port": self.port,
            "last_heartbeat": time.time() - self.last_heartbeat
        }
