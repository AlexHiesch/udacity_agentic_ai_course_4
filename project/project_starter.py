import pandas as pd
import numpy as np
import os
import time
import dotenv
import ast
import re
import json
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import Dict, List, Union
from sqlalchemy import create_engine, Engine

# Import smolagents for tool decoration
from smolagents import tool

# Create an SQLite database
db_engine = create_engine("sqlite:///munder_difflin.db")

# List containing the different kinds of papers 
paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper",                         "category": "paper",        "unit_price": 0.05},
    {"item_name": "Letter-sized paper",              "category": "paper",        "unit_price": 0.06},
    {"item_name": "Cardstock",                        "category": "paper",        "unit_price": 0.15},
    {"item_name": "Colored paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Glossy paper",                     "category": "paper",        "unit_price": 0.20},
    {"item_name": "Matte paper",                      "category": "paper",        "unit_price": 0.18},
    {"item_name": "Recycled paper",                   "category": "paper",        "unit_price": 0.08},
    {"item_name": "Eco-friendly paper",               "category": "paper",        "unit_price": 0.12},
    {"item_name": "Poster paper",                     "category": "paper",        "unit_price": 0.25},
    {"item_name": "Banner paper",                     "category": "paper",        "unit_price": 0.30},
    {"item_name": "Kraft paper",                      "category": "paper",        "unit_price": 0.10},
    {"item_name": "Construction paper",               "category": "paper",        "unit_price": 0.07},
    {"item_name": "Wrapping paper",                   "category": "paper",        "unit_price": 0.15},
    {"item_name": "Glitter paper",                    "category": "paper",        "unit_price": 0.22},
    {"item_name": "Decorative paper",                 "category": "paper",        "unit_price": 0.18},
    {"item_name": "Letterhead paper",                 "category": "paper",        "unit_price": 0.12},
    {"item_name": "Legal-size paper",                 "category": "paper",        "unit_price": 0.08},
    {"item_name": "Crepe paper",                      "category": "paper",        "unit_price": 0.05},
    {"item_name": "Photo paper",                      "category": "paper",        "unit_price": 0.25},
    {"item_name": "Uncoated paper",                   "category": "paper",        "unit_price": 0.06},
    {"item_name": "Butcher paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Heavyweight paper",                "category": "paper",        "unit_price": 0.20},
    {"item_name": "Standard copy paper",              "category": "paper",        "unit_price": 0.04},
    {"item_name": "Bright-colored paper",             "category": "paper",        "unit_price": 0.12},
    {"item_name": "Patterned paper",                  "category": "paper",        "unit_price": 0.15},

    # Product Types (priced per unit)
    {"item_name": "Paper plates",                     "category": "product",      "unit_price": 0.10},  # per plate
    {"item_name": "Paper cups",                       "category": "product",      "unit_price": 0.08},  # per cup
    {"item_name": "Paper napkins",                    "category": "product",      "unit_price": 0.02},  # per napkin
    {"item_name": "Disposable cups",                  "category": "product",      "unit_price": 0.10},  # per cup
    {"item_name": "Table covers",                     "category": "product",      "unit_price": 1.50},  # per cover
    {"item_name": "Envelopes",                        "category": "product",      "unit_price": 0.05},  # per envelope
    {"item_name": "Sticky notes",                     "category": "product",      "unit_price": 0.03},  # per sheet
    {"item_name": "Notepads",                         "category": "product",      "unit_price": 2.00},  # per pad
    {"item_name": "Invitation cards",                 "category": "product",      "unit_price": 0.50},  # per card
    {"item_name": "Flyers",                           "category": "product",      "unit_price": 0.15},  # per flyer
    {"item_name": "Party streamers",                  "category": "product",      "unit_price": 0.05},  # per roll
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},  # per roll
    {"item_name": "Paper party bags",                 "category": "product",      "unit_price": 0.25},  # per bag
    {"item_name": "Name tags with lanyards",          "category": "product",      "unit_price": 0.75},  # per tag
    {"item_name": "Presentation folders",             "category": "product",      "unit_price": 0.50},  # per folder

    # Large-format items (priced per unit)
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},

    # Specialty papers
    {"item_name": "100 lb cover stock",               "category": "specialty",    "unit_price": 0.50},
    {"item_name": "80 lb text paper",                 "category": "specialty",    "unit_price": 0.40},
    {"item_name": "250 gsm cardstock",                "category": "specialty",    "unit_price": 0.30},
    {"item_name": "220 gsm poster paper",             "category": "specialty",    "unit_price": 0.35},
]

# Given below are some utility functions you can use to implement your multi-agent system

