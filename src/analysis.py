import pandas as pd
import requests
import os
import sys


def get_absolute_path(relative_path):
    """Returns the absolute path of a given relative path."""
    base_path = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(base_path, relative_path))


API_KEY = "RISSY9JLIY5NC3FN"  # Reemplaza con tu clave API de Alpha Vantage
API_URL = "https://www.alphavantage.co/query"


def get_market_prices(products):
    """Fetches market prices from the Alpha Vantage API."""
    market_prices = {}
    for product in products["product_name"]:
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": product,
            "interval": "5min",
            "apikey": API_KEY,
        }
        try:
            response = requests.get(API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            if "Time Series (5min)" in data:
                # Extract the latest closing price
                latest_time = list(data["Time Series (5min)"].keys())[0]
                market_prices[product] = float(
                    data["Time Series (5min)"][latest_time]["4. close"]
                )
            else:
                error_message = data.get(
                    "Note", data.get("Error Message", "Unknown error")
                )
                print(
                    f"Error: 'Time Series (5min)' not found in response for {product}. {error_message}"
                )
                market_prices[product] = None
        except requests.RequestException as e:
            print(f"Error fetching market prices for {product}: {e}")
            market_prices[product] = None
    products["market_price"] = products["product_name"].map(market_prices)
    return products


def load_data(file_path):
    """Loads data from a CSV file."""
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return pd.DataFrame()  # Return an empty DataFrame if the file is not found


def clean_data(df):
    """Cleans the data."""
    # Convert restock_date to datetime
    df["restock_date"] = pd.to_datetime(df["restock_date"], errors="coerce")

    # Convert current_stock to numeric, coerce errors to NaN
    df["current_stock"] = pd.to_numeric(df["current_stock"], errors="coerce")

    # Convert restock_threshold to numeric, coerce errors to NaN
    df["restock_threshold"] = pd.to_numeric(df["restock_threshold"], errors="coerce")

    # Fill missing prices with 0
    df["our_price"] = df["our_price"].fillna(0)

    # Standardize category names
    df["category"] = df["category"].str.capitalize()

    return df


def save_data(df, file_path):
    """Saves data to a CSV file."""
    df.to_csv(file_path, index=False)


def generate_report(df, file_path):
    """Generates a markdown report."""
    with open(file_path, "w") as f:
        f.write("# Product Report\n\n")
        f.write("## Summary\n")
        f.write(f"Total products: {len(df)}\n")
        f.write(f"Average price: ${df['our_price'].mean():.2f}\n")
        f.write(f"Average market price: ${df['market_price'].mean():.2f}\n")
        f.write("\n## Products\n")
        for _, row in df.iterrows():
            f.write(
                f"- {row['product_name']}: Our price ${row['our_price']}, Market price ${row['market_price']}\n"
            )


def main():
    if len(sys.argv) != 2:
        print("Usage: python src/analysis.py <path_to_csv_file>")
        return

    csv_file = sys.argv[1]
    cleaned_csv_file = get_absolute_path("cleaned_products.csv")
    report_file = get_absolute_path("report.md")

    # Load data
    df = load_data(csv_file)

    if df.empty:
        print("No data to process.")
        return

    # Clean data
    df = clean_data(df)

    # Get market prices
    df = get_market_prices(df)

    # Save cleaned data
    save_data(df, cleaned_csv_file)

    # Generate report
    generate_report(df, report_file)


if __name__ == "__main__":
    main()
