import pandas as pd

# Load the data files
references_df = pd.read_csv('/tmp/tmpgohlffn5_refs.csv')
citations_df = pd.read_csv('/tmp/tmpr9tzm0_r_cites.csv')

# Count the number of references (n_j)
n_j = len(references_df)

# Count the number of citing papers (n_i)
n_i = len(citations_df)

# Calculate the Disruption Index (D)
# D = (n_i - n_j) / (n_i + n_j)
D = (n_i - n_j) / (n_i + n_j)

# Print the results
print(f'D_INDEX = {D}')
print(f'n_i = {n_i}')
print(f'n_j = {n_j}')