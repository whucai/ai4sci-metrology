import pandas as pd

# Load the data files
references_df = pd.read_csv('/tmp/tmp1rqqoomz_refs.csv')
cites_df = pd.read_csv('/tmp/tmp61ws1oac_cites.csv')

# Count the number of references (n_i) and citing papers (n_j)
n_i = len(references_df)
n_j = len(cites_df)

# Calculate the Disruption Index (D)
D = n_i / (n_i + n_j) if (n_i + n_j) > 0 else 0.0

# Print the results
print(f'D_INDEX = {D}')
print(f'n_i = {n_i}')
print(f'n_j = {n_j}')