# Importing required modules
import psycopg2
import pandas as pd


# Establishing connection with DSDRCV Database
conn = psycopg2.connect(
   database="DSDRCV", user='postgres', password='R43E!T-Ghvc98', host='localhost', port= '5432')
# Creating a cursor object using the cursor() method
cursor = conn.cursor()
# Executing MYSQL function using the execute() method
cursor.execute("select version()")
# Fetch a single row using fetchone() method.
data = cursor.fetchone()
print("Connection established to: ", data)


# Define SQL queries for each table
sql_table1 = "SELECT * FROM store"
sql_table2 = "SELECT * FROM supplier"
sql_table3 = "SELECT * FROM invoice_header"
sql_table4 = "SELECT * FROM invoice_line"
# Read data from each table into separate dataframes
store = pd.read_sql_query(sql_table1, conn)
sup = pd.read_sql_query(sql_table2, conn)
inv_hd = pd.read_sql_query(sql_table3, conn)
inv_line = pd.read_sql_query(sql_table4, conn)
# Print the head of each DataFrame
print("Store:")
print(store.head())

print("Sup:")
print(sup.head())

print("Invoice_Header:")
print(inv_hd.head())

print("Invoice_Line:")
print(inv_line.head())
# Close the database connection
conn.close()


# Create a dictionary to store the DataFrames
dataframes = {'inv_hd': inv_hd, 'inv_line': inv_line}
# Drop columns from each DataFrame in the dictionary
for df_name, df in dataframes.items():
    modified_df = df.where(pd.notna(df), None)
    modified_df = modified_df.dropna(axis=1, how='all')
    dataframes[df_name] = modified_df
# Access the modified DataFrames by their original names
inv_hd = dataframes['inv_hd']
inv_line = dataframes['inv_line']
# Print the modified DataFrames
print("Modified inv_hd:")
print(inv_hd)

print("Modified inv_line:")
print(inv_line)


#Dropping DSD and Facility columns as they won't be needed for any reporting down the road
sup = sup.drop(['dsd', 'facility'], axis=1)
print(sup)
#Dropping unnecessary columns from the inv_line dataframe
inv_hd = inv_hd.drop(['dsd','final_total_ext_deposit', 'base_misc_charge', 'base_misc_allowance', 'base_total_deposit', 'shipment_id', 'upload_timestamp'], axis=1)
print(inv_hd)
#Dropping duplicate/unnecessary columns from the inv_line dataframe
inv_line = inv_line.drop(['upc_number','inventory_units', 'deposit', 'deposit_mult', 'item_type', 'edi_flags'], axis=1)
print(inv_line)


#Creation of a list of the old inv_line column names and the new inv_line column names.
line_col_names = {
    'line_number': 'num_line_items',
     'base_qty': 'base_total_qty',
     'final_qty': 'final_total_qty',
     'base_cost': 'base_total_net',
     'final_cost': 'final_total_net',
     'final_allowance': 'final_misc_allowance',
     'billing_price': 'final_total_retail',
     'billing_major_dept': 'major_dept_number'
}

#Applying the new inv_line column names
inv_line = inv_line.rename(columns=line_col_names)

#Printing column names from both inv_hd and inv_line to make sure name changes took place and match
print("inv_hd columns:", inv_hd.columns.tolist())
print("inv_line columns:", inv_line.columns.tolist())

# Group the inv_line by 'invoice_id' and calculate the maximum 'billing_dept_number'
max_dept_number = inv_line.groupby(['store_id','invoice_id'])['billing_dept_number'].transform('max')

# Assign the maximum 'billing_dept_number' to the 'major_dept_number' column
inv_line['major_dept_number'] = max_dept_number

# Creating a filtered_df for store 340007 and invoice_id 257 to determine accuracy
filtered_df = inv_line[(inv_line['store_id'] == 340007) & (inv_line['invoice_id'] == 257)]

# Selecting the columns necessary from filtered_df for verification
columns_to_print = ['store_id', 'invoice_id', 'billing_dept_number', 'major_dept_number']

# Print the above columns of filtered_df for review
print(filtered_df[columns_to_print])

#Further verification of this working by getting the count of each dept_number for filtered_df
count_19 = (filtered_df['billing_dept_number'] == 19).sum()
count_57 = (filtered_df['billing_dept_number'] == 57).sum()
print(count_19, count_57)

#Printing inv_hd columns data types to compare against inv_line
inv_hd_types = inv_hd.dtypes
print(inv_hd_types)

#Printing inv_line columns data types to compare against inv_hd
inv_line_types = inv_line.dtypes
print(inv_line_types)

#Updating inv_line flags column to int64
inv_line['flags'] = inv_line['flags'].astype('int64')

#Reprint of the inv_line column data types to make sure change above took place
inv_line_types = inv_line.dtypes
print(inv_line_types)

# Get the common columns between inv_hd and inv_line
common_columns = list(set(inv_hd.columns).intersection(inv_line.columns))

# Create a inv_sum with all columns from inv_hd
inv_sum = inv_hd.copy()

# Select only the common columns from inv_line
inv_line_common_columns = inv_line[common_columns]

# Concantenate the rows from inv_line to inv_sum
inv_sum = pd.concat([inv_sum, inv_line_common_columns], ignore_index=True)

# Sort the inv_sum by 'store_id' and 'invoice_id'
inv_sum = inv_sum.sort_values(by=['store_id', 'invoice_id'])

# Print inv_sum to csv
inv_sum.to_csv('invoice_summary.csv')