#!/usr/bin/env python3
"""
Celery Worker Manager
Manages Celery workers for different task types
"""

import os
import subprocess
import signal
import time
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

class CeleryWorkerManager:
    """Manages Celery worker processes"""
    
    def __init__(self):
        self.workers = {}
        self.celery_app = "tasks.celery_app:celery_app"
        
    def start_worker(self, name: str, queues: List[str], concurrency: int = 2):
        """Start a Celery worker"""
        if name in self.workers:
            print(f"Worker {name} is already running")
            return
            
        cmd = [
            "celery", "worker",
            "--app", self.celery_app,
            "--queues", ",".join(queues),
            "--concurrency", str(concurrency),
            "--loglevel", "info",
            "--hostname", f"{name}@%h"
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.workers[name] = {
                'process': process,
                'queues': queues,
                'concurrency': concurrency,
                'started_at': time.time()
            }
            
            print(f"✅ Started {name} worker (queues: {queues}, concurrency: {concurrency})")
            
        except Exception as e:
            print(f"❌ Failed to start {name} worker: {e}")
    
    def stop_worker(self, name: str):
        """Stop a Celery worker"""
        if name not in self.workers:
            print(f"Worker {name} is not running")
            return
            
        worker = self.workers[name]
        process = worker['process']
        
        try:
            process.terminate()
            process.wait(timeout=10)
            print(f"✅ Stopped {name} worker")
            
        except subprocess.TimeoutExpired:
            process.kill()
            print(f"⚠️  Force killed {name} worker")
            
        del self.workers[name]
    
    def start_all_workers(self):
        """Start all configured workers"""
        worker_configs = [
            ("scraping", ["scraping"], 2),
            ("analysis", ["analysis"], 4),
            ("twitter", ["twitter"], 2),
            ("maintenance", ["maintenance", "monitoring"], 1)
        ]
        
        for name, queues, concurrency in worker_configs:
            self.start_worker(name, queues, concurrency)
            time.sleep(2)  # Stagger startup
    
    def stop_all_workers(self):
        """Stop all running workers"""
        for name in list(self.workers.keys()):
            self.stop_worker(name)
    
    def get_status(self) -> Dict:
        """Get status of all workers"""
        status = {}
        
        for name, worker in self.workers.items():
            process = worker['process']
            status[name] = {
                'pid': process.pid,
                'queues': worker['queues'],
                'concurrency': worker['concurrency'],
                'running': process.poll() is None,
                'uptime': time.time() - worker['started_at']
            }
        
        return status
    
    def restart_worker(self, name: str):
        """Restart a specific worker"""
        if name in self.workers:
            self.stop_worker(name)
            time.sleep(2)
            
            # Recreate worker with same config
            worker = self.workers.get(name, {})
            if worker:
                self.start_worker(name, worker['queues'], worker['concurrency'])

def main():
    """Main function for worker management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Celery Worker Manager")
    parser.add_argument('command', choices=['start', 'stop', 'restart', 'status', 'start-all'],
                       help='Command to run')
    parser.add_argument('--worker', help='Worker name for start/stop/restart')
    parser.add_argument('--queues', help='Comma-separated queue names')
    parser.add_argument('--concurrency', type=int, default=2, help='Worker concurrency')
    
    args = parser.parse_args()
    
    manager = CeleryWorkerManager()
    
    if args.command == 'start':
        if not args.worker or not args.queues:
            print("❌ --worker and --queues required for start command")
            return
        
        queues = args.queues.split(',')
        manager.start_worker(args.worker, queues, args.concurrency)
        
    elif args.command == 'stop':
        if not args.worker:
            print("❌ --worker required for stop command")
            return
        
        manager.stop_worker(args.worker)
        
    elif args.command == 'restart':
        if not args.worker:
            print("❌ --worker required for restart command")
            return
        
        manager.restart_worker(args.worker)
        
    elif args.command == 'status':
        status = manager.get_status()
        print("Worker Status:")
        for name, info in status.items():
            print(f"  {name}: {'🟢' if info['running'] else '🔴'} (PID: {info['pid']}, Queues: {info['queues']})")
            
    elif args.command == 'start-all':
        manager.start_all_workers()
        
        # Keep running to maintain workers
        try:
            while True:
                time.sleep(10)
                # Check if any workers died
                status = manager.get_status()
                for name, info in status.items():
                    if not info['running']:
                        print(f"⚠️  Worker {name} died, restarting...")
                        manager.restart_worker(name)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down workers...")
            manager.stop_all_workers()

if __name__ == "__main__":
    main() 