def generate_sample_inventory(paper_supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    """
    Generate inventory for exactly a specified percentage of items from the full paper supply list.

    This function randomly selects exactly `coverage` × N items from the `paper_supplies` list,
    and assigns each selected item:
    - a random stock quantity between 200 and 800,
    - a minimum stock level between 50 and 150.

    The random seed ensures reproducibility of selection and stock levels.

    Args:
        paper_supplies (list): A list of dictionaries, each representing a paper item with
                               keys 'item_name', 'category', and 'unit_price'.
        coverage (float, optional): Fraction of items to include in the inventory (default is 0.4, or 40%).
        seed (int, optional): Random seed for reproducibility (default is 137).

    Returns:
        pd.DataFrame: A DataFrame with the selected items and assigned inventory values, including:
                      - item_name
                      - category
                      - unit_price
                      - current_stock
                      - min_stock_level
    """
    # Ensure reproducible random output
    np.random.seed(seed)

    # Calculate number of items to include based on coverage
    num_items = int(len(paper_supplies) * coverage)

    # Randomly select item indices without replacement
    selected_indices = np.random.choice(
        range(len(paper_supplies)),
        size=num_items,
        replace=False
    )

    # Extract selected items from paper_supplies list
    selected_items = [paper_supplies[i] for i in selected_indices]

    # Construct inventory records
    inventory = []
    for item in selected_items:
        inventory.append({
            "item_name": item["item_name"],
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": np.random.randint(200, 800),  # Realistic stock range
            "min_stock_level": np.random.randint(50, 150)  # Reasonable threshold for reordering
        })

    # Return inventory as a pandas DataFrame
    return pd.DataFrame(inventory)

def init_database(db_engine: Engine, seed: int = 137) -> Engine:    
    """
    Set up the Munder Difflin database with all required tables and initial records.

    This function performs the following tasks:
    - Creates the 'transactions' table for logging stock orders and sales
    - Loads customer inquiries from 'quote_requests.csv' into a 'quote_requests' table
    - Loads previous quotes from 'quotes.csv' into a 'quotes' table, extracting useful metadata
    - Generates a random subset of paper inventory using `generate_sample_inventory`
    - Inserts initial financial records including available cash and starting stock levels

    Args:
        db_engine (Engine): A SQLAlchemy engine connected to the SQLite database.
        seed (int, optional): A random seed used to control reproducibility of inventory stock levels.
                              Default is 137.

    Returns:
        Engine: The same SQLAlchemy engine, after initializing all necessary tables and records.

    Raises:
        Exception: If an error occurs during setup, the exception is printed and raised.
    """
    try:
        # ----------------------------
        # 1. Create an empty 'transactions' table schema
        # ----------------------------
        transactions_schema = pd.DataFrame({
            "id": [],
            "item_name": [],
            "transaction_type": [],  # 'stock_orders' or 'sales'
            "units": [],             # Quantity involved
            "price": [],             # Total price for the transaction
            "transaction_date": [],  # ISO-formatted date
        })
        transactions_schema.to_sql("transactions", db_engine, if_exists="replace", index=False)

        # Set a consistent starting date
        initial_date = datetime(2025, 1, 1).isoformat()

        # ----------------------------
        # 2. Load and initialize 'quote_requests' table
        # ----------------------------
        quote_requests_df = pd.read_csv("quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 3. Load and transform 'quotes' table
        # ----------------------------
        quotes_df = pd.read_csv("quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date

        # Unpack metadata fields (job_type, order_size, event_type) if present
        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))

        # Retain only relevant columns
        quotes_df = quotes_df[[
            "request_id",
            "total_amount",
            "quote_explanation",
            "order_date",
            "job_type",
            "order_size",
            "event_type"
        ]]
        quotes_df.to_sql("quotes", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 4. Generate inventory and seed stock
        # ----------------------------
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)

        # Seed initial transactions
        initial_transactions = []

        # Add a starting cash balance via a dummy sales transaction
        initial_transactions.append({
            "item_name": None,
            "transaction_type": "sales",
            "units": None,
            "price": 50000.0,
            "transaction_date": initial_date,
        })

        # Add one stock order transaction per inventory item
        for _, item in inventory_df.iterrows():
            initial_transactions.append({
                "item_name": item["item_name"],
                "transaction_type": "stock_orders",
                "units": item["current_stock"],
                "price": item["current_stock"] * item["unit_price"],
                "transaction_date": initial_date,
            })

        # Commit transactions to database
        pd.DataFrame(initial_transactions).to_sql("transactions", db_engine, if_exists="append", index=False)

        # Save the inventory reference table
        inventory_df.to_sql("inventory", db_engine, if_exists="replace", index=False)

        return db_engine

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: Union[str, datetime],
) -> int:
    """
    This function records a transaction of type 'stock_orders' or 'sales' with a specified
    item name, quantity, total price, and transaction date into the 'transactions' table of the database.

    Args:
        item_name (str): The name of the item involved in the transaction.
        transaction_type (str): Either 'stock_orders' or 'sales'.
        quantity (int): Number of units involved in the transaction.
        price (float): Total price of the transaction.
        date (str or datetime): Date of the transaction in ISO 8601 format.

    Returns:
        int: The ID of the newly inserted transaction.

    Raises:
        ValueError: If `transaction_type` is not 'stock_orders' or 'sales'.
        Exception: For other database or execution errors.
    """
    try:
        # Convert datetime to ISO string if necessary
        date_str = date.isoformat() if isinstance(date, datetime) else date

        # Validate transaction type
        if transaction_type not in {"stock_orders", "sales"}:
            raise ValueError("Transaction type must be 'stock_orders' or 'sales'")

        # Prepare transaction record as a single-row DataFrame
        transaction = pd.DataFrame([{
            "item_name": item_name,
            "transaction_type": transaction_type,
            "units": quantity,
            "price": price,
            "transaction_date": date_str,
        }])

        # Insert the record into the database
        transaction.to_sql("transactions", db_engine, if_exists="append", index=False)

        # Fetch and return the ID of the inserted row
        result = pd.read_sql("SELECT last_insert_rowid() as id", db_engine)
        return int(result.iloc[0]["id"])

    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise

def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """
    Retrieve a snapshot of available inventory as of a specific date.

    This function calculates the net quantity of each item by summing 
    all stock orders and subtracting all sales up to and including the given date.

    Only items with positive stock are included in the result.

    Args:
        as_of_date (str): ISO-formatted date string (YYYY-MM-DD) representing the inventory cutoff.

    Returns:
        Dict[str, int]: A dictionary mapping item names to their current stock levels.
    """
    # SQL query to compute stock levels per item as of the given date
    query = """
        SELECT
            item_name,
            SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL
        AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """

    # Execute the query with the date parameter
    result = pd.read_sql(query, db_engine, params={"as_of_date": as_of_date})

    # Convert the result into a dictionary {item_name: stock}
    return dict(zip(result["item_name"], result["stock"]))

