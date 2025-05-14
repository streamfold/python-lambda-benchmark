import pandas as pd
import matplotlib.pyplot as plt
from brokenaxes import brokenaxes

# Read the CSV file into a DataFrame
file_path = "../tmp/coldstart-test5-fromsheets.csv"
df = pd.read_csv(file_path)

# Define the function to compute trimmed average for each group.
def compute_trimmed_avg(group):
    durations = group['client_duration_ms'].sort_values().values
    if len(durations) == 5:
        trimmed = durations[1:-1]  # remove lowest and highest
        return trimmed.mean()
    else:
        return float('nan')

# Group by base_name and memory and calculate the trimmed average
result = df.groupby(['base_name', 'memory']).apply(compute_trimmed_avg).reset_index()
result.columns = ['base_name', 'memory', 'trimmed_avg_client_duration_ms']

# Create a mapping for each memory of the baseline trimmed average (base_name = benchmark-coldstart)
baseline_mapping = result[result['base_name'] == 'benchmark-coldstart'].set_index('memory')['trimmed_avg_client_duration_ms'].to_dict()

# Calculate the difference from the baseline for each row, for matching memory
result['difference'] = result.apply(lambda row: row['trimmed_avg_client_duration_ms'] - baseline_mapping.get(row['memory'], float('nan')), axis=1)

# Filter the data only for benchmark-coldstart-otel and benchmark-coldstart-rotel
filtered = result[result['base_name'].isin(['benchmark-coldstart-otel', 'benchmark-coldstart-rotel', 'benchmark-coldstart-datadog'])]

# Sort filtered results by memory for clarity
filtered = filtered.sort_values('memory')

# Separate the data for each base_name
otel_data = filtered[filtered['base_name'] == 'benchmark-coldstart-otel']
rotel_data = filtered[filtered['base_name'] == 'benchmark-coldstart-rotel']
datadog_data = filtered[filtered['base_name'] == 'benchmark-coldstart-datadog']

x = [128, 256, 512, 1024, 2048, 3072, 4096]
labels = ['128 MB', '256 MB', '512 MB', '1 GB', '2 GB', '3 GB', '4 GB']

# Generate the line chart
fig = plt.figure(figsize=(8, 5))

bax = brokenaxes(ylims=((0, 1750), (4400, 4800)), hspace=0.2)

bax.plot(otel_data['memory'], otel_data['difference'], marker='o', label='OpenTelemetry Lambda')
bax.plot(rotel_data['memory'], rotel_data['difference'], marker='o', label='Rotel Lambda')
bax.plot(datadog_data['memory'], datadog_data['difference'], marker='o', label='Datadog Lambda')
plt.xlabel('Memory (MB)')
plt.yscale('log')
plt.ylabel('Coldstart Time (ms)')
plt.title('Coldstart Comparison')
plt.xticks(x, labels, rotation='vertical')
bax.legend()
bax.grid(True)
plt.show()
