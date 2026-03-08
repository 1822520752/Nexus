"""
系统信息动作
提供系统信息、磁盘使用、内存信息、进程列表和网络信息查询
"""
import os
import platform
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.logger import logger
from app.services.action.action_registry import (
    ActionCategory,
    ActionMetadata,
    ActionParameter,
    ActionResult,
    action_registry,
)


def _run_command(command: str, timeout: int = 10) -> str:
    """
    执行命令并返回输出
    
    Args:
        command: 要执行的命令
        timeout: 超时时间
    
    Returns:
        命令输出
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="gbk",
            errors="ignore",
        )
        return result.stdout.strip()
    except Exception as e:
        logger.warning(f"执行命令失败: {command}, 错误: {e}")
        return ""


def _parse_size(size_str: str) -> int:
    """
    解析大小字符串为字节数
    
    Args:
        size_str: 大小字符串 (如 "10 GB")
    
    Returns:
        字节数
    """
    size_str = size_str.strip().upper()
    
    units = {
        "B": 1,
        "KB": 1024,
        "MB": 1024 ** 2,
        "GB": 1024 ** 3,
        "TB": 1024 ** 4,
        "PB": 1024 ** 5,
    }
    
    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            try:
                value = float(size_str[:-len(unit)].strip())
                return int(value * multiplier)
            except ValueError:
                pass
    
    try:
        return int(float(size_str))
    except ValueError:
        return 0


def get_system_info() -> ActionResult:
    """
    获取系统信息
    
    获取操作系统的详细信息
    
    Returns:
        执行结果
    """
    logger.info("获取系统信息")
    
    try:
        info = {
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "node": platform.node(),
            },
            "python": {
                "version": platform.python_version(),
                "implementation": platform.python_implementation(),
                "compiler": platform.python_compiler(),
            },
            "environment": {
                "user": os.environ.get("USERNAME", "Unknown"),
                "computer_name": os.environ.get("COMPUTERNAME", "Unknown"),
                "user_domain": os.environ.get("USERDOMAIN", "Unknown"),
                "os": os.environ.get("OS", "Unknown"),
                "number_of_processors": os.environ.get("NUMBER_OF_PROCESSORS", "Unknown"),
            },
        }
        
        # Windows 特定信息
        if platform.system() == "Windows":
            try:
                # 获取 Windows 版本信息
                win_ver = _run_command("ver")
                info["windows"] = {
                    "version": win_ver,
                }
                
                # 获取系统启动时间
                boot_time = _run_command("wmic os get lastbootuptime /value")
                if "LastBootUpTime" in boot_time:
                    info["windows"]["last_boot"] = boot_time.split("=")[1].strip()
                
            except Exception as e:
                logger.warning(f"获取 Windows 特定信息失败: {e}")
        
        return ActionResult(
            success=True,
            data=info,
            message="获取系统信息成功",
        )
        
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return ActionResult(
            success=False,
            error=str(e),
        )


def get_disk_usage(drive: Optional[str] = None) -> ActionResult:
    """
    获取磁盘使用情况
    
    获取指定驱动器或所有驱动器的使用情况
    
    Args:
        drive: 驱动器字母 (如 "C")，None 获取所有驱动器
    
    Returns:
        执行结果
    """
    logger.info(f"获取磁盘使用情况: {drive or '所有驱动器'}")
    
    try:
        disks = []
        
        if platform.system() == "Windows":
            # Windows 下使用 wmic 获取磁盘信息
            if drive:
                drives = [drive.upper()]
            else:
                # 获取所有驱动器
                drives_output = _run_command("wmic logicaldisk get deviceid /value")
                drives = []
                for line in drives_output.split("\n"):
                    if line.startswith("DeviceID="):
                        drives.append(line.split("=")[1].strip().replace(":", ""))
            
            for d in drives:
                try:
                    # 获取磁盘信息
                    disk_info = _run_command(f'wmic logicaldisk where "DeviceID=\'{d}:\'" get Size,FreeSpace,VolumeName,FileSystem /value')
                    
                    info = {"drive": f"{d}:"}
                    
                    for line in disk_info.split("\n"):
                        line = line.strip()
                        if line.startswith("Size="):
                            size = int(line.split("=")[1].strip() or 0)
                            info["total"] = size
                            info["total_formatted"] = _format_bytes(size)
                        elif line.startswith("FreeSpace="):
                            free = int(line.split("=")[1].strip() or 0)
                            info["free"] = free
                            info["free_formatted"] = _format_bytes(free)
                        elif line.startswith("VolumeName="):
                            info["label"] = line.split("=")[1].strip()
                        elif line.startswith("FileSystem="):
                            info["filesystem"] = line.split("=")[1].strip()
                    
                    # 计算使用情况
                    if "total" in info and "free" in info:
                        info["used"] = info["total"] - info["free"]
                        info["used_formatted"] = _format_bytes(info["used"])
                        info["usage_percent"] = round(info["used"] / info["total"] * 100, 2) if info["total"] > 0 else 0
                    
                    disks.append(info)
                    
                except Exception as e:
                    logger.warning(f"获取驱动器 {d} 信息失败: {e}")
                    continue
        else:
            # 非 Windows 系统
            import shutil
            
            if drive:
                paths = [f"/mnt/{drive}", f"/media/{drive}"]
            else:
                paths = ["/"]
            
            for path in paths:
                try:
                    usage = shutil.disk_usage(path)
                    disks.append({
                        "path": path,
                        "total": usage.total,
                        "total_formatted": _format_bytes(usage.total),
                        "used": usage.used,
                        "used_formatted": _format_bytes(usage.used),
                        "free": usage.free,
                        "free_formatted": _format_bytes(usage.free),
                        "usage_percent": round(usage.used / usage.total * 100, 2),
                    })
                except Exception as e:
                    logger.warning(f"获取路径 {path} 信息失败: {e}")
        
        return ActionResult(
            success=True,
            data={
                "disks": disks,
                "count": len(disks),
            },
            message=f"获取到 {len(disks)} 个驱动器的信息",
        )
        
    except Exception as e:
        logger.error(f"获取磁盘使用情况失败: {e}")
        return ActionResult(
            success=False,
            error=str(e),
        )


def _format_bytes(size: int) -> str:
    """
    格式化字节数为可读字符串
    
    Args:
        size: 字节数
    
    Returns:
        格式化后的字符串
    """
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} EB"


def get_memory_info() -> ActionResult:
    """
    获取内存信息
    
    获取系统内存使用情况
    
    Returns:
        执行结果
    """
    logger.info("获取内存信息")
    
    try:
        memory = {}
        
        if platform.system() == "Windows":
            # Windows 下使用 wmic 获取内存信息
            mem_info = _run_command("wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value")
            
            for line in mem_info.split("\n"):
                line = line.strip()
                if line.startswith("TotalVisibleMemorySize="):
                    total_kb = int(line.split("=")[1].strip() or 0)
                    memory["total"] = total_kb * 1024  # 转换为字节
                    memory["total_formatted"] = _format_bytes(memory["total"])
                elif line.startswith("FreePhysicalMemory="):
                    free_kb = int(line.split("=")[1].strip() or 0)
                    memory["free"] = free_kb * 1024
                    memory["free_formatted"] = _format_bytes(memory["free"])
            
            # 计算使用情况
            if "total" in memory and "free" in memory:
                memory["used"] = memory["total"] - memory["free"]
                memory["used_formatted"] = _format_bytes(memory["used"])
                memory["usage_percent"] = round(memory["used"] / memory["total"] * 100, 2) if memory["total"] > 0 else 0
            
            # 获取页面文件信息
            page_info = _run_command("wmic pagefile get AllocatedBaseSize,CurrentUsage /value")
            for line in page_info.split("\n"):
                line = line.strip()
                if line.startswith("AllocatedBaseSize="):
                    memory["pagefile_total"] = int(line.split("=")[1].strip() or 0) * 1024 * 1024
                elif line.startswith("CurrentUsage="):
                    memory["pagefile_used"] = int(line.split("=")[1].strip() or 0) * 1024 * 1024
        
        else:
            # Linux/macOS
            try:
                with open("/proc/meminfo", "r") as f:
                    meminfo = {}
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 2:
                            key = parts[0].rstrip(":")
                            value = int(parts[1])
                            meminfo[key] = value * 1024  # 转换为字节
                    
                    memory["total"] = meminfo.get("MemTotal", 0)
                    memory["free"] = meminfo.get("MemFree", 0)
                    memory["available"] = meminfo.get("MemAvailable", memory["free"])
                    memory["used"] = memory["total"] - memory["available"]
                    
                    for key in ["total", "free", "available", "used"]:
                        if key in memory:
                            memory[f"{key}_formatted"] = _format_bytes(memory[key])
                    
                    memory["usage_percent"] = round(memory["used"] / memory["total"] * 100, 2) if memory["total"] > 0 else 0
                    
            except FileNotFoundError:
                pass
        
        return ActionResult(
            success=True,
            data=memory,
            message="获取内存信息成功",
        )
        
    except Exception as e:
        logger.error(f"获取内存信息失败: {e}")
        return ActionResult(
            success=False,
            error=str(e),
        )


def get_running_processes(
    filter_name: Optional[str] = None,
    sort_by: str = "memory",
    limit: int = 20,
) -> ActionResult:
    """
    获取运行进程
    
    获取系统正在运行的进程列表
    
    Args:
        filter_name: 按进程名过滤
        sort_by: 排序字段 (cpu, memory, name, pid)
        limit: 返回数量限制
    
    Returns:
        执行结果
    """
    logger.info("获取运行进程列表")
    
    try:
        processes = []
        
        if platform.system() == "Windows":
            # Windows 下使用 wmic 获取进程信息
            proc_info = _run_command(
                'wmic process get ProcessId,Name,WorkingSetSize,PageFileUsage /format:csv',
                timeout=30
            )
            
            lines = proc_info.strip().split("\n")
            
            for line in lines[1:]:  # 跳过标题行
                parts = line.strip().split(",")
                if len(parts) >= 5:
                    try:
                        pid = int(parts[1]) if parts[1] else 0
                        name = parts[2]
                        working_set = int(parts[3]) if parts[3] else 0
                        page_file = int(parts[4]) if parts[4] else 0
                        
                        # 过滤
                        if filter_name and filter_name.lower() not in name.lower():
                            continue
                        
                        processes.append({
                            "pid": pid,
                            "name": name,
                            "memory_bytes": working_set,
                            "memory_mb": round(working_set / (1024 * 1024), 2),
                            "page_file_bytes": page_file,
                        })
                    except (ValueError, IndexError):
                        continue
        else:
            # Linux/macOS 使用 ps 命令
            proc_info = _run_command("ps aux --sort=-%mem", timeout=30)
            
            for line in proc_info.split("\n")[1:]:  # 跳过标题行
                parts = line.split()
                if len(parts) >= 11:
                    try:
                        name = parts[10]
                        
                        if filter_name and filter_name.lower() not in name.lower():
                            continue
                        
                        processes.append({
                            "pid": int(parts[1]),
                            "name": name,
                            "cpu_percent": float(parts[2]),
                            "memory_percent": float(parts[3]),
                        })
                    except (ValueError, IndexError):
                        continue
        
        # 排序
        if sort_by == "memory":
            processes.sort(key=lambda x: x.get("memory_bytes", x.get("memory_percent", 0)), reverse=True)
        elif sort_by == "cpu":
            processes.sort(key=lambda x: x.get("cpu_percent", 0), reverse=True)
        elif sort_by == "name":
            processes.sort(key=lambda x: x.get("name", "").lower())
        elif sort_by == "pid":
            processes.sort(key=lambda x: x.get("pid", 0))
        
        # 限制数量
        processes = processes[:limit]
        
        return ActionResult(
            success=True,
            data={
                "processes": processes,
                "count": len(processes),
                "filter": filter_name,
                "sort_by": sort_by,
            },
            message=f"获取到 {len(processes)} 个进程",
        )
        
    except Exception as e:
        logger.error(f"获取进程列表失败: {e}")
        return ActionResult(
            success=False,
            error=str(e),
        )


def get_network_info() -> ActionResult:
    """
    获取网络信息
    
    获取网络适配器和连接信息
    
    Returns:
        执行结果
    """
    logger.info("获取网络信息")
    
    try:
        network = {
            "adapters": [],
            "connections": [],
        }
        
        if platform.system() == "Windows":
            # 获取网络适配器信息
            adapter_info = _run_command("ipconfig /all")
            
            current_adapter = None
            for line in adapter_info.split("\n"):
                line = line.strip()
                
                # 检测新适配器
                if line and not line.startswith(" ") and ":" in line and not line.startswith("Windows"):
                    if current_adapter:
                        network["adapters"].append(current_adapter)
                    current_adapter = {"name": line.rstrip(":")}
                
                # 解析适配器信息
                elif current_adapter:
                    if line.startswith("Description"):
                        current_adapter["description"] = line.split(":", 1)[1].strip()
                    elif line.startswith("Physical Address"):
                        current_adapter["mac"] = line.split(":", 1)[1].strip()
                    elif line.startswith("IPv4 Address"):
                        current_adapter["ipv4"] = line.split(":", 1)[1].strip()
                    elif line.startswith("Subnet Mask"):
                        current_adapter["subnet_mask"] = line.split(":", 1)[1].strip()
                    elif line.startswith("Default Gateway"):
                        current_adapter["gateway"] = line.split(":", 1)[1].strip()
                    elif line.startswith("DNS Servers"):
                        current_adapter["dns"] = line.split(":", 1)[1].strip()
            
            if current_adapter:
                network["adapters"].append(current_adapter)
            
            # 获取网络连接
            netstat_info = _run_command("netstat -an")
            
            for line in netstat_info.split("\n"):
                line = line.strip()
                if line.startswith("TCP") or line.startswith("UDP"):
                    parts = line.split()
                    if len(parts) >= 2:
                        proto = parts[0]
                        local = parts[1]
                        remote = parts[2] if len(parts) > 2 else ""
                        state = parts[3] if len(parts) > 3 else ""
                        
                        network["connections"].append({
                            "protocol": proto,
                            "local_address": local,
                            "remote_address": remote,
                            "state": state,
                        })
        
        else:
            # Linux/macOS
            # 获取网络接口
            ifconfig_info = _run_command("ifconfig")
            # 简单解析...
            
            # 获取网络连接
            netstat_info = _run_command("netstat -an")
            for line in netstat_info.split("\n"):
                line = line.strip()
                parts = line.split()
                if len(parts) >= 4:
                    network["connections"].append({
                        "protocol": parts[0],
                        "local_address": parts[3],
                        "remote_address": parts[4] if len(parts) > 4 else "",
                        "state": parts[5] if len(parts) > 5 else "",
                    })
        
        return ActionResult(
            success=True,
            data={
                "adapters": network["adapters"],
                "connections": network["connections"][:50],  # 限制连接数量
                "adapter_count": len(network["adapters"]),
                "connection_count": len(network["connections"]),
            },
            message=f"获取到 {len(network['adapters'])} 个网络适配器",
        )
        
    except Exception as e:
        logger.error(f"获取网络信息失败: {e}")
        return ActionResult(
            success=False,
            error=str(e),
        )


def get_cpu_info() -> ActionResult:
    """
    获取 CPU 信息
    
    获取 CPU 详细信息和使用率
    
    Returns:
        执行结果
    """
    logger.info("获取 CPU 信息")
    
    try:
        cpu = {
            "processor": platform.processor(),
            "machine": platform.machine(),
            "cores": {
                "physical": os.cpu_count(),
                "logical": os.cpu_count(),
            },
        }
        
        if platform.system() == "Windows":
            # 获取 CPU 详细信息
            cpu_info = _run_command("wmic cpu get Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed /value")
            
            for line in cpu_info.split("\n"):
                line = line.strip()
                if line.startswith("Name="):
                    cpu["name"] = line.split("=")[1].strip()
                elif line.startswith("NumberOfCores="):
                    cpu["cores"]["physical"] = int(line.split("=")[1].strip() or 0)
                elif line.startswith("NumberOfLogicalProcessors="):
                    cpu["cores"]["logical"] = int(line.split("=")[1].strip() or 0)
                elif line.startswith("MaxClockSpeed="):
                    mhz = int(line.split("=")[1].strip() or 0)
                    cpu["max_clock_mhz"] = mhz
                    cpu["max_clock_ghz"] = round(mhz / 1000, 2)
            
            # 获取 CPU 使用率
            load_info = _run_command("wmic cpu get LoadPercentage /value")
            for line in load_info.split("\n"):
                line = line.strip()
                if line.startswith("LoadPercentage="):
                    cpu["load_percent"] = int(line.split("=")[1].strip() or 0)
        
        else:
            # Linux/macOS
            try:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "model name" in line:
                            cpu["name"] = line.split(":")[1].strip()
                        elif "cpu cores" in line:
                            cpu["cores"]["physical"] = int(line.split(":")[1].strip())
                
                # 获取负载
                with open("/proc/loadavg", "r") as f:
                    load = f.read().split()
                    cpu["load_avg"] = {
                        "1min": float(load[0]),
                        "5min": float(load[1]),
                        "15min": float(load[2]),
                    }
            except FileNotFoundError:
                pass
        
        return ActionResult(
            success=True,
            data=cpu,
            message="获取 CPU 信息成功",
        )
        
    except Exception as e:
        logger.error(f"获取 CPU 信息失败: {e}")
        return ActionResult(
            success=False,
            error=str(e),
        )


# 注册动作到注册表
def _register_actions():
    """
    注册所有系统信息动作
    """
    # 获取系统信息
    action_registry.register(
        name="system.info",
        display_name="获取系统信息",
        description="获取操作系统的详细信息",
        category=ActionCategory.SYSTEM,
        executor=get_system_info,
        parameters=[],
        returns="系统信息字典",
        examples=[{}],
        tags=["system", "info", "os"],
    )
    
    # 获取磁盘使用情况
    action_registry.register(
        name="system.disk_usage",
        display_name="获取磁盘使用情况",
        description="获取指定驱动器或所有驱动器的使用情况",
        category=ActionCategory.SYSTEM,
        executor=get_disk_usage,
        parameters=[
            ActionParameter(
                name="drive",
                type="str",
                description="驱动器字母 (如 'C')，None 获取所有驱动器",
                required=False,
            ),
        ],
        returns="磁盘使用情况列表",
        examples=[
            {"drive": "C"},
            {},
        ],
        tags=["system", "disk", "storage"],
    )
    
    # 获取内存信息
    action_registry.register(
        name="system.memory_info",
        display_name="获取内存信息",
        description="获取系统内存使用情况",
        category=ActionCategory.SYSTEM,
        executor=get_memory_info,
        parameters=[],
        returns="内存信息字典",
        examples=[{}],
        tags=["system", "memory", "ram"],
    )
    
    # 获取运行进程
    action_registry.register(
        name="system.processes",
        display_name="获取运行进程",
        description="获取系统正在运行的进程列表",
        category=ActionCategory.SYSTEM,
        executor=get_running_processes,
        parameters=[
            ActionParameter(
                name="filter_name",
                type="str",
                description="按进程名过滤",
                required=False,
            ),
            ActionParameter(
                name="sort_by",
                type="str",
                description="排序字段 (cpu, memory, name, pid)",
                required=False,
                default="memory",
                choices=["cpu", "memory", "name", "pid"],
            ),
            ActionParameter(
                name="limit",
                type="int",
                description="返回数量限制",
                required=False,
                default=20,
                min_value=1,
                max_value=100,
            ),
        ],
        returns="进程列表",
        examples=[
            {"sort_by": "memory", "limit": 10},
            {"filter_name": "python"},
        ],
        tags=["system", "process", "task"],
    )
    
    # 获取网络信息
    action_registry.register(
        name="system.network_info",
        display_name="获取网络信息",
        description="获取网络适配器和连接信息",
        category=ActionCategory.SYSTEM,
        executor=get_network_info,
        parameters=[],
        returns="网络信息字典",
        examples=[{}],
        tags=["system", "network", "adapter"],
    )
    
    # 获取 CPU 信息
    action_registry.register(
        name="system.cpu_info",
        display_name="获取 CPU 信息",
        description="获取 CPU 详细信息和使用率",
        category=ActionCategory.SYSTEM,
        executor=get_cpu_info,
        parameters=[],
        returns="CPU 信息字典",
        examples=[{}],
        tags=["system", "cpu", "processor"],
    )


# 模块加载时自动注册
_register_actions()
