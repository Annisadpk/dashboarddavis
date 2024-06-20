import streamlit as st
from sqlalchemy import create_engine
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import squarify
import mplcursors
import geopandas as gpd
from urllib.parse import quote_plus
import matplotlib.ticker as ticker

# Mengatur tampilan matplotlib untuk Streamlit
st.set_option('deprecation.showPyplotGlobalUse', False)

# Konfigurasi koneksi untuk SQLAlchemy
db_username = 'davis2024irwan'
db_password = 'wh451n9m@ch1n3'
db_host = 'kubela.id'
db_name = 'aw'

encoded_password = quote_plus(db_password)
connection_string = f'mysql+mysqlconnector://{db_username}:{encoded_password}@{db_host}/{db_name}'
engine = create_engine(connection_string)

# Fungsi untuk menjalankan query dan mengembalikan dataframe
def run_query(query):
    with engine.connect() as connection:
        return pd.read_sql(query, connection)

# Fungsi untuk plot Top 10 Produk Terlaris
def plot_top_10_products():
    query = """
    SELECT 
        p.ProductKey,
        p.EnglishProductName,
        SUM(s.OrderQuantity) AS TotalSales
    FROM 
        factinternetsales s
    JOIN 
        dimproduct p ON s.ProductKey = p.ProductKey
    GROUP BY 
        p.ProductKey, p.EnglishProductName
    ORDER BY 
        TotalSales DESC
    LIMIT 10;
    """
    data = run_query(query)
    plt.figure(figsize=(12, 8))
    sns.barplot(x='EnglishProductName', y='TotalSales', data=data, palette='pastel', dodge=False)
    plt.title("Top 10 Produk Terlaris")
    plt.xlabel('Nama Produk')
    plt.ylabel('Jumlah Penjualan')
    plt.xticks(rotation=45, ha='right')
    st.pyplot(plt)

# Fungsi untuk plot Penjualan Berdasarkan Kategori
def plot_sales_by_category():
    query = """
    SELECT 
        pc.EnglishProductCategoryName,
        SUM(s.OrderQuantity) AS TotalSales
    FROM 
        factinternetsales s
    JOIN 
        dimproduct p ON s.ProductKey = p.ProductKey
    JOIN 
        dimproductsubcategory psc ON p.ProductSubcategoryKey = psc.ProductSubcategoryKey
    JOIN 
        dimproductcategory pc ON psc.ProductCategoryKey = pc.ProductCategoryKey
    GROUP BY 
        pc.EnglishProductCategoryName
    """
    data = run_query(query)
    plt.figure(figsize=(10, 8))
    plt.barh(data['EnglishProductCategoryName'], data['TotalSales'], color=plt.cm.tab20.colors)
    plt.title("Perbandingan Penjualan Produk Berdasarkan Kategori")
    plt.xlabel('Total Penjualan')
    plt.ylabel('Kategori Produk')
    st.pyplot(plt)

# Fungsi untuk plot Pendapatan Perusahaan Pertahun
def plot_revenue_per_year():
    query = """
    SELECT 
        t.CalendarYear,
        SUM(ff.Amount) AS TotalRevenue
    FROM 
        dimtime t
    JOIN 
        factfinance ff ON t.TimeKey = ff.TimeKey
    GROUP BY 
        t.CalendarYear
    ORDER BY 
        t.CalendarYear
    """
    data = run_query(query)
    plt.figure(figsize=(12, 8))
    plt.plot(data['CalendarYear'], data['TotalRevenue'], marker='o', linestyle='-')
    plt.title("Pendapatan Perusahaan Pertahun")
    plt.xlabel('Tahun')
    plt.ylabel('Pendapatan Total')
    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: '{:,.0f}'.format(x)))
    st.pyplot(plt)