def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Retrieve the stock level of a specific item as of a given date.

    This function calculates the net stock by summing all 'stock_orders' and 
    subtracting all 'sales' transactions for the specified item up to the given date.

    Args:
        item_name (str): The name of the item to look up.
        as_of_date (str or datetime): The cutoff date (inclusive) for calculating stock.

    Returns:
        pd.DataFrame: A single-row DataFrame with columns 'item_name' and 'current_stock'.
    """
    # Convert date to ISO string format if it's a datetime object
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # SQL query to compute net stock level for the item
    stock_query = """
        SELECT
            item_name,
            COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
        FROM transactions
        WHERE item_name = :item_name
        AND transaction_date <= :as_of_date
    """

    # Execute query and return result as a DataFrame
    return pd.read_sql(
        stock_query,
        db_engine,
        params={"item_name": item_name, "as_of_date": as_of_date},
    )

def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """
    Estimate the supplier delivery date based on the requested order quantity and a starting date.

    Delivery lead time increases with order size:
        - ≤10 units: same day
        - 11–100 units: 1 day
        - 101–1000 units: 4 days
        - >1000 units: 7 days

    Args:
        input_date_str (str): The starting date in ISO format (YYYY-MM-DD).
        quantity (int): The number of units in the order.

    Returns:
        str: Estimated delivery date in ISO format (YYYY-MM-DD).
    """
    # Debug log (comment out in production if needed)
    print(f"FUNC (get_supplier_delivery_date): Calculating for qty {quantity} from date string '{input_date_str}'")

    # Attempt to parse the input date
    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        # Fallback to current date on format error
        print(f"WARN (get_supplier_delivery_date): Invalid date format '{input_date_str}', using today as base.")
        input_date_dt = datetime.now()

    # Determine delivery delay based on quantity
    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    # Add delivery days to the starting date
    delivery_date_dt = input_date_dt + timedelta(days=days)

    # Return formatted delivery date
    return delivery_date_dt.strftime("%Y-%m-%d")

def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """
    Calculate the current cash balance as of a specified date.

    The balance is computed by subtracting total stock purchase costs ('stock_orders')
    from total revenue ('sales') recorded in the transactions table up to the given date.

    Args:
        as_of_date (str or datetime): The cutoff date (inclusive) in ISO format or as a datetime object.

    Returns:
        float: Net cash balance as of the given date. Returns 0.0 if no transactions exist or an error occurs.
    """
    try:
        # Convert date to ISO format if it's a datetime object
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.isoformat()

        # Query all transactions on or before the specified date
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            db_engine,
            params={"as_of_date": as_of_date},
        )

        # Compute the difference between sales and stock purchases
        if not transactions.empty:
            total_sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
            total_purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
            return float(total_sales - total_purchases)

        return 0.0

    except Exception as e:
        print(f"Error getting cash balance: {e}")
        return 0.0


def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """
    Generate a complete financial report for the company as of a specific date.

    This includes:
    - Cash balance
    - Inventory valuation
    - Combined asset total
    - Itemized inventory breakdown
    - Top 5 best-selling products

    Args:
        as_of_date (str or datetime): The date (inclusive) for which to generate the report.

    Returns:
        Dict: A dictionary containing the financial report fields:
            - 'as_of_date': The date of the report
            - 'cash_balance': Total cash available
            - 'inventory_value': Total value of inventory
            - 'total_assets': Combined cash and inventory value
            - 'inventory_summary': List of items with stock and valuation details
            - 'top_selling_products': List of top 5 products by revenue
    """
    # Normalize date input
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # Get current cash balance
    cash = get_cash_balance(as_of_date)

    # Get current inventory snapshot
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    inventory_value = 0.0
    inventory_summary = []

    # Compute total inventory value and summary by item
    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level(item["item_name"], as_of_date)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value

        inventory_summary.append({
            "item_name": item["item_name"],
            "stock": stock,
            "unit_price": item["unit_price"],
            "value": item_value,
        })

    # Identify top-selling products by revenue
    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, db_engine, params={"date": as_of_date})
    top_selling_products = top_sales.to_dict(orient="records")

    return {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_selling_products,
    }


def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """
    Retrieve a list of historical quotes that match any of the provided search terms.

    The function searches both the original customer request (from `quote_requests`) and
    the explanation for the quote (from `quotes`) for each keyword. Results are sorted by
    most recent order date and limited by the `limit` parameter.

    Args:
        search_terms (List[str]): List of terms to match against customer requests and explanations.
        limit (int, optional): Maximum number of quote records to return. Default is 5.

    Returns:
        List[Dict]: A list of matching quotes, each represented as a dictionary with fields:
            - original_request
            - total_amount
            - quote_explanation
            - job_type
            - order_size
            - event_type
            - order_date
    """
    conditions = []
    params = {}

    # Build SQL WHERE clause using LIKE filters for each search term
    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(
            f"(LOWER(qr.response) LIKE :{param_name} OR "
            f"LOWER(q.quote_explanation) LIKE :{param_name})"
        )
        params[param_name] = f"%{term.lower()}%"

    # Combine conditions; fallback to always-true if no terms provided
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Final SQL query to join quotes with quote_requests
    query = f"""
        SELECT
            qr.response AS original_request,
            q.total_amount,
            q.quote_explanation,
            q.job_type,
            q.order_size,
            q.event_type,
            q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """

    # Execute parameterized query
    with db_engine.connect() as conn:
        result = conn.execute(text(query), params)
        rows = result.fetchall()
        columns = result.keys()
        return [dict(zip(columns, row)) for row in rows]

########################
########################
########################
# YOUR MULTI AGENT STARTS HERE
########################
########################
########################


# Set up and load your env parameters and instantiate your model.
dotenv.load_dotenv()

# Import smolagents framework
from smolagents import CodeAgent, ToolCallingAgent, tool, LiteLLMModel
import json

# Initialize OpenAI client for direct LLM calls
from openai import OpenAI
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://openai.vocareum.com/v1")
)

# Initialize LiteLLM model for smolagents (if needed for tool calling agents)
model = LiteLLMModel(
    model_id="openai/gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
    api_base=os.getenv("OPENAI_BASE_URL", "https://openai.vocareum.com/v1")
)


"""Set up tools for your agents to use, these should be methods that combine the database functions above
 and apply criteria to them to ensure that the flow of the system is correct."""


# Tools for inventory agent using smolagents @tool decorator

@tool
def check_inventory_availability(item_name: str, quantity: int, date: str) -> str:
    """
    Check if an item is available in sufficient quantity.
    
    Args:
        item_name: Name of the item to check
        quantity: Requested quantity
        date: Date in YYYY-MM-DD format
        
    Returns:
        JSON string with availability status and stock information
    """
    stock_info = get_stock_level(item_name, date)
    current_stock = int(stock_info["current_stock"].iloc[0]) if not stock_info.empty else 0
    
    result = {
        "item_name": item_name,
        "requested_quantity": quantity,
        "current_stock": current_stock,
        "available": current_stock >= quantity,
        "shortfall": max(0, quantity - current_stock)
    }
    return json.dumps(result)


@tool
def get_inventory_list(date: str) -> str:
    """
    Get a formatted list of all available inventory items with their prices.
    
    Args:
        date: Date in YYYY-MM-DD format for checking inventory
        
    Returns:
        Formatted string listing all available items with prices
    """
    inventory_dict = get_all_inventory(date)
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    
    result = "Available Inventory:\n"
    for _, item in inventory_df.iterrows():
        item_name = item["item_name"]
        stock = inventory_dict.get(item_name, 0)
        if stock > 0:
            result += f"- {item_name}: {stock} units @ ${item['unit_price']:.2f} each\n"
    
    return result


@tool
def check_restock_needed(item_name: str, date: str) -> str:
    """
    Check if an item needs restocking based on minimum stock levels.
    
    Args:
        item_name: Name of the item to check
        date: Date in YYYY-MM-DD format
        
    Returns:
        JSON string with restock recommendation
    """
    stock_info = get_stock_level(item_name, date)
    inventory_df = pd.read_sql("SELECT * FROM inventory WHERE item_name = ?", 
                               db_engine, params=(item_name,))
    
    if stock_info.empty or inventory_df.empty:
        return json.dumps({"needs_restock": False, "reason": "Item not found"})
    
    current_stock = int(stock_info["current_stock"].iloc[0])
    min_stock = int(inventory_df["min_stock_level"].iloc[0])
    
    needs_restock = current_stock < min_stock
    return json.dumps({
        "needs_restock": needs_restock,
        "current_stock": current_stock,
        "min_stock": min_stock
    })


# Tools for quoting agent

@tool
def calculate_bulk_discount(quantity: int, unit_price: float) -> str:
    """
    Calculate bulk discount based on quantity.
    - 100-500 units: 5% discount
    - 501-1000 units: 10% discount
    - 1001+ units: 15% discount
    
    Args:
        quantity: Number of units
        unit_price: Price per unit
        
    Returns:
        JSON string with total price after discount
    """
    total = quantity * unit_price
    
    if quantity >= 1001:
        discount = 0.15
    elif quantity >= 501:
        discount = 0.10
    elif quantity >= 100:
        discount = 0.05
    else:
        discount = 0.0
    
    final_price = total * (1 - discount)
    return json.dumps({
        "total_before_discount": total,
        "discount_percent": discount * 100,
        "final_price": final_price
    })


@tool
def get_item_price(item_name: str) -> str:
    """
    Get the unit price for an item from inventory.
    
    Args:
        item_name: Name of the item
        
    Returns:
        JSON string with item price
    """
    inventory_df = pd.read_sql("SELECT unit_price FROM inventory WHERE item_name = ?",
                               db_engine, params=(item_name,))
    
    if not inventory_df.empty:
        price = float(inventory_df["unit_price"].iloc[0])
        return json.dumps({"item_name": item_name, "unit_price": price})
    return json.dumps({"item_name": item_name, "unit_price": 0.0, "error": "Item not found"})


def generate_quote(items: List[Dict], date: str) -> Dict:
    """
    Generate a quote for multiple items with bulk discounts.
    
    This function uses helper functions DIRECTLY (not via tools).
    Tools are only for framework agents.
    
    Args:
        items: List of {item_name, quantity}
        date: Date for quote
        
    Returns:
        Dict with quote details
    """
    quote_items = []
    total_amount = 0.0
    unavailable_items = []
    
    for item in items:
        item_name = item["item_name"]
        quantity = item["quantity"]
        
        # Check availability using helper function DIRECTLY
        stock_info = get_stock_level(item_name, date)
        current_stock = int(stock_info["current_stock"].iloc[0]) if not stock_info.empty else 0
        available = current_stock >= quantity
        
        if not available:
            unavailable_items.append({
                "item_name": item_name,
                "requested": quantity,
                "available": current_stock,
                "shortfall": max(0, quantity - current_stock)
            })
            continue
        
        # Get price from database DIRECTLY
        inventory_df = pd.read_sql("SELECT unit_price FROM inventory WHERE item_name = ?",
                                   db_engine, params=(item_name,))
        
        if inventory_df.empty:
            continue
            
        unit_price = float(inventory_df["unit_price"].iloc[0])
        
        # Calculate bulk discount DIRECTLY
        total = quantity * unit_price
        
        if quantity >= 1001:
            discount = 0.15
        elif quantity >= 501:
            discount = 0.10
        elif quantity >= 100:
            discount = 0.05
        else:
            discount = 0.0
        
        discounted_total = total * (1 - discount)
        
        quote_items.append({
            "item_name": item_name,
            "quantity": quantity,
            "unit_price": unit_price,
            "line_total": discounted_total
        })
        
        total_amount += discounted_total
    
    return {
        "quote_items": quote_items,
        "total_amount": round(total_amount, 2),
        "unavailable_items": unavailable_items,
        "has_unavailable": len(unavailable_items) > 0
    }


# Tools for ordering agent

def place_order(items: List[Dict], date: str) -> Dict:
    """
    Place an order for items (creates sales transactions).
    
    This function uses helper functions DIRECTLY (not via tools).
    Tools are only for framework agents.
    
    Args:
        items: List of {item_name, quantity, price}
        date: Date for order
        
    Returns:
        Dict with order results
    """
    results = []
    total_revenue = 0.0
    
    for item in items:
        item_name = item["item_name"]
        quantity = item["quantity"]
        price = item["price"]
        
        # Check one more time if stock is available using helper DIRECTLY
        stock_info = get_stock_level(item_name, date)
        current_stock = int(stock_info["current_stock"].iloc[0]) if not stock_info.empty else 0
        available = current_stock >= quantity
        
        if available:
            # Create sales transaction
            transaction_id = create_transaction(
                item_name=item_name,
                transaction_type="sales",
                quantity=quantity,
                price=price,
                date=date
            )
            
            results.append({
                "item_name": item_name,
                "quantity": quantity,
                "price": price,
                "transaction_id": transaction_id,
                "success": True
            })
            
            total_revenue += price
        else:
            results.append({
                "item_name": item_name,
                "quantity": quantity,
                "price": 0,
                "success": False,
                "reason": f"Insufficient stock: {current_stock} available"
            })
    
    return {
        "order_results": results,
        "total_revenue": total_revenue,
        "success": all(r["success"] for r in results)
    }


def restock_item(item_name: str, quantity: int, date: str) -> Dict:
    """
    Restock an item (creates stock_orders transaction).
    
    This function uses helper functions DIRECTLY (not via tools).
    Tools are only for framework agents.
    
    Args:
        item_name: Name of item to restock
        quantity: Quantity to order
        date: Date of order
        
    Returns:
        Dict with restock result
    """
    # Get price from database DIRECTLY
    inventory_df = pd.read_sql("SELECT unit_price FROM inventory WHERE item_name = ?",
                               db_engine, params=(item_name,))
    
    if inventory_df.empty:
        return {
            "success": False,
            "reason": f"Item '{item_name}' not found in inventory"
        }
    
    unit_price = float(inventory_df["unit_price"].iloc[0])
    total_cost = quantity * unit_price
    
    # Check if we have enough cash
    cash_balance = get_cash_balance(date)
    
    if cash_balance < total_cost:
        return {
            "success": False,
            "reason": f"Insufficient funds. Need ${total_cost:.2f}, have ${cash_balance:.2f}"
        }
    
    # Estimate delivery date
    delivery_date = get_supplier_delivery_date(date, quantity)
    
    # Create stock order transaction
    transaction_id = create_transaction(
        item_name=item_name,
        transaction_type="stock_orders",
        quantity=quantity,
        price=total_cost,
        date=delivery_date
    )
    
    return {
        "success": True,
        "item_name": item_name,
        "quantity": quantity,
        "cost": total_cost,
        "delivery_date": delivery_date,
        "transaction_id": transaction_id
    }


# Set up your agents and create an orchestration agent that will manage them.

def parse_customer_request(request: str, date: str) -> Dict:
    """
    Use LLM to parse customer request and extract items with quantities.
    """
    system_prompt = """You are an expert at parsing customer orders for paper supplies.
