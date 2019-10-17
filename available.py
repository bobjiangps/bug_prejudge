import os
import time


def get_cpu():
    # return float(os.popen("top -l 1 -s 0 | grep 'CPU usage'").read().split(",")[-1].strip().split(" ")[0].split("%")[0])
    s = "top -bn1 | grep Cpu | awk '{printf \"%.2f\", $5}'"
    return float(os.popen(s).read())


def get_mem():
    # return float(os.popen("top -l 1 -s 0 | grep PhysMem").read().split(",")[-1].strip().split(" ")[0].split("M")[0])
    s = "free -m | awk 'NR==2{printf \"%.2f\", ($4+$6+$7)*100/$2}'"
    return float(os.popen(s).read())


if __name__ == "__main__":
    idle_memory = []
    idle_cpu = []
    checking_time = 600
    interval = 10
    while checking_time:
        idle_cpu.append(get_cpu())
        idle_memory.append(get_mem())
        time.sleep(interval)
        checking_time -= interval

    avg_cpu = sum(idle_cpu) / len(idle_cpu)
    avg_mem = sum(idle_memory) / len(idle_memory)
    if avg_cpu > 80 and avg_mem > 50:
        os.system("python generate_triage_history.py")
        os.system("python generate_triaged_bug.py")
        os.system("python weight.py")