# Fungsi untuk plot Stacked Area Chart Pendapatan Per Kategori
def plot_stacked_area_chart():
    query = """
    SELECT 
        t.CalendarYear,
        pc.EnglishProductCategoryName,
        SUM(fs.SalesAmount) AS TotalSales
    FROM 
        dimtime t
    JOIN 
        factinternetsales fs ON t.TimeKey = fs.OrderDateKey
    JOIN 
        dimproduct p ON fs.ProductKey = p.ProductKey
    JOIN 
        dimproductsubcategory psc ON p.ProductSubcategoryKey = psc.ProductSubcategoryKey
    JOIN 
        dimproductcategory pc ON psc.ProductCategoryKey = pc.ProductCategoryKey
    GROUP BY 
        t.CalendarYear, pc.EnglishProductCategoryName
    ORDER BY 
        t.CalendarYear, pc.EnglishProductCategoryName
    """
    data = run_query(query)
    data_pivot = data.pivot_table(index='CalendarYear', columns='EnglishProductCategoryName', values='TotalSales', aggfunc='sum', fill_value=0)
    plt.figure(figsize=(12, 8))
    sns.set_palette("pastel")
    data_pivot.plot(kind='area', stacked=True)
    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:,.0f}'.format(x)))
    plt.title("Pendapatan Perusahaan Per Kategori Produk Tiap Tahun")
    plt.xlabel('Tahun')
    plt.ylabel('Pendapatan Total')
    mplcursors.cursor(hover=True)
    plt.grid(False)
    plt.legend(title='Kategori Produk', loc='upper left')
    st.pyplot(plt)

# Fungsi untuk plot Donut Chart Penjualan Per Kategori
def plot_donut_chart():
    query = """
    SELECT 
        pc.EnglishProductCategoryName,
        SUM(fs.OrderQuantity) AS TotalOrderQuantity
    FROM 
        factinternetsales fs
    JOIN 
        dimproduct p ON fs.ProductKey = p.ProductKey
    JOIN 
        dimproductsubcategory psc ON p.ProductSubcategoryKey = psc.ProductSubcategoryKey
    JOIN 
        dimproductcategory pc ON psc.ProductCategoryKey = pc.ProductCategoryKey
    GROUP BY 
        pc.EnglishProductCategoryName
    ORDER BY 
        TotalOrderQuantity DESC;
    """
    data = run_query(query)
    plt.figure(figsize=(10, 8))
    plt.pie(data['TotalOrderQuantity'], labels=data['EnglishProductCategoryName'], autopct='%1.1f%%', startangle=90, pctdistance=0.85)
    centre_circle = plt.Circle((0,0),0.70,fc='white')
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)
    plt.title("Komposisi Jumlah Penjualan Unit Produk Tiap Kategori")
    plt.axis('equal')
    st.pyplot(plt)

# Fungsi untuk plot TreeMap Komposisi Produk
def plot_treemap():
    query = """
    SELECT 
        pc.EnglishProductCategoryName AS Category,
        ps.EnglishProductSubcategoryName AS Subcategory,
        p.EnglishProductName AS Product,
        SUM(s.OrderQuantity) AS TotalSales
    FROM 
        factinternetsales s
    JOIN 
        dimproduct p ON s.ProductKey = p.ProductKey
    JOIN 
        dimproductsubcategory ps ON p.ProductSubcategoryKey = ps.ProductSubcategoryKey
    JOIN 
        dimproductcategory pc ON ps.ProductCategoryKey = pc.ProductCategoryKey
    GROUP BY 
        pc.EnglishProductCategoryName, ps.EnglishProductSubcategoryName, p.EnglishProductName
    """
    data = run_query(query)
    total_sales_category = data.groupby('Category')['TotalSales'].sum()
    plt.figure(figsize=(12, 8))
    colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99']
    squarify.plot(sizes=total_sales_category, color=colors, label=total_sales_category.index, alpha=0.7)
    plt.title("TreeMap Komposisi Produk yang Terjual Berdasarkan Kategori Produk")
    plt.axis('off')
    st.pyplot(plt)

# Fungsi untuk plot Komposisi Penjualan Berdasarkan Wilayah Penjualan
def plot_sales_per_region():
    sales_data = run_query("SELECT * FROM factinternetsales")
    territory_data = run_query("SELECT * FROM dimsalesterritory")
    merged_data = pd.merge(sales_data, territory_data, on="SalesTerritoryKey")
    total_sales_per_region = merged_data.groupby(["SalesTerritoryRegion"]).agg({"SalesAmount": "sum"}).reset_index()
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    world = world.merge(total_sales_per_region, how="left", left_on="name", right_on="SalesTerritoryRegion")
    fig, ax = plt.subplots(1, 1, figsize=(15, 10))
    world.plot(column="SalesAmount", ax=ax, legend=True, cmap="Oranges", edgecolor="grey", linewidth=0.5)
    ax.set_title("Komposisi Penjualan Berdasarkan Wilayah Penjualan")
    st.pyplot(fig)

