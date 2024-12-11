import streamlit as st
import pandas as pd
import io
import zipfile
from datetime import datetime

# Function to combine multiple CSV files
def combine_csv_files(uploaded_files):
    try:
        dfs = []
        for file in uploaded_files:
            df = pd.read_csv(file)
            dfs.append(df)
        combined_df = pd.concat(dfs, ignore_index=True)
        return combined_df, None
    except Exception as e:
        return None, f"Error combining files: {str(e)}"

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
    try:
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
        
        return df[columns_to_keep], None
    except Exception as e:
        return None, f"Error processing data: {str(e)}"

def split_by_port(df):
    try:
        port_dfs = {}
        for port in df['PORT OF UNLADING'].unique():
            port_dfs[port] = df[df['PORT OF UNLADING'] == port]
        return port_dfs, None
    except Exception as e:
        return None, f"Error splitting files: {str(e)}"

def main():
    st.title('CSV Processing Application')
    
    # Initialize session state
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'combined_df' not in st.session_state:
        st.session_state.combined_df = None
    if 'processed_df' not in st.session_state:
        st.session_state.processed_df = None
    if 'port_dfs' not in st.session_state:
        st.session_state.port_dfs = None

    # Progress bar
    st.progress(st.session_state.step/3)
    st.write(f"Step {st.session_state.step} of 3")

    # Step 1: File Combination
    if st.session_state.step == 1:
        st.header("Step 1: Combine CSV Files")
        uploaded_files = st.file_uploader("Upload CSV files", type='csv', accept_multiple_files=True)
        
        if uploaded_files:
            # In Step 1 section, replace the existing proceed button code with:
if st.button('Combine Files'):
    with st.spinner('Combining files...'):
        combined_df, error = combine_csv_files(uploaded_files)
        if error:
            st.error(error)
        else:
            st.session_state.combined_df = combined_df
            st.write("Preview of combined data:")
            st.dataframe(combined_df.head())
            st.success('Files combined successfully!')
            
            # Change this part
            if st.button('Proceed to Step 2', key='proceed_step2'):
                st.session_state.step = 2
                st.rerun()

    # Step 2: Process Data
    elif st.session_state.step == 2:
        st.header("Step 2: Process Data")
        if st.session_state.combined_df is not None:
            if st.button('Process Data'):
                with st.spinner('Processing data...'):
                    processed_df, error = process_csv(st.session_state.combined_df)
                    if error:
                        st.error(error)
                    else:
                        st.session_state.processed_df = processed_df
                        st.write("Preview of processed data:")
                        st.dataframe(processed_df.head())
                        st.success('Data processed successfully!')
                        if st.button('Proceed to Step 3'):
                            st.session_state.step = 3
                            st.experimental_rerun()

    # Step 3: Split by Port
    elif st.session_state.step == 3:
        st.header("Step 3: Split by Port")
        if st.session_state.processed_df is not None:
            if st.button('Split by Port'):
                with st.spinner('Splitting files...'):
                    port_dfs, error = split_by_port(st.session_state.processed_df)
                    if error:
                        st.error(error)
                    else:
                        st.session_state.port_dfs = port_dfs
                        
                        # Create ZIP file containing all split files
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for port, df in port_dfs.items():
                                # Create CSV for each port
                                csv_buffer = io.StringIO()
                                df.to_csv(csv_buffer, index=False)
                                zip_file.writestr(f"PORT_{port}_{timestamp}.csv", csv_buffer.getvalue())
                        
                        # Download buttons
                        st.download_button(
                            label="Download All Port Files (ZIP)",
                            data=zip_buffer.getvalue(),
                            file_name=f"port_files_{timestamp}.zip",
                            mime="application/zip"
                        )
                        
                        # Individual file downloads
                        st.write("Download Individual Port Files:")
                        for port, df in port_dfs.items():
                            csv_buffer = io.StringIO()
                            df.to_csv(csv_buffer, index=False)
                            st.download_button(
                                label=f"Download {port} data",
                                data=csv_buffer.getvalue(),
                                file_name=f"PORT_{port}_{timestamp}.csv",
                                mime="text/csv",
                                key=port
                            )
                            
                            st.write(f"\nPreview of {port} data:")
                            st.dataframe(df.head())
                        
                        st.success('Files split successfully!')

    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.step > 1:
            if st.button('Previous Step'):
                st.session_state.step -= 1
                st.experimental_rerun()

if __name__ == "__main__":
    main()
