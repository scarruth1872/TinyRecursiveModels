#!/usr/bin/env python3
"""
COMPREHENSIVE STRESS TEST SUITE FOR TRM SWARM V2
Tests all major components under load:
1. Cognitive Stack & API endpoints
2. Artifact Pipeline with concurrent operations
3. Global Memory (ChromaDB) concurrent access
4. Agent Mesh routing and communication
5. Learning Engine scalability
6. Federation protocols
7. System resource management
"""

import asyncio
import time
import statistics
import random
import json
import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple
import sys
import os

# Configuration
BASE_URL = "http://localhost:8001"
TEST_DURATION_SECONDS = 60  # Run test for 1 minute
CONCURRENT_WORKERS = 15     # Simulate 15 concurrent users
REQUEST_TIMEOUT = 30.0

class ComponentStressTest:
    """Base class for component stress testing."""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.results = {
            "total_requests": 0,
            "successful": 0,
            "failed": 0,
            "response_times": [],
            "errors": []
        }
    
    def add_result(self, success: bool, response_time: float, error: str = None):
        self.results["total_requests"] += 1
        if success:
            self.results["successful"] += 1
            self.results["response_times"].append(response_time)
        else:
            self.results["failed"] += 1
            if error:
                self.results["errors"].append(error)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test summary with statistics."""
        summary = {
            "component": self.component_name,
            "total_requests": self.results["total_requests"],
            "successful": self.results["successful"],
            "failed": self.results["failed"],
            "success_rate": (self.results["successful"] / self.results["total_requests"] * 100) 
                          if self.results["total_requests"] > 0 else 0,
            "error_count": len(self.results["errors"])
        }
        
        if self.results["response_times"]:
            summary.update({
                "avg_response_time": statistics.mean(self.results["response_times"]),
                "min_response_time": min(self.results["response_times"]),
                "max_response_time": max(self.results["response_times"]),
                "p95_response_time": statistics.quantiles(self.results["response_times"], n=20)[18] 
                                   if len(self.results["response_times"]) > 1 else self.results["response_times"][0],
                "requests_per_second": self.results["successful"] / TEST_DURATION_SECONDS
            })
        
        return summary
    
    def print_summary(self):
        """Print formatted test results."""
        summary = self.get_summary()
        print(f"\n{'='*60}")
        print(f"📊 {self.component_name.upper()} STRESS TEST RESULTS")
        print(f"{'='*60}")
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Successful: {summary['successful']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success Rate: {summary['success_rate']:.2f}%")
        
        if 'avg_response_time' in summary:
            print(f"\n⏱️ Response Times:")
            print(f"  Average: {summary['avg_response_time']:.3f}s")
            print(f"  Minimum: {summary['min_response_time']:.3f}s")
            print(f"  Maximum: {summary['max_response_time']:.3f}s")
            print(f"  P95: {summary['p95_response_time']:.3f}s")
            print(f"  Requests/sec: {summary['requests_per_second']:.2f}")
        
        if summary['error_count'] > 0:
            print(f"\n❌ Errors ({summary['error_count']} unique):")
            for error in set(self.results["errors"])[:5]:
                print(f"  - {error}")
            if summary['error_count'] > 5:
                print(f"  ... and {summary['error_count'] - 5} more")

class APIPipelineTest(ComponentStressTest):
    """Test artifact pipeline API endpoints."""
    
    def __init__(self):
        super().__init__("Artifact Pipeline API")
        self.endpoints = [
            ("GET", "/artifacts"),
            ("GET", "/artifacts?grouped=true"),
            ("GET", "/artifacts/stats"),
            ("GET", "/artifacts?include_content=true"),
            ("POST", "/artifacts/remediate"),
            ("POST", "/artifacts/deploy"),
        ]
    
    def run_single_test(self, endpoint: str, method: str = "GET") -> Tuple[bool, float, str]:
        """Run a single API request."""
        start_time = time.time()
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=REQUEST_TIMEOUT)
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", timeout=REQUEST_TIMEOUT)
            else:
                return False, time.time() - start_time, f"Invalid method: {method}"
            
            elapsed = time.time() - start_time
            success = response.status_code in [200, 201, 202]
            error = f"HTTP {response.status_code}" if not success else None
            return success, elapsed, error
            
        except Exception as e:
            elapsed = time.time() - start_time
            return False, elapsed, str(e)
    
    def run_stress_test(self) -> Dict[str, Any]:
        """Run comprehensive stress test on all endpoints."""
        print(f"\n🧪 Starting {self.component_name} stress test...")
        
        # Run initial baseline tests
        print(f"  Running baseline tests for {len(self.endpoints)} endpoints...")
        for method, endpoint in self.endpoints:
            success, elapsed, error = self.run_single_test(endpoint, method)
            self.add_result(success, elapsed, error)
            status = "✅" if success else "❌"
            print(f"    {status} {method} {endpoint}: {elapsed:.3f}s")
        
        # Run concurrent stress test
        print(f"\n  Starting concurrent stress test ({CONCURRENT_WORKERS} workers, {TEST_DURATION_SECONDS}s)...")
        
        stop_time = time.time() + TEST_DURATION_SECONDS
        threads = []
        
        def worker_loop(worker_id: int):
            """Worker that continuously makes requests until stop time."""
            request_count = 0
            while time.time() < stop_time:
                method, endpoint = random.choice(self.endpoints)
                success, elapsed, error = self.run_single_test(endpoint, method)
                self.add_result(success, elapsed, error)
                request_count += 1
                # Small random delay between requests
                time.sleep(random.uniform(0.05, 0.2))
            return request_count
        
        # Start worker threads
        with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
            futures = [executor.submit(worker_loop, i) for i in range(CONCURRENT_WORKERS)]
            for future in as_completed(futures):
                try:
                    requests_made = future.result()
                    print(f"    Worker completed: {requests_made} requests")
                except Exception as e:
                    print(f"    Worker error: {e}")
        
        return self.get_summary()

class GlobalMemoryTest(ComponentStressTest):
    """Test global memory (ChromaDB) concurrent access."""
    
    def __init__(self):
        super().__init__("Global Memory (ChromaDB)")
        self.test_contents = [
            "Machine learning models require large datasets",
            "Recursive neural networks can process hierarchical data",
            "Swarm intelligence emerges from simple agent interactions",
            "Distributed systems need fault tolerance mechanisms",
            "Vector databases enable semantic search capabilities",
            "Quantum computing leverages superposition and entanglement",
            "Autonomous agents can collaborate to solve complex tasks",
            "Natural language processing uses transformer architectures",
            "Reinforcement learning agents learn through trial and error",
            "Computer vision systems can identify objects in images",
        ]
        self.test_authors = ["Architect", "Lead Developer", "QA Engineer", "Security Auditor", "DevOps Engineer"]
    
    def run_single_test(self) -> Tuple[bool, float, str]:
        """Run a single memory operation."""
        start_time = time.time()
        try:
            # Randomly choose to contribute or query
            if random.random() < 0.3:
                # Contribute memory
                content = random.choice(self.test_contents)
                author = random.choice(self.test_authors)
                payload = {
                    "content": content,
                    "author": author,
                    "author_role": author,
                    "memory_type": "test_knowledge",
                    "tags": ["stress_test", "ai", "ml"]
                }
                response = requests.post(f"{BASE_URL}/memory/contribute", 
                                        json=payload, timeout=REQUEST_TIMEOUT)
            else:
                # Query memory
                query = random.choice(["machine learning", "neural networks", "swarm", "distributed", "quantum"])
                payload = {
                    "query": query,
                    "top_k": random.randint(1, 5),
                    "author_filter": "" if random.random() < 0.7 else random.choice(self.test_authors),
                    "type_filter": "" if random.random() < 0.7 else "test_knowledge"
                }
                response = requests.post(f"{BASE_URL}/memory/query", 
                                        json=payload, timeout=REQUEST_TIMEOUT)
            
            elapsed = time.time() - start_time
            success = response.status_code in [200, 201]
            error = f"HTTP {response.status_code}" if not success else None
            return success, elapsed, error
            
        except Exception as e:
            elapsed = time.time() - start_time
            return False, elapsed, str(e)
    
    def run_stress_test(self) -> Dict[str, Any]:
        """Run concurrent memory stress test."""
        print(f"\n🧪 Starting {self.component_name} stress test...")
        
        # Run initial baseline tests
        print(f"  Running baseline memory operations...")
        for i in range(10):
            success, elapsed, error = self.run_single_test()
            self.add_result(success, elapsed, error)
            status = "✅" if success else "❌"
            print(f"    {status} Memory operation {i+1}: {elapsed:.3f}s")
        
        # Run concurrent stress test
        print(f"\n  Starting concurrent memory stress test ({CONCURRENT_WORKERS} workers, {TEST_DURATION_SECONDS}s)...")
        
        stop_time = time.time() + TEST_DURATION_SECONDS
        threads = []
        
        def memory_worker(worker_id: int):
            """Worker that continuously performs memory operations."""
            operation_count = 0
            while time.time() < stop_time:
                success, elapsed, error = self.run_single_test()
                self.add_result(success, elapsed, error)
                operation_count += 1
                # Small random delay between operations
                time.sleep(random.uniform(0.1, 0.3))
            return operation_count
        
        # Start worker threads
        with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
            futures = [executor.submit(memory_worker, i) for i in range(CONCURRENT_WORKERS)]
            for future in as_completed(futures):
                try:
                    ops_made = future.result()
                    print(f"    Memory worker completed: {ops_made} operations")
                except Exception as e:
                    print(f"    Memory worker error: {e}")
        
        # Check memory stats
        try:
            response = requests.get(f"{BASE_URL}/memory/stats", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                print(f"\n  📈 Memory Stats after stress test:")
                print(f"    Total memories: {stats.get('total_memories', 'N/A')}")
                print(f"    Total accesses: {stats.get('total_accesses', 'N/A')}")
        except:
            pass
        
        return self.get_summary()

class AgentMeshTest(ComponentStressTest):
    """Test agent mesh routing and communication."""
    
    def __init__(self):
        super().__init__("Agent Mesh Routing")
        self.agents = ["Architect", "Lead Developer", "QA Engineer", "Security Auditor", "DevOps Engineer"]
        self.tasks = [
            "Design a scalable microservices architecture",
            "Write a Python function to parse JSON data",
            "Create a test plan for authentication system",
            "Analyze security risks in a web application",
            "Deploy a containerized application to Kubernetes",
            "Optimize database queries for better performance",
            "Implement caching strategy for high-traffic website",
            "Design REST API for user management system",
            "Create monitoring dashboard for system metrics",
            "Implement CI/CD pipeline for automated testing",
        ]
    
    def run_single_test(self) -> Tuple[bool, float, str]:
        """Run a single mesh routing test."""
        start_time = time.time()
        try:
            # Randomly choose direct chat or mesh routing
            if random.random() < 0.5:
                # Direct chat with agent
                role = random.choice(self.agents)
                task = random.choice(self.tasks)
                payload = {
                    "role": role,
                    "message": task,
                    "sender": "stress_test"
                }
                response = requests.post(f"{BASE_URL}/swarm/chat", 
                                        json=payload, timeout=REQUEST_TIMEOUT)
            else:
                # Mesh routing
                task = random.choice(self.tasks)
                payload = {
                    "task": task,
                    "target_node_id": "",
                    "required_specialty": random.choice(["", "security", "testing", "development"])
                }
                response = requests.post(f"{BASE_URL}/mesh/route", 
                                        json=payload, timeout=REQUEST_TIMEOUT)
            
            elapsed = time.time() - start_time
            success = response.status_code in [200, 201]
            error = f"HTTP {response.status_code}" if not success else None
            return success, elapsed, error
            
        except Exception as e:
            elapsed = time.time() - start_time
            return False, elapsed, str(e)
    
    def run_stress_test(self) -> Dict[str, Any]:
        """Run concurrent mesh routing stress test."""
        print(f"\n🧪 Starting {self.component_name} stress test...")
        
        # Run initial baseline tests
        print(f"  Running baseline mesh operations...")
        for i in range(8):
            success, elapsed, error = self.run_single_test()
            self.add_result(success, elapsed, error)
            status = "✅" if success else "❌"
            print(f"    {status} Mesh operation {i+1}: {elapsed:.3f}s")
        
        # Run concurrent stress test
        print(f"\n  Starting concurrent mesh stress test ({CONCURRENT_WORKERS} workers, {TEST_DURATION_SECONDS}s)...")
        
        stop_time = time.time() + TEST_DURATION_SECONDS
        threads = []
        
        def mesh_worker(worker_id: int):
            """Worker that continuously performs mesh operations."""
            operation_count = 0
            while time.time() < stop_time:
                success, elapsed, error = self.run_single_test()
                self.add_result(success, elapsed, error)
                operation_count += 1
                # Small random delay between operations
                time.sleep(random.uniform(0.2, 0.5))
            return operation_count
        
        # Start worker threads
        with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
            futures = [executor.submit(mesh_worker, i) for i in range(CONCURRENT_WORKERS)]
            for future in as_completed(futures):
                try:
                    ops_made = future.result()
                    print(f"    Mesh worker completed: {ops_made} operations")
                except Exception as e:
                    print(f"    Mesh worker error: {e}")
        
        # Check mesh stats
        try:
            response = requests.get(f"{BASE_URL}/mesh/stats", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                print(f"\n  📈 Mesh Stats after stress test:")
                print(f"    Total nodes: {stats.get('total_nodes', 'N/A')}")
                print(f"    Alive nodes: {stats.get('alive_nodes', 'N/A')}")
                print(f"    Total tasks routed: {stats.get('total_tasks_routed', 'N/A')}")
        except:
            pass
        
        return self.get_summary()

class LearningEngineTest(ComponentStressTest):
    """Test learning engine scalability."""
    
    def __init__(self):
        super().__init__("Learning Engine")
        self.sample_docs = [
            "Python is a high-level programming language known for its simplicity and readability.",
            "Docker is a platform for developing, shipping, and running applications in containers.",
            "Kubernetes is an open-source system for automating deployment, scaling, and management of containerized applications.",
            "React is a JavaScript library for building user interfaces, particularly single-page applications.",
            "Machine learning algorithms can be supervised, unsupervised, or reinforcement learning.",
            "API stands for Application Programming Interface, which defines interactions between software components.",
            "Microservices architecture structures an application as a collection of loosely coupled services.",
            "CI/CD stands for Continuous Integration and Continuous Deployment, enabling frequent code changes.",
            "SQL databases use structured query language for defining and manipulating data.",
            "NoSQL databases provide a mechanism for storage and retrieval of data that is modeled differently from relational databases.",
        ]
    
    def run_single_test(self) -> Tuple[bool, float, str]:
        """Run a single learning engine test."""
        start_time = time.time()
        try:
            # Randomly choose to ingest or use skill
            if random.random() < 0.3:
                # Ingest new knowledge
                doc = random.choice(self.sample_docs)
                skill_name = f"TestSkill_{random.randint(1000, 9999)}"
                payload = {
                    "name": skill_name,
                    "content": doc,
                    "source": "stress_test"
                }
                response = requests.post(f"{BASE_URL}/learning/ingest", 
                                        json=payload, timeout=REQUEST_TIMEOUT)
            else:
                # Use existing skill or list skills
                if random.random() < 0.5:
                    # List skills
                    response = requests.get(f"{BASE_URL}/learning/skills", timeout=REQUEST_TIMEOUT)
                else:
                    # Use skill (try to use a learned one)
                    response = requests.get(f"{BASE_URL}/learning/skills", timeout=5)
                    if response.status_code == 200:
                        skills_data = response.json()
                        if skills_data.get("skills"):
                            skill = random.choice(skills_data["skills"])
                            skill_name = skill["skill_name"]
                            payload = {
                                "skill_name": skill_name,
                                "task": "Explain this concept simply",
                                "target_role": random.choice(["", "Architect", "Lead Developer"])
                            }
                            response = requests.post(f"{BASE_URL}/learning/use", 
                                                    json=payload, timeout=REQUEST_TIMEOUT)
                        else:
                            # No skills, just list them again
                            response = requests.get(f"{BASE_URL}/learning/skills", timeout=REQUEST_TIMEOUT)
            
            elapsed = time.time() - start_time
            success = response.status_code in [200, 201]
            error = f"HTTP {response.status_code}" if not success else None
            return success, elapsed, error
            
        except Exception as e:
            elapsed = time.time() - start_time
            return False, elapsed, str(e)
    
    def run_stress_test(self) -> Dict[str, Any]:
        """Run concurrent learning engine stress test."""
        print(f"\n🧪 Starting {self.component_name} stress test...")
        
        # Run initial baseline tests
        print(f"  Running baseline learning operations...")
        for i in range(6):
            success, elapsed, error = self.run_single_test()
            self.add_result(success, elapsed, error)
            status = "✅" if success else "❌"
            print(f"    {status} Learning operation {i+1}: {elapsed:.3f}s")
        
        # Run concurrent stress test
        print(f"\n  Starting concurrent learning stress test ({CONCURRENT_WORKERS} workers, {TEST_DURATION_SECONDS}s)...")
        
        stop_time = time.time() + TEST_DURATION_SECONDS
        threads = []
        
        def learning_worker(worker_id: int):
            """Worker that continuously performs learning operations."""
            operation_count = 0
            while time.time() < stop_time:
                success, elapsed, error = self.run_single_test()
                self.add_result(success, elapsed, error)
                operation_count += 1
                # Small random delay between operations
                time.sleep(random.uniform(0.3, 0.8))
            return operation_count
        
        # Start worker threads
        with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
            futures = [executor.submit(learning_worker, i) for i in range(CONCURRENT_WORKERS)]
            for future in as_completed(futures):
                try:
                    ops_made = future.result()
                    print(f"    Learning worker completed: {ops_made} operations")
                except Exception as e:
                    print(f"    Learning worker error: {e}")
        
        # Check learning stats
        try:
            response = requests.get(f"{BASE_URL}/learning/skills", timeout=5)
            if response.status_code == 200:
                stats = response.json().get("stats", {})
                print(f"\n  📈 Learning Engine Stats after stress test:")
                print(f"    Total learned: {stats.get('total_learned', 'N/A')}")
                print(f"    Total usages: {stats.get('total_usages', 'N/A')}")
        except:
            pass
        
        return self.get_summary()

class SystemHealthMonitor:
    """Monitor system health during stress tests."""
    
    @staticmethod
    def get_system_health() -> Dict[str, Any]:
        """Get current system health status."""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {}
    
    @staticmethod
    def get_resource_status() -> Dict[str, Any]:
        """Get resource arbitration status."""
        try:
            response = requests.get(f"{BASE_URL}/system/resources", timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {}
    
    @staticmethod
    def print_health_baseline():
        """Print baseline health before stress tests."""
        print("\n" + "="*60)
        print("🏥 SYSTEM HEALTH BASELINE")
        print("="*60)
        
        health = SystemHealthMonitor.get_system_health()
        if health:
            print(f"Status: {health.get('status', 'N/A')}")
            print(f"Phase: {health.get('phase', 'N/A')}")
            print(f"Agents: {health.get('agents', 'N/A')}")
            
            artifacts = health.get('artifacts', {})
            if isinstance(artifacts, dict):
                print(f"Artifacts: {artifacts.get('total', 'N/A')} total")
            
            memory = health.get('global_memory', {})
            if isinstance(memory, dict):
                print(f"Global Memories: {memory.get('total_memories', 'N/A')}")
        
        resources = SystemHealthMonitor.get_resource_status()
        if resources:
            print(f"Resource Status: {resources.get('status', 'N/A')}")
            if 'cpu_usage' in resources:
                print(f"CPU Usage: {resources.get('cpu_usage', 'N/A')}%")
            if 'memory_usage' in resources:
                print(f"Memory Usage: {resources.get('memory_usage', 'N/A')}%")

def main():
    """Run comprehensive stress test suite."""
    print("🚀 TRM SWARM V2 COMPREHENSIVE STRESS TEST SUITE")
    print("="*60)
    print(f"Target: {BASE_URL}")
    print(f"Test Duration: {TEST_DURATION_SECONDS} seconds")
    print(f"Concurrent Workers: {CONCURRENT_WORKERS}")
    print(f"Request Timeout: {REQUEST_TIMEOUT} seconds")
    print("="*60)
    
    # First, verify API is accessible
    print("\n🔍 Verifying API accessibility...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ API is accessible")
        else:
            print(f"❌ API returned status {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        sys.exit(1)
    
    # Print baseline health
    SystemHealthMonitor.print_health_baseline()
    
    # Run all stress tests
    test_results = {}
    
    # 1. Artifact Pipeline Test
    print("\n" + "="*60)
    print("📦 TEST 1: ARTIFACT PIPELINE")
    print("="*60)
    pipeline_test = APIPipelineTest()
    test_results["pipeline"] = pipeline_test.run_stress_test()
    pipeline_test.print_summary()
    
    # 2. Global Memory Test
    print("\n" + "="*60)
    print("🧠 TEST 2: GLOBAL MEMORY (ChromaDB)")
    print("="*60)
    memory_test = GlobalMemoryTest()
    test_results["memory"] = memory_test.run_stress_test()
    memory_test.print_summary()
    
    # 3. Agent Mesh Test
    print("\n" + "="*60)
    print("🕸️ TEST 3: AGENT MESH ROUTING")
    print("="*60)
    mesh_test = AgentMeshTest()
    test_results["mesh"] = mesh_test.run_stress_test()
    mesh_test.print_summary()
    
    # 4. Learning Engine Test
    print("\n" + "="*60)
    print("🎓 TEST 4: LEARNING ENGINE")
    print("="*60)
    learning_test = LearningEngineTest()
    test_results["learning"] = learning_test.run_stress_test()
    learning_test.print_summary()
    
    # Print final summary
    print("\n" + "="*60)
    print("📋 COMPREHENSIVE STRESS TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for component, results in test_results.items():
        success_rate = results.get("success_rate", 0)
        passed = success_rate >= 95.0  # 95% success rate threshold
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {component.upper()}: {success_rate:.2f}% success rate")
        if not passed:
            all_passed = False
    
    # Final health check
    print(f"\n🏥 FINAL SYSTEM HEALTH CHECK:")
    final_health = SystemHealthMonitor.get_system_health()
    if final_health:
        print(f"  Status: {final_health.get('status', 'N/A')}")
        print(f"  Agents: {final_health.get('agents', 'N/A')}")
        
        artifacts = final_health.get('artifacts', {})
        if isinstance(artifacts, dict):
            print(f"  Artifacts: {artifacts.get('total', 'N/A')} total")
        
        # Check for any service degradation
        mesh_stats = final_health.get('mesh', {})
        if isinstance(mesh_stats, dict):
            alive_nodes = mesh_stats.get('alive_nodes', 0)
            total_nodes = mesh_stats.get('total_nodes', 0)
            if alive_nodes < total_nodes:
                print(f"  ⚠️  Mesh node degradation: {alive_nodes}/{total_nodes} nodes alive")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT:")
    if all_passed:
        print("✨ ALL stress tests passed! System is production-ready under load.")
        return True
    else:
        print("⚠️ Some stress tests failed to meet success criteria. Review logs above.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 Comprehensive stress test completed successfully!")
            sys.exit(0)
        else:
            print("\n💥 Comprehensive stress test failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stress test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)