Your task is to extract item names and quantities from customer requests.

Available items include (match closely to these names):
- A4 paper, Letter-sized paper, Cardstock, Colored paper, Glossy paper, Matte paper
- Recycled paper, Eco-friendly paper, Poster paper, Banner paper, Kraft paper
- Construction paper, Wrapping paper, Photo paper, Standard copy paper
- Paper plates, Paper cups, Paper napkins, Disposable cups, Table covers
- Envelopes, Sticky notes, Notepads, Invitation cards, Flyers
- Party streamers, Paper party bags, Name tags with lanyards, Presentation folders

Return ONLY a JSON array of objects with 'item_name' and 'quantity' fields.
Match item names as closely as possible to the available items list.
Example: [{"item_name": "A4 paper", "quantity": 200}, {"item_name": "Cardstock", "quantity": 100}]"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Parse this order request:\n{request}"}
            ],
            temperature=0.3
        )
        
        content = response.choices[0].message.content.strip()
        
        # Try to parse JSON from response
        import json
        import re
        
        # Extract JSON array from response
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            items = json.loads(json_match.group())
            return {"success": True, "items": items}
        else:
            return {"success": False, "error": "Could not parse items from request"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


#Framework agent initializations
inventory_agent = ToolCallingAgent(
    tools=[check_inventory_availability, get_inventory_list, check_restock_needed],
    model=model,
    max_steps=5
)

# Restocking Agent: Uses restocking-related tools (defined below)
@tool
def restock_item_tool(item_name: str, quantity: int, date: str) -> str:
    """
    Restock an item by creating a stock order transaction.
    
    Args:
        item_name: Name of the item to restock
        quantity: Quantity to order
        date: Date in YYYY-MM-DD format
        
    Returns:
        JSON string with restocking result
    """
    result = restock_item(item_name, quantity, date)
    return json.dumps(result)

@tool
def get_supplier_delivery_date_tool(date: str, quantity: int) -> str:
    """
    Get estimated supplier delivery date.
    
    Args:
        date: Order date in YYYY-MM-DD format
        quantity: Order quantity
        
    Returns:
        Delivery date string in YYYY-MM-DD format
    """
    return get_supplier_delivery_date(date, quantity)

@tool
def get_cash_balance_tool(date: str) -> str:
    """
    Get current cash balance as of a date.
    
    Args:
        date: Date in YYYY-MM-DD format
        
    Returns:
        JSON string with cash balance
    """
    balance = get_cash_balance(date)
    return json.dumps({"cash_balance": balance, "date": date})

# Restocking Agent: Uses restocking-related tools
# This is a ToolCallingAgent INSTANCE (Framework Agent)
restocking_agent = ToolCallingAgent(
    tools=[restock_item_tool, get_supplier_delivery_date_tool, get_cash_balance_tool],
    model=model,
    max_steps=5
)

# Quoting Agent: Uses pricing and quote tools
@tool
def generate_quote_tool(items_json: str, date: str) -> str:
    """
    Generate a quote for multiple items with bulk discounts.
    
    Args:
        items_json: JSON string of list of items [{"item_name": "...", "quantity": 123}, ...]
        date: Date in YYYY-MM-DD format
        
    Returns:
        JSON string with quote details
    """
    items = json.loads(items_json)
    result = generate_quote(items, date)
    return json.dumps(result)

@tool
def search_quote_history_tool(search_terms_json: str, limit: int = 5) -> str:
    """
    Search historical quotes for reference.
    
    Args:
        search_terms_json: JSON array of search terms
        limit: Maximum results to return
        
    Returns:
        JSON string with historical quotes
    """
    search_terms = json.loads(search_terms_json)
    results = search_quote_history(search_terms, limit)
    return json.dumps(results)

# Quoting Agent: Uses pricing and quote tools
# This is a ToolCallingAgent INSTANCE (Framework Agent)
quoting_agent = ToolCallingAgent(
    tools=[calculate_bulk_discount, get_item_price, generate_quote_tool, search_quote_history_tool],
    model=model,
    max_steps=5
)

# Ordering Agent: Uses order placement tools
@tool
def place_order_tool(items_json: str, date: str) -> str:
    """
    Place an order for items (creates sales transactions).
    
    Args:
        items_json: JSON string of list of items [{"item_name": "...", "quantity": 123, "price": 456.78}, ...]
        date: Date in YYYY-MM-DD format
        
    Returns:
        JSON string with order results
    """
    items = json.loads(items_json)
    result = place_order(items, date)
    return json.dumps(result)

@tool
def create_transaction_tool(item_name: str, transaction_type: str, quantity: int, price: float, date: str) -> str:
    """
    Create a transaction record.
    
    Args:
        item_name: Name of the item
        transaction_type: Either 'stock_orders' or 'sales'
        quantity: Number of units
        price: Total price
        date: Date in YYYY-MM-DD format
        
    Returns:
        Transaction ID as string
    """
    transaction_id = create_transaction(item_name, transaction_type, quantity, price, date)
    return str(transaction_id)

# Ordering Agent: Uses order placement tools
# This is a ToolCallingAgent INSTANCE (Framework Agent)
ordering_agent = ToolCallingAgent(
    tools=[place_order_tool, create_transaction_tool],
    model=model,
    max_steps=5
)


# ========================================================================================
# FRAMEWORK AGENT EXECUTION FUNCTIONS
# ========================================================================================
# These functions invoke the Framework Agents defined above
# They use agent.run() method from smolagents ToolCallingAgent
# The framework handles tool selection and execution based on the task
# ========================================================================================

# Helper function to run agents with proper error handling
def run_agent_with_task(agent, task: str) -> str:
    """
    Run a smolagents ToolCallingAgent with a task and return the result.
    
    This function invokes the framework agent using agent.run() method.
    The ToolCallingAgent uses its LLM to decide which tools to call based on the task.
    
    Args:
        agent: A ToolCallingAgent instance (Framework Agent)
        task: Natural language task description
        
    Returns:
        String result from agent execution
    """
    try:
        result = agent.run(task)  # FRAMEWORK METHOD: agent.run()
        return str(result)
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


def inventory_check_with_agent(items: List[Dict], date: str) -> Dict:
    """
    Use the inventory_agent (Framework ToolCallingAgent) to check availability.
    
    This function demonstrates Framework Agent usage:
    1. inventory_agent is a ToolCallingAgent INSTANCE (not a function)
    2. We call agent.run(task) - a FRAMEWORK METHOD
    3. The framework's LLM decides which tools to use
    4. The framework executes the selected tools
    5. Results are returned
    
    Args:
        items: List of items to check
        date: Date for inventory check
        
    Returns:
        Dict with availability results
    """
    items_str = "\n".join([f"- {item['item_name']}: {item['quantity']} units" for item in items])
    
    task = f"""Check inventory availability for these items as of {date}:
{items_str}

For each item:
1. Use check_inventory_availability to verify stock levels
2. Identify items that are unavailable or need restocking

Return a JSON summary with:
- availability_results: list of availability checks
- items_to_restock: list of items needing restock with shortfall amounts
- all_available: boolean"""

    result_str = run_agent_with_task(inventory_agent, task)  # FRAMEWORK AGENT EXECUTION
    
    # Parse the result
    try:
        # Try to extract JSON from result
        json_match = re.search(r'\{.*\}', result_str, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            # Fallback to manual checking if agent fails
            return inventory_agent_fallback(items, date)
    except:
        return inventory_agent_fallback(items, date)


def inventory_agent_fallback(items: List[Dict], date: str) -> Dict:
    """
    Fallback method if framework agent fails - uses helper functions DIRECTLY.
    
    This fallback does NOT use tool wrappers - it uses helper functions directly.
    """
    availability_results = []
    items_to_restock = []
    
    for item in items:
        item_name = item["item_name"]
        quantity = item["quantity"]
        
        # Use helper function DIRECTLY (not via tool)
        stock_info = get_stock_level(item_name, date)
        current_stock = int(stock_info["current_stock"].iloc[0]) if not stock_info.empty else 0
        available = current_stock >= quantity
        
        availability = {
            "item_name": item_name,
            "requested_quantity": quantity,
            "current_stock": current_stock,
            "available": available,
            "shortfall": max(0, quantity - current_stock)
        }
        
        availability_results.append(availability)
        
        if not available:
            items_to_restock.append({
                "item_name": item_name,
                "needed_quantity": quantity,
                "current_stock": current_stock,
                "shortfall": max(0, quantity - current_stock)
            })
    
    return {
        "availability_results": availability_results,
        "items_to_restock": items_to_restock,
        "all_available": len(items_to_restock) == 0
    }


def quoting_with_agent(items: List[Dict], date: str, customer_context: str) -> Dict:
    """
    Use the quoting agent (framework agent) to generate quotes.
    """
    items_json = json.dumps(items)
    
    task = f"""Generate a quote for a customer as of {date}.
    
Customer context: {customer_context}

Items requested: {items_json}

Tasks:
1. Use generate_quote_tool with items_json='{items_json}' and date='{date}'
2. Search historical quotes using search_quote_history_tool for similar orders
3. Return the complete quote with explanations

Return JSON with quote details including total_amount, quote_items, and historical_references."""

    result_str = run_agent_with_task(quoting_agent, task)
    
    # Parse result or fallback
    try:
        json_match = re.search(r'\{.*\}', result_str, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            # Ensure we have the explanation
            if "explanation" not in result:
                result["explanation"] = quoting_agent_fallback(items, date, customer_context).get("explanation", "")
            return result
        else:
            return quoting_agent_fallback(items, date, customer_context)
    except:
        return quoting_agent_fallback(items, date, customer_context)


def quoting_agent_fallback(items: List[Dict], date: str, customer_context: str) -> Dict:
    """
    Generate a quote with bulk discounts and search historical quotes for reference.
    """
    # Generate the quote
    quote = generate_quote(items, date)
    
    # Search historical quotes for similar requests
    search_terms = []
    for item in items:
        # Extract key terms from item names
        terms = item["item_name"].lower().split()
        search_terms.extend(terms)
    
    # Get relevant historical quotes
    historical_quotes = search_quote_history(search_terms[:3], limit=3) if search_terms else []
    
    # Use LLM to generate explanation
    system_prompt = """You are a friendly sales representative for Munder Difflin Paper Company.
Generate a professional quote explanation that:
1. Lists each item with quantity and pricing
2. Explains any bulk discounts applied
3. Provides the total amount
4. Is warm and customer-focused

Keep it concise and professional."""

    quote_details = ""
    for item in quote["quote_items"]:
        quote_details += f"- {item['item_name']}: {item['quantity']} units @ ${item['unit_price']:.2f} each = ${item['line_total']:.2f}\n"
    
    historical_context = ""
    if historical_quotes:
        historical_context = "\n\nSimilar past quotes:\n"
        for hq in historical_quotes:
            historical_context += f"- {hq.get('event_type', 'event')}: ${hq.get('total_amount', 0)}\n"
    
    prompt = f"""Customer context: {customer_context}

Quote details:
{quote_details}
Total: ${quote['total_amount']:.2f}
{historical_context}

Generate a professional quote explanation."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        explanation = response.choices[0].message.content.strip()
        
        return {
            **quote,
            "explanation": explanation,
            "historical_references": len(historical_quotes)
        }
    except Exception as e:
        return {
            **quote,
            "explanation": f"Quote total: ${quote['total_amount']:.2f}. Error generating detailed explanation: {str(e)}",
            "historical_references": 0
        }


def ordering_with_agent(quote: Dict, date: str) -> Dict:
    """
    Use the ordering agent (framework agent) to process orders.
    """
    if quote.get("has_unavailable", False):
        return {
            "success": False,
            "message": "Cannot process order: some items are unavailable",
            "unavailable_items": quote["unavailable_items"]
        }
    
    # Prepare order items for JSON
    order_items = []
    for item in quote["quote_items"]:
        order_items.append({
            "item_name": item["item_name"],
            "quantity": item["quantity"],
            "price": item["line_total"]
        })
    
    items_json = json.dumps(order_items)
    
    task = f"""Place an order for the following items on {date}:

{items_json}

Use place_order_tool with items_json='{items_json}' and date='{date}'.

Return JSON with order results including success status and total_revenue."""

    result_str = run_agent_with_task(ordering_agent, task)
    
    # Parse result or fallback
    try:
        json_match = re.search(r'\{.*\}', result_str, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return ordering_agent_fallback(quote, date)
    except:
        return ordering_agent_fallback(quote, date)


def ordering_agent_fallback(quote: Dict, date: str) -> Dict:
    """
    Fallback method for ordering when framework agent fails.
    """
    if quote.get("has_unavailable", False):
        return {
            "success": False,
            "message": "Cannot process order: some items are unavailable",
            "unavailable_items": quote["unavailable_items"]
        }
    
    # Prepare order items
    order_items = []
    for item in quote["quote_items"]:
        order_items.append({
            "item_name": item["item_name"],
            "quantity": item["quantity"],
            "price": item["line_total"]
        })
    
    # Place the order
    order_result = place_order(order_items, date)
    
    return order_result


def restocking_with_agent(items_to_restock: List[Dict], date: str) -> Dict:
    """
    Use the restocking agent (framework agent) to restock items.
    """
    items_str = "\n".join([f"- {item['item_name']}: need {item['shortfall']} units (current: {item['current_stock']})" 
                           for item in items_to_restock])
    
    task = f"""Restock the following items as of {date}:

{items_str}

For each item:
1. Use get_cash_balance_tool to check available funds
2. Use restock_item_tool to place restock orders (add 200 buffer units to shortfall)
3. Use get_supplier_delivery_date_tool to estimate delivery

Return JSON with:
- restock_results: list of restock operations
- total_cost: sum of all costs
- success: boolean"""

    result_str = run_agent_with_task(restocking_agent, task)
    
    # Parse result or fallback
    try:
        json_match = re.search(r'\{.*\}', result_str, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return restocking_agent_fallback(items_to_restock, date)
    except:
        return restocking_agent_fallback(items_to_restock, date)


def restocking_agent_fallback(items_to_restock: List[Dict], date: str) -> Dict:
    """
    Restock items that are low or out of stock.
    """
    restock_results = []
    total_cost = 0.0
    
    for item in items_to_restock:
        item_name = item["item_name"]
        # Order enough to fulfill request plus buffer
        restock_quantity = item["shortfall"] + 200  # Add buffer stock
        
        result = restock_item(item_name, restock_quantity, date)
        restock_results.append(result)
        
        if result["success"]:
            total_cost += result["cost"]
    
    return {
        "restock_results": restock_results,
        "total_cost": total_cost,
        "success": all(r["success"] for r in restock_results)
    }


def orchestrator_agent(customer_request: str, date: str) -> str:
    """
    Main orchestrator that coordinates all agents to handle customer requests.
    
    This orchestrator uses framework-based agents (ToolCallingAgent from smolagents) to:
    1. Parse the customer request to extract items and quantities
    2. Check inventory availability using inventory_agent with its tools
    3. If items unavailable, attempt restocking using restocking_agent with its tools
    4. Generate quote with bulk discounts using quoting_agent with its tools
    5. Process order using ordering_agent with its tools
    6. Return comprehensive response
    """
    
    # Step 1: Parse customer request
    parsed_request = parse_customer_request(customer_request, date)
    
    if not parsed_request["success"]:
        return f"Error: Unable to parse your request. {parsed_request.get('error', '')}"
    
    items = parsed_request["items"]
    
    if not items:
        return "Error: No items found in your request. Please specify the items and quantities you need."
    
    # Step 2: Check inventory using framework agent
    inventory_check = inventory_check_with_agent(items, date)
    
    # Step 3: Handle restocking if needed using framework agent
    restocking_message = ""
    if not inventory_check["all_available"]:
        restock_result = restocking_with_agent(inventory_check["items_to_restock"], date)
        
        if restock_result["success"]:
            restocking_message = f"\nNote: We've placed restock orders for items that were low in inventory (Cost: ${restock_result['total_cost']:.2f})."
            # Recheck inventory after restocking (with new delivery dates)
            # For now, inform customer of delay
            delivery_dates = [r.get("delivery_date", date) for r in restock_result["restock_results"] if r.get("success")]
            if delivery_dates:
                latest_delivery = max(delivery_dates)
                restocking_message += f" New items will arrive by {latest_delivery}."
        else:
            return f"Unfortunately, some items are out of stock and we cannot fulfill your complete order at this time:\n{inventory_check['items_to_restock']}"
    
    # Step 4: Generate quote using framework agent
    quote = quoting_with_agent(items, date, customer_request)
    
    if quote.get("has_unavailable", False):
        unavailable_list = "\n".join([f"- {item['item_name']}: need {item['requested']}, have {item['available']}" 
                                      for item in quote["unavailable_items"]])
        return f"Quote cannot be completed. The following items are unavailable:\n{unavailable_list}{restocking_message}"
    
    # Step 5: Process order using framework agent
    order_result = ordering_with_agent(quote, date)
    
    if not order_result["success"]:
        return f"Error processing order: {order_result.get('message', 'Unknown error')}"
    
    # Step 6: Generate response
    response = f"""Thank you for your order!

{quote['explanation']}

ORDER SUMMARY:
"""
    for item in quote["quote_items"]:
        response += f"✓ {item['item_name']}: {item['quantity']} units @ ${item['unit_price']:.2f} each = ${item['line_total']:.2f}\n"
    
    response += f"\nTOTAL: ${quote['total_amount']:.2f}"
    response += f"\nOrder processed successfully! Transaction revenue: ${order_result['total_revenue']:.2f}"
    response += restocking_message
    
    return response


# Run your test scenarios by writing them here. Make sure to keep track of them.

def run_test_scenarios():
    
    print("Initializing Database...")
    init_database(db_engine)
    try:
        quote_requests_sample = pd.read_csv("quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"], format="%m/%d/%y", errors="coerce"
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample = quote_requests_sample.sort_values("request_date")
    except Exception as e:
        print(f"FATAL: Error loading test data: {e}")
        return

    quote_requests_sample = pd.read_csv("quote_requests_sample.csv")

    # Sort by date
    quote_requests_sample["request_date"] = pd.to_datetime(
        quote_requests_sample["request_date"], format="mixed", dayfirst=False
    )
    quote_requests_sample = quote_requests_sample.sort_values("request_date")

    # Get initial state
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    report = generate_financial_report(initial_date)
    current_cash = report["cash_balance"]
    current_inventory = report["inventory_value"]

    ############
    ############
    ############
    # INITIALIZE YOUR MULTI AGENT SYSTEM HERE
    ############
    ############
    ############

    results = []
    for idx, row in quote_requests_sample.iterrows():
        request_date = row["request_date"].strftime("%Y-%m-%d")

        print(f"\n=== Request {idx+1} ===")
        print(f"Context: {row['job']} organizing {row['event']}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance: ${current_cash:.2f}")
        print(f"Inventory Value: ${current_inventory:.2f}")

        # Process request
        request_with_date = f"{row['request']} (Date of request: {request_date})"

        ############
        ############
        ############
        # USE YOUR MULTI AGENT SYSTEM TO HANDLE THE REQUEST
        ############
        ############
        ############

        # Call the orchestrator agent to handle the request
        response = orchestrator_agent(request_with_date, request_date)

        # Update state
        report = generate_financial_report(request_date)
        current_cash = report["cash_balance"]
        current_inventory = report["inventory_value"]

        print(f"Response: {response}")
        print(f"Updated Cash: ${current_cash:.2f}")
        print(f"Updated Inventory: ${current_inventory:.2f}")

        results.append(
            {
                "request_id": idx + 1,
                "request_date": request_date,
                "cash_balance": current_cash,
                "inventory_value": current_inventory,
                "response": response,
            }
        )

        time.sleep(1)

    # Final report
    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("\n===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")

    # Save results
    pd.DataFrame(results).to_csv("test_results.csv", index=False)
    return results


if __name__ == "__main__":
    results = run_test_scenarios()