import streamlit as st
import pandas as pd
import io
import zipfile

# Function to combine multiple CSV files
def combine_csv_files(uploaded_files):
    dfs = []
    for file in uploaded_files:
        df = pd.read_csv(file)
        dfs.append(df)
    combined_df = pd.concat(dfs, ignore_index=True)
    return combined_df

# Your existing processing functions
def extract_state_abbrev(address_str):
    state_abbrevs = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 
                     'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 
                     'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 
                     'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 
                     'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
    words = str(address_str).upper().split()
    for word in words:
        if word in state_abbrevs:
            return word
    return ''

def split_party_info(data):
    if pd.isna(data) or data == '':
        return pd.Series(['', '', '', '', ''])
    parts = str(data).split('|')
    name = parts[0].strip() if len(parts) > 0 else ''
    address = parts[1].strip() if len(parts) > 1 else ''
    state = extract_state_abbrev(address) if len(parts) > 1 else ''
    phone = parts[2].strip() if len(parts) > 2 else ''
    email = parts[3].strip() if len(parts) > 3 else ''
    return pd.Series([name, address, state, phone, email])

def process_csv(df):
    supplier_cols = ['Supplier_Name', 'Supplier_Address', 'Supplier_State', 'Supplier_Phone', 'Supplier_Email']
    df[supplier_cols] = df['SUPPLIER'].apply(split_party_info)
    
    buyer_cols = ['Buyer_Name', 'Buyer_Address', 'Buyer_State', 'Buyer_Phone', 'Buyer_Email']
    df[buyer_cols] = df['BUYER'].apply(split_party_info)
    
    notify_cols = ['Notify_Party_Name', 'Notify_Party_Address', 'Notify_Party_State', 'Notify_Party_Phone', 'Notify_Party_Email']
    df[notify_cols] = df['NOTIFY PARTY NAME'].apply(split_party_info)
    
    df['Delivery Type'] = df['CONTAINER INFO FROM TYPE 20 RECORD'].apply(
        lambda x: str(x).split('TYPE-Of-SVC=')[1].strip() if pd.notna(x) and 'TYPE-Of-SVC=' in str(x) else '')
    
    columns_to_keep = [
        'ACTUAL ARRIVAL DATE',
        *supplier_cols,
        *buyer_cols,
        'BOL',
        *notify_cols,
        'PORT OF UNLADING',
        'VESSEL NAME',
        'CONTAINER NUMBER',
        'Delivery Type'
    ]
    
    return df[columns_to_keep]

# Function to split by port
def split_by_port(df):
    port_dfs = {}
    for port in df['PORT OF UNLADING'].unique():
        port_dfs[port] = df[df['PORT OF UNLADING'] == port]
    return port_dfs

def main():
    st.title('CSV Processing Application')
    
    # Initialize session state
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'combined_df' not in st.session_state:
        st.session_state.combined_df = None
    if 'processed_df' not in st.session_state:
        st.session_state.processed_df = None

    # Progress bar
    st.progress(st.session_state.step/3)
    st.write(f"Step {st.session_state.step} of 3")

    # Step 1: File Combination
    if st.session_state.step == 1:
        st.header("Step 1: Combine CSV Files")
        uploaded_files = st.file_uploader("Upload CSV files", type='csv', accept_multiple_files=True)
        
        if uploaded_files:
            if st.button('Combine Files'):
                with st.spinner('Combining files...'):
                    st.session_state.combined_df = combine_csv_files(uploaded_files)
                    st.write("Preview of combined data:")
                    st.dataframe(st.session_state.combined_df.head())
                    st.success('Files combined successfully!')
                    st.session_state.step = 2

    # Step 2: Process Data
    elif st.session_state.step == 2:
        st.header("Step 2: Process Data")
        if st.session_state.combined_df is not None:
            if st.button('Process Data'):
                with st.spinner('Processing data...'):
                    st.session_state.processed_df = process_csv(st.session_state.combined_df)
                    st.write("Preview of processed data:")
                    st.dataframe(st.session_state.processed_df.head())
                    st.success('Data processed successfully!')
                    st.session_state.step = 3

    # Step 3: Split by Port
    elif st.session_state.step == 3:
        st.header("Step 3: Split by Port")
        if st.session_state.processed_df is not None:
            if st.button('Split by Port'):
                with st.spinner('Splitting files...'):
                    port_dfs = split_by_port(st.session_state.processed_df)
                    
                    # Create ZIP file containing all split files
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for port, df in port_dfs.items():
                            # Create CSV for each port
                            csv_buffer = io.StringIO()
                            df.to_csv(csv_buffer, index=False)
                            zip_file.writestr(f"PORT_{port}.csv", csv_buffer.getvalue())
                    
                    # Download button for ZIP file
                    st.download_button(
                        label="Download All Port Files (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name="port_files.zip",
                        mime="application/zip"
                    )
                    
                    # Show preview of each split
                    for port, df in port_dfs.items():
                        st.write(f"\nPreview of {port} data:")
                        st.dataframe(df.head())
                    
                    st.success('Files split successfully!')

    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.step > 1:
            if st.button('Previous Step'):
                st.session_state.step -= 1
    with col2:
        if st.session_state.step < 3:
            if st.button('Next Step'):
                st.session_state.step += 1

if __name__ == "__main__":
    main()
