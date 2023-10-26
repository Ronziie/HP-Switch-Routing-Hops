import netmiko
import ipaddress
import os
import subprocess

#define method to get the switch ip address store in variable switch and pass outside method 
def get_lldp_info(initial_ip):
    """
        Get LLDP information from switch
        Store in a lldp_info variable to be passed onto this method so this method can be invoked inside other methods
        Return a dictionary of a bunch of remote devices connected to the switch
    """

    output = initial_ip.send_command("show lldp info remote-device detail")
    lldp_info = []
    sysname = None
    ip_address = None
    for line in output.splitlines():
        if line.strip().startswith("SysName"):
            sysname = line[13:].strip()
        elif line.strip().startswith("Address"):
            parts = line.split(":")
            if len(parts) > 1:
                ip_address = parts[1].strip()
                if ipaddress.ip_address(ip_address).is_private and ip_address != initial_ip:
                    lldp_info.append({
                        "sysname": sysname,
                        "ip_address": ip_address
                    })
                    sysname = None
                    ip_address = None

    return lldp_info


#define method ping and pass the result from previous method into
def ping_device(ip_address):
    """
    Ping the IP address and check if it's alive or dead
    """
    response = subprocess.call(["ping", "-n", "1",  "-w", "1000", ip_address], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if response == 0:
        return True  # Response is the round-trip time in milliseconds
    else:
        return False  # Indicates that the device did not respond to the ping
        
def find_path_to_core(initial_ip):
    """
        Finding the Path to the core WPSWCORE
    """
    path = []
    current_switch = netmiko.ConnectHandler(host=initial_ip, username="admin", password="admin", device_type="hp_procurve")

    while True:
        lldp_info = get_lldp_info(current_switch)
        
        found = False

        for device in lldp_info:
            if device["ip_address"].startswith("10.200.70") and device["ip_address"] != initial_ip and device["ip_address"] not in path:
                if ping_device(device["ip_address"]):
                    path.append(device["ip_address"])
                    current_switch = netmiko.ConnectHandler(host=device["ip_address"], device_type="hp_procurve", username="admin", password="admin")
                    found = True
            
            if device["sysname"] == "WPSWCORE":
                return path

        if not current_switch.is_alive() or not found:
            break

    return path
    
if __name__ == "__main__":
    initial_ip = input("Enter the starting IP address to find the path for: ")

    path = find_path_to_core(initial_ip)

    if path:
        print("Path to core:")
        print(initial_ip)  # Print the host switch's IP address
        for hop in path:
            print(hop)
        print("WPSWCORE")
    else:
        print(f"{initial_ip} route to core ends here")

