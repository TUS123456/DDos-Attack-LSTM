import os
import pandas as pd

# Input CSV
file = r"C:\Users\tusar\Desktop\sunita-project\DDoSWatch\DDoSWatch\data\traffic_logs.csv"
df = pd.read_csv(file)

# Convert timestamp to minute bucket
df['timestamp'] = pd.to_datetime(df['timeStamp'], unit='ms')
df['minute'] = df['timestamp'].dt.floor('min')

# Count requests per minute
traffic = df.groupby('minute').size().reset_index(name='Traffic')

# Ensure output folder exists
output_folder = r"C:\Users\tusar\Desktop\sunita-project\DDoSWatch\DDoSWatch\data"
os.makedirs(output_folder, exist_ok=True)

# Save formatted traffic
traffic.to_csv(os.path.join(output_folder, "traffic-data.csv"), index=False)

print("Formatted traffic saved as traffic-data.csv")
