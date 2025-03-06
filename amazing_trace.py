import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.ticker import MaxNLocator
import time
import os
from subprocess import run
import re

def execute_traceroute(destination):
    # Run the traceroute command and get the output
    result = run(["traceroute", "-I", destination], capture_output=True)
    # If there was an error, throw it
    if result.stderr:
        raise Exception(result.stderr.decode())
    # Otherwise, return the output
    else:
        return result.stdout.decode()

def parse_traceroute(traceroute_output: str):
    """
    Parses the raw traceroute output into a structured format.

    Args:
        traceroute_output (str): Raw output from the traceroute command

    Returns:
        list: A list of dictionaries, each containing information about a hop:
            - 'hop': The hop number (int)
            - 'ip': The IP address of the router (str or None if timeout)
            - 'hostname': The hostname of the router (str or None if same as ip)
            - 'rtt': List of round-trip times in ms (list of floats, None for timeouts)

    Example:
    ```
        [
            {
                'hop': 1,
                'ip': '172.21.160.1',
                'hostname': 'HELDMANBACK.mshome.net',
                'rtt': [0.334, 0.311, 0.302]
            },
            {
                'hop': 2,
                'ip': '10.103.29.254',
                'hostname': None,
                'rtt': [3.638, 3.630, 3.624]
            },
            {
                'hop': 3,
                'ip': None,  # For timeout/asterisk
                'hostname': None,
                'rtt': [None, None, None]
            }
        ]
    ```
    """
    # Your code here
    # Hint: Use regular expressions to extract the relevant information
    # Handle timeouts (asterisks) appropriately

    # Remove this line once you implement the function,
    # and don't forget to *return* the output
    dict_list = []
    lines = traceroute_output.strip().split("\n")
    # Iterate over each line in the output, except the first one (it doesn't have any data)
    for line in lines[1:]:
        hop_dict = {}
        # Perform a regex search to find each necessary element
        hop_dict["hop"] = re.search("^(?: *)([0-9]*)", line)
        hop_dict["ip"] = re.search("([0-9]{1,3}[.]){3}[0-9]{1,3}", line)
        hop_dict["hostname"] = re.search("([^ ]*)(?: [(])", line)
        # Convert all the found times to a number
        hop_dict["rtt"] = [float(i) for i in re.findall("([0-9]*[.][0-9]*)(?: ms)", line)]

        # Get the actual match from each part if it was found
        if hop_dict["hop"]:
            hop_dict["hop"] = int(hop_dict["hop"][1])
        if hop_dict["ip"]:
            hop_dict["ip"] = hop_dict["ip"][0]
        if hop_dict["hostname"]:
            hop_dict["hostname"] = hop_dict["hostname"][1]
            # Do a extra check for if the hostname is just the ip address
            if hop_dict["hostname"] == hop_dict["ip"]:
                hop_dict["hostname"] = None
        # Pad the times list with Nones
        while len(hop_dict["rtt"]) < 3:
            hop_dict["rtt"].append(None)
        dict_list.append(hop_dict)
    return dict_list


# ============================================================================ #
#                    DO NOT MODIFY THE CODE BELOW THIS LINE                    #
# ============================================================================ #
def visualize_traceroute(destination, num_traces=3, interval=5, output_dir='output'):
    """
    Runs multiple traceroutes to a destination and visualizes the results.

    Args:
        destination (str): The hostname or IP address to trace
        num_traces (int): Number of traces to run
        interval (int): Interval between traces in seconds
        output_dir (str): Directory to save the output plot

    Returns:
        tuple: (DataFrame with trace data, path to the saved plot)
    """
    all_hops = []

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    print(f"Running {num_traces} traceroutes to {destination}...")

    for i in range(num_traces):
        if i > 0:
            print(f"Waiting {interval} seconds before next trace...")
            time.sleep(interval)

        print(f"Trace {i+1}/{num_traces}...")
        output = execute_traceroute(destination)
        hops = parse_traceroute(output)

        # Add timestamp and trace number
        timestamp = time.strftime("%H:%M:%S")
        for hop in hops:
            hop['trace_num'] = i + 1
            hop['timestamp'] = timestamp
            all_hops.append(hop)

    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(all_hops)

    # Calculate average RTT for each hop (excluding timeouts)
    df['avg_rtt'] = df['rtt'].apply(lambda x: np.mean([r for r in x if r is not None]) if any(r is not None for r in x) else None)

    # Plot the results
    plt.figure(figsize=(12, 6))

    # Create a subplot for RTT by hop
    ax1 = plt.subplot(1, 1, 1)

    # Group by trace number and hop number
    for trace_num in range(1, num_traces + 1):
        trace_data = df[df['trace_num'] == trace_num]

        # Plot each trace with a different color
        ax1.plot(trace_data['hop'], trace_data['avg_rtt'], 'o-',
                label=f'Trace {trace_num} ({trace_data.iloc[0]["timestamp"]})')

    # Add labels and legend
    ax1.set_xlabel('Hop Number')
    ax1.set_ylabel('Average Round Trip Time (ms)')
    ax1.set_title(f'Traceroute Analysis for {destination}')
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend()

    # Make sure hop numbers are integers
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))

    plt.tight_layout()

    # Save the plot to a file instead of displaying it
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    safe_dest = destination.replace('.', '-')
    output_file = os.path.join(output_dir, f"trace_{safe_dest}_{timestamp}.png")
    plt.savefig(output_file)
    plt.close()

    print(f"Plot saved to: {output_file}")

    # Return the dataframe and the path to the saved plot
    return df, output_file

# Test the functions
if __name__ == "__main__":
    # Test destinations
    destinations = [
        "google.com",
        "amazon.com",
        "bbc.co.uk"  # International site
    ]

    for dest in destinations:
        df, plot_path = visualize_traceroute(dest, num_traces=3, interval=5)
        print(f"\nAverage RTT by hop for {dest}:")
        avg_by_hop = df.groupby('hop')['avg_rtt'].mean()
        print(avg_by_hop)
        print("\n" + "-"*50 + "\n")