# Fungsi untuk plot Scatter Hubungan Antara Harga Produk dan Jumlah Terjual
def plot_scatter_price_sales():
    query = """
    SELECT 
        p.ListPrice AS ProductPrice,
        SUM(s.OrderQuantity) AS UnitsSold
    FROM 
        factinternetsales s
    JOIN 
        dimproduct p ON s.ProductKey = p.ProductKey
    GROUP BY 
        p.ListPrice
    """
    data = run_query(query)
    plt.figure(figsize=(10, 6))
    plt.scatter(data['ProductPrice'], data['UnitsSold'], color='blue')
    plt.title('Hubungan Antara Harga Produk dan Jumlah Terjual')
    plt.xlabel('Harga Produk')
    plt.ylabel('Jumlah Terjual')
    st.pyplot(plt)

# Fungsi untuk plot Histogram Distribusi Harga Produk
def plot_histogram_price_distribution():
    query = """
    SELECT 
        ListPrice
    FROM 
        dimproduct
    """
    data_price = run_query(query)
    plt.figure(figsize=(10, 6))
    sns.histplot(x='ListPrice', data=data_price, kde=True)
    plt.title('Distribusi Harga Produk')
    plt.xlabel('Harga Produk')
    plt.ylabel('Frekuensi')
    st.pyplot(plt)
# Plot Pertumbuhan Jumlah Pelanggan Setiap Tahun
def plot_customer_growth():
    query = """
    SELECT 
        YEAR(c.DateFirstPurchase) AS PurchaseYear,
        COUNT(c.CustomerKey) AS CustomerCount
    FROM 
        dimcustomer c
    WHERE 
        c.DateFirstPurchase IS NOT NULL
    GROUP BY 
        PurchaseYear
    """
    data = run_query(query)
    plt.figure(figsize=(12, 6))
    plt.plot(data['PurchaseYear'], data['CustomerCount'], marker='o', color='b')
    plt.title('Pertumbuhan Jumlah Pelanggan Setiap Tahun')
    plt.xlabel('Tahun')
    plt.ylabel('Jumlah Pelanggan')
    plt.grid(False)
    st.pyplot(plt)

# Plot Distribusi Pelanggan Berdasarkan Kota
def plot_customer_distribution_city():
    query = """
    SELECT 
        COUNT(c.CustomerKey) AS CustomerCount,
        g.City,
        g.StateProvinceName,
        g.CountryRegionCode,
        g.SalesTerritoryKey
    FROM 
        dimcustomer c
    JOIN 
        dimgeography g ON c.GeographyKey = g.GeographyKey
    GROUP BY
        g.City,
        g.StateProvinceName,
        g.CountryRegionCode,
        g.SalesTerritoryKey
    """
    data = run_query(query)
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    merged_data = world.merge(data, how='left', left_on='name', right_on='City')
    fig, ax = plt.subplots(figsize=(10, 6))
    merged_data.plot(column='CustomerCount', cmap='Blues', linewidth=0.8, ax=ax, edgecolor='0.8', legend=True)
    plt.title('Distribusi Pelanggan Berdasarkan Kota')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    st.pyplot(plt)

# Plot Donut Chart Pelanggan berdasarkan Status Pernikahan
def plot_donut_marital_status():
    query = "SELECT * FROM dimcustomer"
    customer_data = run_query(query)
    plt.figure(figsize=(8, 8))
    customer_data['MaritalStatus'].value_counts().plot.pie(autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.4), labels=None)
    plt.title('Donut chart Pelanggan berdasarkan Status Pernikahan')
    plt.legend(labels=customer_data['MaritalStatus'].value_counts().index, loc='best')
    plt.axis('equal')
    st.pyplot(plt)

# Plot Pie Chart jumlah Pelanggan berdasarkan Pendidikan
def plot_pie_education():
    query = "SELECT * FROM dimcustomer"
    customer_data = run_query(query)
    plt.figure(figsize=(8, 8))
    customer_data['EnglishEducation'].value_counts().plot.pie(autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=1), labels=None)
    plt.title('Pie chart jumlah Pelanggan berdasarkan Pendidikan')
    plt.legend(labels=customer_data['EnglishEducation'].value_counts().index, loc='best')
    plt.axis('equal')
    st.pyplot(plt)

