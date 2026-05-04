import docker
import os
import tempfile
import time
from .config import settings

client = docker.DockerClient(base_url=settings.docker_host)

LANG_CONFIGS = {
    "python": {
        "image": "python:3.10-slim",
        "filename": "solution.py",
        "command": "python3 solution.py < input.txt",
        "build": None
    },
    "cpp": {
        "image": "gcc:latest",
        "filename": "solution.cpp",
        "command": "./solution < input.txt",
        "build": "g++ solution.cpp -o solution"
    },
    "java": {
        "image": "openjdk:17-slim",
        "filename": "Solution.java",
        "command": "java Solution < input.txt",
        "build": "javac Solution.java"
    },
    "go": {
        "image": "golang:1.20-alpine",
        "filename": "solution.go",
        "command": "./solution < input.txt",
        "build": "go build -o solution solution.go"
    }
}

def run_code(language, code_body, input_text, time_limit, memory_limit):
    lang_config = LANG_CONFIGS.get(language.lower())
    if not lang_config:
        return {"status": "Error", "message": f"Unsupported language: {language}"}
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Write code to file
        filename = lang_config["filename"]
        code_path = os.path.join(temp_dir, filename)
        with open(code_path, "w") as f:
            f.write(code_body)
        
        # Write input to file
        input_path = os.path.join(temp_dir, "input.txt")
        with open(input_path, "w") as f:
            f.write(input_text)
        
        # Determine command
        build_cmd = lang_config["build"]
        run_cmd = lang_config["command"]
        
        if build_cmd:
            full_command = f"{build_cmd} && {run_cmd}"
        else:
            full_command = run_cmd
        
        try:
            container = client.containers.run(
                image=lang_config["image"],
                command=f'sh -c "{full_command}"',
                volumes={temp_dir: {"bind": "/code", "mode": "rw"}},
                working_dir="/code",
                network_disabled=True,
                mem_limit=f"{memory_limit}m",
                cpu_quota=50000,
                read_only=False, # Allowed for compilation & temp file writing
                detach=True,
            )
            
            start_time = time.time()
            exit_code = None
            timeout = False
            
            # Monitoring loop
            while time.time() - start_time < time_limit:
                container.reload()
                if container.status == "exited":
                    exit_code = container.attrs["State"]["ExitCode"]
                    break
                time.sleep(0.1)
            else:
                container.kill()
                timeout = True
            
            execution_time = (time.time() - start_time) * 1000 # in ms
            stdout = container.logs(stdout=True, stderr=False).decode("utf-8")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8")
            
            # Memory usage placeholder
            memory_usage = 0 
            
            container.remove()
            
            if timeout:
                return {"status": "TLE", "time": execution_time, "memory": memory_usage}
            if exit_code != 0:
                # Check for compile error vs runtime error
                if build_cmd and "error" in stderr.lower():
                    return {"status": "Compile Error", "error": stderr, "time": execution_time, "memory": memory_usage}
                return {"status": "Runtime Error", "error": stderr, "time": execution_time, "memory": memory_usage}
            
            return {"status": "Success", "output": stdout, "time": execution_time, "memory": memory_usage}
            
        except Exception as e:
            return {"status": "Judge Error", "message": str(e)}

def judge_submission(problem_data, test_cases, language, code_body):
    final_status = "Accepted"
    max_time = 0
    max_memory = 0
    error_msg = None
    
    for tc in test_cases:
        result = run_code(
            language, 
            code_body, 
            tc["input_text"], 
            problem_data["time_limit_sec"], 
            problem_data["memory_limit_mb"]
        )
        
        if result["status"] == "TLE":
            return "TLE", result["time"], result["memory"], "Time Limit Exceeded"
        if result["status"] == "Compile Error":
            return "Compile Error", 0, 0, result["error"]
        if result["status"] == "Runtime Error":
            return "Runtime Error", result["time"], result["memory"], result["error"]
        if result["status"] == "Judge Error":
            return "Judge Error", 0, 0, result["message"]
        
        # Compare output (strip trailing whitespaces/newlines)
        if result["output"].strip() != tc["expected_output"].strip():
            return "Wrong Answer", result["time"], result["memory"], f"Failed on a test case"
        
        max_time = max(max_time, result["time"])
        max_memory = max(max_memory, result["memory"])
    
    return final_status, max_time, max_memory, None
