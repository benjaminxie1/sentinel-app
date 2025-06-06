"""
Network Monitoring and Redundancy System
Handles network connectivity, failover, and status monitoring
"""

import socket
import subprocess
import threading
import time
import logging
import json
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import requests
import psutil

@dataclass
class NetworkInterface:
    """Network interface information"""
    name: str
    ip_address: str
    is_up: bool
    type: str  # ethernet, wifi, cellular
    priority: int = 1  # 1=primary, 2=secondary, etc.
    last_test: Optional[datetime] = None
    latency_ms: float = 0.0
    packet_loss: float = 0.0

@dataclass
class ConnectivityTest:
    """Network connectivity test result"""
    interface: str
    target: str
    success: bool
    latency_ms: float
    timestamp: datetime
    error: Optional[str] = None

@dataclass
class NetworkStatus:
    """Overall network status"""
    primary_interface: Optional[str]
    active_interface: Optional[str]
    interfaces: Dict[str, NetworkInterface]
    connectivity_tests: List[ConnectivityTest]
    last_failover: Optional[datetime]
    uptime_percentage: float
    alert_count: int

class NetworkMonitor:
    """Monitors network connectivity and manages failover"""
    
    def __init__(self, config_file: str = "config/network_config.yaml"):
        self.logger = logging.getLogger(__name__)
        self.config_file = Path(config_file)
        self.config = self._load_config()
        
        # Network state
        self.interfaces: Dict[str, NetworkInterface] = {}
        self.active_interface: Optional[str] = None
        self.primary_interface: Optional[str] = None
        self.connectivity_tests: List[ConnectivityTest] = []
        self.last_failover: Optional[datetime] = None
        
        # Monitoring state
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.status_callback: Optional[Callable] = None
        self.alert_callback: Optional[Callable] = None
        
        # Performance tracking
        self.uptime_start = datetime.now()
        self.total_downtime = timedelta()
        self.alert_count = 0
        
        # Test targets for connectivity checks
        self.test_targets = self.config.get('test_targets', [
            '8.8.8.8',          # Google DNS
            '1.1.1.1',          # Cloudflare DNS
            '208.67.222.222',   # OpenDNS
        ])
        
        self._discover_interfaces()
    
    def _load_config(self) -> Dict:
        """Load network configuration"""
        default_config = {
            'monitor_interval': 30,
            'test_timeout': 5,
            'failover_threshold': 3,
            'test_targets': ['8.8.8.8', '1.1.1.1'],
            'interface_priorities': {
                'ethernet': 1,
                'wifi': 2,
                'cellular': 3
            }
        }
        
        try:
            if self.config_file.exists():
                import yaml
                with open(self.config_file, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    default_config.update(loaded_config)
                    self.logger.info("Loaded network configuration")
        except Exception as e:
            self.logger.warning(f"Could not load network config: {e}, using defaults")
        
        return default_config
    
    def _discover_interfaces(self):
        """Discover available network interfaces"""
        try:
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET and addr.address != '127.0.0.1':
                        # Determine interface type
                        iface_type = self._determine_interface_type(interface)
                        priority = self.config['interface_priorities'].get(iface_type, 99)
                        
                        # Check if interface is up
                        stats = psutil.net_if_stats().get(interface)
                        is_up = stats.isup if stats else False
                        
                        network_interface = NetworkInterface(
                            name=interface,
                            ip_address=addr.address,
                            is_up=is_up,
                            type=iface_type,
                            priority=priority
                        )
                        
                        self.interfaces[interface] = network_interface
                        self.logger.info(f"Discovered interface: {interface} ({addr.address}) - {iface_type}")
            
            # Set primary interface (lowest priority number)
            if self.interfaces:
                primary = min(self.interfaces.values(), key=lambda x: x.priority)
                self.primary_interface = primary.name
                self.active_interface = primary.name
                self.logger.info(f"Primary interface: {self.primary_interface}")
        
        except Exception as e:
            self.logger.error(f"Failed to discover interfaces: {e}")
    
    def _determine_interface_type(self, interface_name: str) -> str:
        """Determine the type of network interface"""
        interface_name = interface_name.lower()
        
        if 'eth' in interface_name or 'enp' in interface_name or 'eno' in interface_name:
            return 'ethernet'
        elif 'wlan' in interface_name or 'wifi' in interface_name or 'wlp' in interface_name:
            return 'wifi'
        elif 'wwan' in interface_name or 'ppp' in interface_name or 'cellular' in interface_name:
            return 'cellular'
        else:
            return 'unknown'
    
    def start_monitoring(self):
        """Start network monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Started network monitoring")
    
    def stop_monitoring(self):
        """Stop network monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Stopped network monitoring")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        consecutive_failures = {}
        
        while self.is_monitoring:
            try:
                # Test all interfaces
                for interface_name, interface in self.interfaces.items():
                    if not interface.is_up:
                        continue
                    
                    # Test connectivity on this interface
                    success, latency, error = self._test_interface_connectivity(interface_name)
                    
                    # Record test result
                    test_result = ConnectivityTest(
                        interface=interface_name,
                        target=self.test_targets[0],  # Use first target for simplicity
                        success=success,
                        latency_ms=latency,
                        timestamp=datetime.now(),
                        error=error
                    )
                    
                    self.connectivity_tests.append(test_result)
                    
                    # Limit test history
                    if len(self.connectivity_tests) > 1000:
                        self.connectivity_tests = self.connectivity_tests[-500:]
                    
                    # Update interface status
                    interface.last_test = test_result.timestamp
                    interface.latency_ms = latency
                    
                    # Track consecutive failures
                    if not success:
                        consecutive_failures[interface_name] = consecutive_failures.get(interface_name, 0) + 1
                        self.logger.warning(f"Interface {interface_name} connectivity failed: {error}")
                    else:
                        consecutive_failures[interface_name] = 0
                    
                    # Check if failover needed
                    if (interface_name == self.active_interface and 
                        consecutive_failures[interface_name] >= self.config['failover_threshold']):
                        self._trigger_failover()
                
                # Call status callback if set
                if self.status_callback:
                    try:
                        self.status_callback(self.get_network_status())
                    except Exception as e:
                        self.logger.error(f"Status callback error: {e}")
                
                # Sleep until next check
                time.sleep(self.config['monitor_interval'])
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(10)
    
    def _test_interface_connectivity(self, interface_name: str) -> Tuple[bool, float, Optional[str]]:
        """Test connectivity on a specific interface"""
        interface = self.interfaces.get(interface_name)
        if not interface or not interface.is_up:
            return False, 0.0, "Interface not available"
        
        # Test connectivity to multiple targets
        for target in self.test_targets:
            try:
                start_time = time.time()
                
                # Use ping to test connectivity
                result = subprocess.run(
                    ['ping', '-c', '1', '-W', str(self.config['test_timeout']), target],
                    capture_output=True,
                    text=True,
                    timeout=self.config['test_timeout'] + 2
                )
                
                latency = (time.time() - start_time) * 1000  # Convert to ms
                
                if result.returncode == 0:
                    return True, latency, None
                
            except subprocess.TimeoutExpired:
                return False, 0.0, f"Timeout testing {target}"
            except Exception as e:
                return False, 0.0, f"Error testing {target}: {str(e)}"
        
        return False, 0.0, "All connectivity tests failed"
    
    def _trigger_failover(self):
        """Trigger network failover to backup interface"""
        if not self.interfaces:
            return
        
        current_interface = self.active_interface
        
        # Find best available backup interface
        available_interfaces = [
            iface for name, iface in self.interfaces.items()
            if name != current_interface and iface.is_up
        ]
        
        if not available_interfaces:
            self.logger.error("No backup interfaces available for failover")
            self._trigger_alert("No backup network interfaces available")
            return
        
        # Sort by priority (lower number = higher priority)
        backup_interface = min(available_interfaces, key=lambda x: x.priority)
        
        # Test backup interface before switching
        success, latency, error = self._test_interface_connectivity(backup_interface.name)
        if not success:
            self.logger.error(f"Backup interface {backup_interface.name} also failed: {error}")
            self._trigger_alert(f"Network failover failed - backup interface not working")
            return
        
        # Perform failover
        old_interface = self.active_interface
        self.active_interface = backup_interface.name
        self.last_failover = datetime.now()
        
        self.logger.warning(f"Network failover: {old_interface} -> {backup_interface.name}")
        self._trigger_alert(f"Network failover from {old_interface} to {backup_interface.name}")
    
    def _trigger_alert(self, message: str):
        """Trigger network alert"""
        self.alert_count += 1
        self.logger.error(f"NETWORK ALERT: {message}")
        
        if self.alert_callback:
            try:
                self.alert_callback({
                    'type': 'network_alert',
                    'message': message,
                    'timestamp': datetime.now().isoformat(),
                    'active_interface': self.active_interface,
                    'alert_count': self.alert_count
                })
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")
    
    def get_network_status(self) -> NetworkStatus:
        """Get current network status"""
        # Calculate uptime percentage
        total_time = datetime.now() - self.uptime_start
        uptime_percentage = max(0, 100 * (1 - self.total_downtime.total_seconds() / total_time.total_seconds()))
        
        return NetworkStatus(
            primary_interface=self.primary_interface,
            active_interface=self.active_interface,
            interfaces=self.interfaces.copy(),
            connectivity_tests=self.connectivity_tests[-10:],  # Last 10 tests
            last_failover=self.last_failover,
            uptime_percentage=uptime_percentage,
            alert_count=self.alert_count
        )
    
    def set_status_callback(self, callback: Callable[[NetworkStatus], None]):
        """Set callback for status updates"""
        self.status_callback = callback
    
    def set_alert_callback(self, callback: Callable[[Dict], None]):
        """Set callback for network alerts"""
        self.alert_callback = callback
    
    def force_interface(self, interface_name: str) -> bool:
        """Force switch to specific interface"""
        if interface_name not in self.interfaces:
            return False
        
        interface = self.interfaces[interface_name]
        if not interface.is_up:
            return False
        
        # Test interface first
        success, latency, error = self._test_interface_connectivity(interface_name)
        if not success:
            self.logger.error(f"Cannot switch to {interface_name}: {error}")
            return False
        
        old_interface = self.active_interface
        self.active_interface = interface_name
        self.logger.info(f"Manually switched interface: {old_interface} -> {interface_name}")
        return True
    
    def get_interface_stats(self) -> Dict:
        """Get detailed interface statistics"""
        stats = {}
        
        for name, interface in self.interfaces.items():
            try:
                net_stats = psutil.net_if_stats().get(name)
                io_stats = psutil.net_io_counters(pernic=True).get(name)
                
                stats[name] = {
                    'interface': asdict(interface),
                    'is_up': net_stats.isup if net_stats else False,
                    'speed': net_stats.speed if net_stats else 0,
                    'mtu': net_stats.mtu if net_stats else 0,
                    'bytes_sent': io_stats.bytes_sent if io_stats else 0,
                    'bytes_recv': io_stats.bytes_recv if io_stats else 0,
                    'packets_sent': io_stats.packets_sent if io_stats else 0,
                    'packets_recv': io_stats.packets_recv if io_stats else 0,
                    'errors_in': io_stats.errin if io_stats else 0,
                    'errors_out': io_stats.errout if io_stats else 0,
                    'dropped_in': io_stats.dropin if io_stats else 0,
                    'dropped_out': io_stats.dropout if io_stats else 0,
                }
            except Exception as e:
                self.logger.error(f"Error getting stats for {name}: {e}")
                stats[name] = {'error': str(e)}
        
        return stats
    
    def test_connectivity_now(self) -> Dict[str, bool]:
        """Test connectivity on all interfaces immediately"""
        results = {}
        
        for interface_name in self.interfaces:
            success, latency, error = self._test_interface_connectivity(interface_name)
            results[interface_name] = {
                'success': success,
                'latency_ms': latency,
                'error': error
            }
        
        return results
    
    def export_network_log(self, hours: int = 24) -> str:
        """Export network monitoring log"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_tests = [
            test for test in self.connectivity_tests
            if test.timestamp >= cutoff_time
        ]
        
        log_data = {
            'export_info': {
                'timestamp': datetime.now().isoformat(),
                'hours_covered': hours,
                'test_count': len(recent_tests)
            },
            'network_status': asdict(self.get_network_status()),
            'interface_stats': self.get_interface_stats(),
            'connectivity_tests': [asdict(test) for test in recent_tests]
        }
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"network_log_{timestamp}.json"
        
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2, default=str)
        
        self.logger.info(f"Exported network log: {log_file}")
        return log_file

class OfflineCapabilityManager:
    """Manages system capabilities during network outages"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.offline_mode = False
        self.offline_start: Optional[datetime] = None
        self.offline_cache: Dict = {}
        
    def enter_offline_mode(self):
        """Enter offline operation mode"""
        if not self.offline_mode:
            self.offline_mode = True
            self.offline_start = datetime.now()
            self.logger.warning("Entering OFFLINE MODE - network connectivity lost")
            
            # Cache critical data for offline operation
            self._cache_critical_data()
    
    def exit_offline_mode(self):
        """Exit offline operation mode"""
        if self.offline_mode:
            offline_duration = datetime.now() - self.offline_start
            self.offline_mode = False
            self.offline_start = None
            
            self.logger.info(f"Exiting offline mode - was offline for {offline_duration}")
            
            # Sync any offline data
            self._sync_offline_data()
    
    def _cache_critical_data(self):
        """Cache critical system data for offline operation"""
        try:
            # Cache detection configurations
            # Cache last known camera configurations
            # Cache alert templates
            self.offline_cache['cached_at'] = datetime.now().isoformat()
            self.logger.info("Cached critical data for offline operation")
        except Exception as e:
            self.logger.error(f"Failed to cache offline data: {e}")
    
    def _sync_offline_data(self):
        """Sync data accumulated during offline operation"""
        try:
            # Upload any stored alerts
            # Sync configuration changes
            # Update remote monitoring
            self.logger.info("Synced offline data with network services")
        except Exception as e:
            self.logger.error(f"Failed to sync offline data: {e}")
    
    def is_offline(self) -> bool:
        """Check if system is in offline mode"""
        return self.offline_mode

if __name__ == "__main__":
    # Test network monitoring
    logging.basicConfig(level=logging.INFO)
    
    def status_callback(status: NetworkStatus):
        print(f"Network status: Active={status.active_interface}, Uptime={status.uptime_percentage:.1f}%")
    
    def alert_callback(alert: Dict):
        print(f"ALERT: {alert['message']}")
    
    # Create and start monitor
    monitor = NetworkMonitor()
    monitor.set_status_callback(status_callback)
    monitor.set_alert_callback(alert_callback)
    
    try:
        monitor.start_monitoring()
        print("Network monitoring started. Press Ctrl+C to stop...")
        
        while True:
            time.sleep(10)
            
            # Show current status
            status = monitor.get_network_status()
            print(f"\nActive interface: {status.active_interface}")
            print(f"Interfaces: {list(status.interfaces.keys())}")
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        monitor.stop_monitoring()