# Plot Barchart jumlah Pelanggan berdasarkan Pekerjaan
def plot_bar_occupation():
    query = "SELECT * FROM dimcustomer"
    customer_data = run_query(query)
    plt.figure(figsize=(10, 6))
    sns.countplot(data=customer_data, x='EnglishOccupation')
    plt.title('Barchart jumlah Pelanggan berdasarkan Pekerjaan')
    plt.xlabel('Pekerjaan')
    plt.ylabel('Jumlah Pelanggan')
    plt.xticks(rotation=45)
    st.pyplot(plt)

# Plot Distribusi Pelanggan berdasarkan Negara
def plot_customer_distribution_country():
    query = """
    SELECT g.EnglishCountryRegionName as name , COUNT(c.CustomerKey) as CustomerCount
    FROM dimcustomer c
    JOIN dimgeography g ON c.GeographyKey = g.GeographyKey
    GROUP BY g.EnglishCountryRegionName
    """
    country_data = run_query(query)
    country_map = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    merged_data = country_map.merge(country_data, left_on='name', right_on='name', how='left')
    plt.figure(figsize=(15, 10))
    merged_data.plot(column='CustomerCount', cmap='Blues', edgecolor='0.9', legend=True)
    for idx, row in merged_data.iterrows():
        if not pd.isnull(row['name']) and row.geometry is not None:
            plt.text(row.geometry.centroid.x, row.geometry.centroid.y, row['name'], fontsize=8, ha='center')
    plt.title('Distribusi Pelanggan berdasarkan Negara')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    st.pyplot(plt)

# Plot Histogram distribusi usia pelanggan
def plot_age_distribution():
    query_last_date = "SELECT MAX(FullDateAlternateKey) FROM dimtime"
    last_date = run_query(query_last_date)['MAX(FullDateAlternateKey)'].iloc[0]
    query_customer = "SELECT CustomerKey, BirthDate FROM dimcustomer"
    customer_data = run_query(query_customer)
    customer_data['BirthDate'] = pd.to_datetime(customer_data['BirthDate'])
    customer_data['Age'] = (last_date - customer_data['BirthDate']).dt.days // 365
    plt.figure(figsize=(10, 6))
    sns.histplot(data=customer_data, x='Age', bins=30, kde=True)
    plt.title('Histogram distribusi usia pelanggan')
    plt.xlabel('Usia')
    plt.ylabel('Jumlah Pelanggan')
    st.pyplot(plt)

# Plot Scatter Plot Pendapatan Tahunan vs. Total Pembelian
def plot_income_vs_sales():
    query = """
    SELECT 
        c.YearlyIncome AS YearlyIncome,
        SUM(sales.SalesAmount) AS TotalSalesAmount
    FROM 
        dimcustomer c
    JOIN 
        factinternetsales sales ON c.CustomerKey = sales.CustomerKey
    GROUP BY 
        c.YearlyIncome;
    """
    df = run_query(query)
    plt.figure(figsize=(10, 6))
    plt.scatter(df['YearlyIncome'], df['TotalSalesAmount'], alpha=0.5)
    plt.title('Scatter Plot Pendapatan Tahunan vs. Total Pembelian')
    plt.xlabel('Pendapatan Tahunan')
    plt.ylabel('Total Pembelian')
    plt.grid(True)
    st.pyplot(plt)

# Streamlit Layout
st.title('Adventure Works')

st.sidebar.title('Adventure Works')
option = st.sidebar.selectbox('Menu', [
    'Sales Performance Overview',
    'Customer Analysis',
    'Operational Performance Overview'
])

if option == 'Sales Performance Overview':
    plot_top_10_products()
    plot_sales_by_category()
    plot_revenue_per_year()
    plot_stacked_area_chart()
    plot_donut_chart()
    plot_treemap()
    plot_sales_per_region()
    plot_scatter_price_sales()
    plot_histogram_price_distribution()
elif option == 'Customer Analysis':
    plot_customer_growth()
    plot_customer_distribution_city()
    plot_donut_marital_status()
    plot_pie_education()
    plot_bar_occupation()
    plot_customer_distribution_country()
    plot_age_distribution()
    plot_income_vs_sales()
elif option == 'Operational Performance Overview':
