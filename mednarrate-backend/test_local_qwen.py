import asyncio
import time
import json
from app.services.llm_client import llm_client_instance
from app.services.translation_planner import execute_translation_plan

async def run_diagnostics():
    provider = llm_client_instance.get_provider("local")
    
    print("--- A. LocalProvider initialization ---")
    start_load = time.time()
    health = await provider.health_check()
    
    # We must trigger generate once to actually load the model in run_in_executor
    try:
        res = await provider.generate("Hi", timeout=45.0)
    except Exception as e:
        pass
        
    load_time = time.time() - start_load
    print(f"Model load time: {load_time:.2f}s")
    
    print("--- B. Model reuse & C. Small synthetic translation ---")
    prompt_small = "Translate to Hindi: The patient has a mild fever."
    start_req1 = time.time()
    res1 = await provider.generate(prompt_small, timeout=45.0)
    req1_time = time.time() - start_req1
    print(f"First generation latency: {req1_time:.2f}s")
    
    start_req2 = time.time()
    res2 = await provider.generate(prompt_small, timeout=45.0)
    req2_time = time.time() - start_req2
    print(f"Second generation latency: {req2_time:.2f}s")
    
    print("Tokens sec calculation...")
    in_toks = 15 # rough estimate
    out_toks = len(res1.get("content", "").split())
    print(f"Rough generation tokens/sec: {out_toks / req1_time:.2f}")

    print("--- D. Valid JSON output & E. Medical-anchor preservation ---")
    # Will use standard tests for this via pytest later, or run execute_translation_plan
    
    print("--- J. Realistic MedNarrate test ---")
    realistic_prompt = "Translate this long medical text. Patient shows signs of cardiomegaly and bilateral pulmonary opacities consistent with pneumonia..." * 50
    start_long = time.time()
    try:
        # H. Local timeout/failure behavior & I. No orphaned background inference
        res_long = await provider.generate(realistic_prompt, timeout=10.0) # short timeout to test
        long_time = time.time() - start_long
        print(f"Realistic test completed in {long_time:.2f}s")
    except Exception as e:
        print(f"Realistic test timed out/failed as expected: {e}")
        long_time = time.time() - start_long
        print(f"Time taken to abort: {long_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(run_diagnostics())

import subprocess
subprocess.run(['pytest', 'tests/test_translation_pipeline.py'])
subprocess.run(['python', 'test_failover_mock.py'])
