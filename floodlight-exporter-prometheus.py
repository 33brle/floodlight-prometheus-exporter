from prometheus_client import start_http_server, Gauge
import requests
import time

# Prometheus metrics for packet counts sent and received by each switch port
PACKETS_SENT = Gauge('floodlight_packets_sent_total', 'Total packets sent by each switch port', ['switch_id', 'port'])
PACKETS_RECEIVED = Gauge('floodlight_packets_received_total', 'Total packets received by each switch port', ['switch_id', 'port'])

def fetch_switches():
    """Fetch the list of switches (DPID) from Floodlight."""
    try:
        response = requests.get('http://192.168.253.128:8080/wm/core/controller/switches/json')
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching switch data: {e}")
        return []

def fetch_port_stats_for_switch(switch_id):
    """Get port stats (packets sent/received) for a given switch."""
    try:
        response = requests.get(f'http://192.168.253.128:8080/wm/core/switch/{switch_id}/port/json')
        response.raise_for_status()
        port_stats = response.json()

        # Check if port stats are in the expected format
        if 'port_reply' in port_stats:
            for port in port_stats['port_reply'][0]['port']:
                port_number = port.get('port_number', 'unknown')
                
                # Extract sent/received packet counts with a fallback to zero
                packets_sent = int(port.get('transmit_packets', 0))
                packets_received = int(port.get('receive_packets', 0))

                # Update Prometheus metrics for this port
                PACKETS_SENT.labels(switch_id=switch_id, port=port_number).set(packets_sent)
                PACKETS_RECEIVED.labels(switch_id=switch_id, port=port_number).set(packets_received)
        else:
            print(f"No port_reply data found for switch {switch_id}")

    except requests.RequestException as e:
        print(f"Error fetching stats for switch {switch_id}: {e}")
    except ValueError as e:
        print(f"Data processing error for switch {switch_id}: {e}")

if __name__ == "__main__":
    # Start Prometheus server on port 8000
    start_http_server(8000)
    print("Prometheus exporter running on port 8000...")

    # Continuously fetch and update metrics
    while True:
        switches = fetch_switches()
        
        # Get stats for each switch
        for switch in switches:
            switch_id = switch.get('switchDPID')  # Extract switch ID
            if switch_id:
                fetch_port_stats_for_switch(switch_id)

        time.sleep(10)  # Refresh every 10 seconds
