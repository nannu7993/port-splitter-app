import streamlit as st
import pandas as pd
import io

def split_csv_by_port(df):
    # Get unique values from PORT OF UNLADING column
    unique_ports = df['PORT OF UNLADING'].unique()
    
    # Create a dictionary to store DataFrames for each port
    port_dfs = {}
    
    # Split the data based on port
    for port in unique_ports:
        port_dfs[port] = df[df['PORT OF UNLADING'] == port]
    
    return port_dfs

def main():
    st.title('CSV Splitter by Port of Unlading')
    
    # File uploader
    uploaded_file = st.file_uploader("Upload your CSV file", type=['csv'])
    
    if uploaded_file is not None:
        try:
            # Read the CSV file
            df = pd.read_csv(uploaded_file)
            
            # Display original data
            st.subheader('Original Data Preview')
            st.dataframe(df.head())
            
            # Split the data
            port_dfs = split_csv_by_port(df)
            
            # Create download buttons for each split file
            st.subheader('Download Split Files')
            
            for port, port_df in port_dfs.items():
                # Create a buffer for the CSV file
                csv_buffer = io.StringIO()
                port_df.to_csv(csv_buffer, index=False)
                
                # Create a download button
                csv_str = csv_buffer.getvalue()
                filename = f"PORT_{port.replace(' ', '_')}.csv"
                
                st.download_button(
                    label=f"Download {port} data",
                    data=csv_str,
                    file_name=filename,
                    mime='text/csv'
                )
                
                # Show preview of each split
                st.write(f"Preview of {port} data:")
                st.dataframe(port_df.head())
                st.write("---")
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()