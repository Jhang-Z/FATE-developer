import numpy as np
import pandas as pd

def generate_unique_data(n) -> pd.DataFrame:
    """
    generate two-dimension table with unique 'id' column

    example
    -------

    id, x
    12, 9.1
    7,  8.0
    2,  4.4
    ...
    
    """

    ids = ids = np.random.randint(low=0, high=np.iinfo(np.uint64).max, size=n, dtype=np.uint64)
    x_values = np.random.uniform(low=0.0, high=1000.0, size=n)
    
    df = pd.DataFrame({'id': ids, 'x': x_values})
    
    return df

def ensure_unique_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    ensure each 'id' is unique
    """

    # remove duplicate 'id' row
    df_unique = df.drop_duplicates(subset='id')
    
    missing_rows = len(df) - len(df_unique)
    if missing_rows > 0:
        df_additional = generate_unique_data(missing_rows)
        df_unique = pd.concat([df_unique, df_additional], ignore_index=True)
        # recursion detection
        return ensure_unique_df(df_unique)
    
    return df_unique

def shuffle_dataframe(df):
    """
    shuffle table in rows
    """
    df_shuffled = df.sample(frac=1).reset_index(drop=True)
    return df_shuffled

def save_table(df: pd.DataFrame, filename: str):
    """
    save table to a csv file
    """
    df.to_csv(filename, index=False)

COMMON = 1 << 16
TOTAL = 1 << 20

comm = generate_unique_data(COMMON)
comm = ensure_unique_df(comm)

data_host = generate_unique_data(TOTAL - COMMON)
data_host = pd.concat([comm, data_host], ignore_index=True)
data_host = shuffle_dataframe(ensure_unique_df(data_host))
save_table(data_host, "intersect_host.csv")

data_guest = generate_unique_data(TOTAL - COMMON)
data_guest = pd.concat([comm, data_guest], ignore_index=True)
data_guest = shuffle_dataframe(ensure_unique_df(data_guest))
save_table(data_guest, "intersect_guest.csv")