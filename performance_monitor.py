import time
from typing import Dict, List
from collections import deque

class PerformanceMonitor:
    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self.decision_times = deque(maxlen=max_samples)
        self.redis_operation_times = deque(maxlen=max_samples)
        self.fallback_events = []
        
        self.metrics = {
            'total_decisions': 0,
            'avg_decision_time': 0.0,
            'max_decision_time': 0.0,
            'redis_failures': 0,
            'fallback_activations': 0,
            'performance_warnings': 0
        }
        
        # Performance thresholds
        self.decision_time_warning = 200  # ms
        self.decision_time_critical = 500  # ms
        self.redis_time_warning = 50  # ms
        
    def track_decision_time(self, decision_time_ms: float):
        """Track decision making performance"""
        self.decision_times.append(decision_time_ms)
        self.metrics['total_decisions'] += 1
        
        # Update running statistics
        if self.decision_times:
            self.metrics['avg_decision_time'] = sum(self.decision_times) / len(self.decision_times)
            self.metrics['max_decision_time'] = max(self.decision_times)
        
        # Check for performance issues
        if decision_time_ms > self.decision_time_critical:
            self.metrics['performance_warnings'] += 1
            print(f"CRITICAL: Very slow decision time: {decision_time_ms:.1f}ms")
        elif decision_time_ms > self.decision_time_warning:
            self.metrics['performance_warnings'] += 1
            print(f"WARNING: Slow decision time: {decision_time_ms:.1f}ms")
    
    def track_redis_operation(self, operation_time_ms: float, success: bool):
        """Track Redis operation performance"""
        self.redis_operation_times.append(operation_time_ms)
        
        if not success:
            self.metrics['redis_failures'] += 1
        
        if operation_time_ms > self.redis_time_warning:
            print(f"WARNING: Slow Redis operation: {operation_time_ms:.1f}ms")
    
    def record_fallback_event(self, reason: str):
        """Record when fallback to JSON mode occurs"""
        self.fallback_events.append({
            'timestamp': time.time(),
            'reason': reason
        })
        self.metrics['fallback_activations'] += 1
        print(f"Fallback event recorded: {reason}")
    
    def should_disable_features(self) -> bool:
        """Determine if enhanced features should be disabled due to performance"""
        if len(self.decision_times) < 10:
            return False
        
        # Check recent performance
        recent_times = list(self.decision_times)[-10:]
        avg_recent = sum(recent_times) / len(recent_times)
        
        # Disable if consistently slow
        if avg_recent > self.decision_time_critical:
            print("Disabling enhanced features due to poor performance")
            return True
        
        # Disable if too many fallbacks recently
        recent_fallbacks = [
            event for event in self.fallback_events
            if time.time() - event['timestamp'] < 60  # Last minute
        ]
        
        if len(recent_fallbacks) > 5:
            print("Disabling enhanced features due to frequent fallbacks")
            return True
        
        return False
    
    def get_performance_report(self) -> Dict:
        """Get comprehensive performance report"""
        report = self.metrics.copy()
        
        if self.decision_times:
            recent_decisions = list(self.decision_times)[-100:]  # Last 100 decisions
            report['recent_avg_decision_time'] = sum(recent_decisions) / len(recent_decisions)
            report['recent_max_decision_time'] = max(recent_decisions)
        
        if self.redis_operation_times:
            recent_redis = list(self.redis_operation_times)[-100:]
            report['recent_avg_redis_time'] = sum(recent_redis) / len(recent_redis)
            report['recent_max_redis_time'] = max(recent_redis)
        
        # Performance status
        if report.get('recent_avg_decision_time', 0) > self.decision_time_critical:
            report['status'] = 'critical'
        elif report.get('recent_avg_decision_time', 0) > self.decision_time_warning:
            report['status'] = 'warning'
        else:
            report['status'] = 'good'
        
        return report
    
    def print_performance_summary(self):
        """Print a summary of performance metrics"""
        report = self.get_performance_report()
        
        print("\n=== Performance Summary ===")
        print(f"Total decisions: {report['total_decisions']}")
        print(f"Average decision time: {report['avg_decision_time']:.1f}ms")
        print(f"Max decision time: {report['max_decision_time']:.1f}ms")
        print(f"Redis failures: {report['redis_failures']}")
        print(f"Fallback activations: {report['fallback_activations']}")
        print(f"Performance warnings: {report['performance_warnings']}")
        print(f"Status: {report['status'].upper()}")
        
        if 'recent_avg_decision_time' in report:
            print(f"Recent avg decision time: {report['recent_avg_decision_time']:.1f}ms")
        
        print("===========================\n")
    
    def reset_metrics(self):
        """Reset all performance metrics"""
        self.decision_times.clear()
        self.redis_operation_times.clear()
        self.fallback_events.clear()
        
        for key in self.metrics:
            if isinstance(self.metrics[key], (int, float)):
                self.metrics[key] = 0
                
        print("Performance metrics reset")
