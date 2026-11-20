import os
import re
import json
import random
import urllib.request
from datetime import datetime
from urllib.parse import quote
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import pandas as pd
import plotly.graph_objects as go

from data import (
    ADMIN_CREDENTIALS,
    FIREBASE_DB_URL,
    REAL_SHOE_FALLBACK_URL,
    BRANDS,
    CATEGORIES,
    PRODUCTS,
    INITIAL_DEMO_ORDERS
)

app = Flask(__name__)
app.secret_key = "solemetrics_pure_python_key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE = os.path.join(BASE_DIR, "orders.xlsx")
CSV_BACKUP_FILE = os.path.join(BASE_DIR, "orders_backup.csv")
CUSTOMERS_FILE = os.path.join(BASE_DIR, "customers.json")

AGE_GROUPS = ["Under 18", "18-25", "26-40", "41-55", "55+"]
GENDERS = ["Male", "Female", "Other"]
UK_SIZES = ["UK 6", "UK 7", "UK 8", "UK 9", "UK 10", "UK 11"]
COST_PRICE_MAP = {p["id"]: int(p.get("cost_price", int(p["price"] * 0.6))) for p in PRODUCTS}


# =========================================================================
# 1. FIREBASE CLOUD SYNC HELPERS
# =========================================================================
def firebase_enabled() -> bool:
    return bool(FIREBASE_DB_URL) and "YAHAN_APNA_FIREBASE" not in FIREBASE_DB_URL


def firebase_safe_key(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", text.strip().lower())


def firebase_request(path: str, method: str = "GET", payload=None):
    if not firebase_enabled():
        return None
    base = FIREBASE_DB_URL.rstrip("/")
    url = f"{base}/{path}.json"
    data_bytes = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    try:
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8")
            parsed = json.loads(raw) if raw else None
            if isinstance(parsed, dict) and "error" in parsed:
                return None
            return parsed
    except Exception as e:
        print(f"Firebase ({method} {path}) skipped:", e)
        return None


# =========================================================================
# 2. CUSTOMER ACCOUNT STORAGE (WITH GENDER & AGE GROUP)
# =========================================================================
def load_local_customers() -> list:
    if not os.path.exists(CUSTOMERS_FILE):
        return []
    try:
        with open(CUSTOMERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def write_local_customers(customers: list):
    with open(CUSTOMERS_FILE, "w", encoding="utf-8") as f:
        json.dump(customers, f, indent=2)


def load_customers() -> list:
    merged = {}
    for c in load_local_customers():
        if isinstance(c, dict) and c.get("email"):
            em = str(c["email"]).strip().lower()
            merged[em] = {
                "name": str(c.get("name", "")).strip(),
                "email": em,
                "phone": str(c.get("phone", "")).strip(),
                "city": str(c.get("city", "")).strip(),
                "gender": str(c.get("gender", "Male")).strip(),
                "ageGroup": str(c.get("ageGroup", "18-25")).strip(),
                "password": str(c.get("password", ""))
            }

    if firebase_enabled():
        cloud_cust = firebase_request("customers", "GET")
        if cloud_cust:
            rows = list(cloud_cust.values()) if isinstance(cloud_cust, dict) else [x for x in cloud_cust if x]
            for c in rows:
                if isinstance(c, dict) and c.get("email"):
                    em = str(c["email"]).strip().lower()
                    merged[em] = {
                        "name": str(c.get("name", "")).strip(),
                        "email": em,
                        "phone": str(c.get("phone", "")).strip(),
                        "city": str(c.get("city", "")).strip(),
                        "gender": str(c.get("gender", "Male")).strip(),
                        "ageGroup": str(c.get("ageGroup", "18-25")).strip(),
                        "password": str(c.get("password", ""))
                    }

    result = list(merged.values())
    write_local_customers(result)
    return result


def save_new_customer(customer: dict, all_customers: list):
    write_local_customers(all_customers)
    if firebase_enabled():
        key = firebase_safe_key(customer["email"])
        firebase_request(f"customers/{key}", "PUT", customer)
    write_local_excel_files(load_orders_df(), all_customers)


# =========================================================================
# 3. PANDAS EXCEL + PROFIT MARGIN ANALYTICS ENGINE
# =========================================================================
def clean_orders_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=list(INITIAL_DEMO_ORDERS[0].keys()))

    df = df.fillna("")
    df["customerPhone"] = df["customerPhone"].astype(str)

    if "gender" not in df.columns:
        df["gender"] = "Male"
    df["gender"] = df["gender"].replace("", "Male")

    if "ageGroup" not in df.columns:
        df["ageGroup"] = "18-25"
    df["ageGroup"] = df["ageGroup"].replace("", "18-25")

    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(1).astype(int)
    df["unitPrice"] = pd.to_numeric(df["unitPrice"], errors="coerce").fillna(0).astype(int)
    df["totalAmount"] = pd.to_numeric(df["totalAmount"], errors="coerce").fillna(0).astype(int)

    if "costPrice" not in df.columns:
        df["costPrice"] = df["productId"].map(COST_PRICE_MAP).fillna((df["unitPrice"] * 0.6).astype(int))
    else:
        df["costPrice"] = pd.to_numeric(df["costPrice"], errors="coerce").fillna(0).astype(int)
        zero_mask = df["costPrice"] == 0
        df.loc[zero_mask, "costPrice"] = df.loc[zero_mask, "productId"].map(COST_PRICE_MAP).fillna((df.loc[zero_mask, "unitPrice"] * 0.6).astype(int))

    df["profit"] = df["totalAmount"] - (df["costPrice"] * df["qty"])
    return df


def write_local_excel_files(df: pd.DataFrame, customers_list: list = None):
    """5 Sheets ke saath orders.xlsx aur orders_backup.csv save karta hai"""
    df.to_csv(CSV_BACKUP_FILE, index=False)

    if not df.empty:
        brand_summary = df.groupby("brand", as_index=False).agg(
            Total_Orders=("orderId", "count"),
            Units_Sold=("qty", "sum"),
            Revenue_INR=("totalAmount", "sum"),
            Gross_Profit_INR=("profit", "sum")
        )
        brand_summary["Profit_Margin_%"] = (
            (brand_summary["Gross_Profit_INR"] / brand_summary["Revenue_INR"].replace(0, 1)) * 100
        ).round(2)

        cat_summary = df.groupby("category", as_index=False).agg(
            Total_Orders=("orderId", "count"),
            Units_Sold=("qty", "sum"),
            Revenue_INR=("totalAmount", "sum"),
            Gross_Profit_INR=("profit", "sum")
        )
        cat_summary["Profit_Margin_%"] = (
            (cat_summary["Gross_Profit_INR"] / cat_summary["Revenue_INR"].replace(0, 1)) * 100
        ).round(2)

        city_demo = df.groupby(["city", "ageGroup", "gender"], as_index=False).agg(
            Orders=("orderId", "count"),
            Units_Sold=("qty", "sum"),
            Revenue_INR=("totalAmount", "sum"),
            Gross_Profit_INR=("profit", "sum")
        )
    else:
        brand_summary = pd.DataFrame(columns=["brand", "Total_Orders", "Units_Sold", "Revenue_INR", "Gross_Profit_INR", "Profit_Margin_%"])
        cat_summary = pd.DataFrame(columns=["category", "Total_Orders", "Units_Sold", "Revenue_INR", "Gross_Profit_INR", "Profit_Margin_%"])
        city_demo = pd.DataFrame(columns=["city", "ageGroup", "gender", "Orders", "Units_Sold", "Revenue_INR", "Gross_Profit_INR"])

    cust_data = customers_list if customers_list is not None else load_local_customers()
    if cust_data:
        cust_df = pd.DataFrame(cust_data)
        for col in ["name", "email", "phone", "city", "gender", "ageGroup"]:
            if col not in cust_df.columns:
                cust_df[col] = ""
        cust_df = cust_df[["name", "email", "phone", "city", "gender", "ageGroup"]]
    else:
        cust_df = pd.DataFrame(columns=["name", "email", "phone", "city", "gender", "ageGroup"])

    try:
        with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="All_Orders", index=False)
            brand_summary.to_excel(writer, sheet_name="Brand_Profit_Summary", index=False)
            cat_summary.to_excel(writer, sheet_name="Category_Profit_Summary", index=False)
            city_demo.to_excel(writer, sheet_name="City_And_Demographics", index=False)
            cust_df.to_excel(writer, sheet_name="Registered_Customers", index=False)
    except PermissionError:
        print("Note: Close orders.xlsx in MS Excel so live changes write directly.")


def load_orders_df() -> pd.DataFrame:
    if firebase_enabled():
        cloud_data = firebase_request("orders", "GET")
        if cloud_data is None:
            if os.path.exists(EXCEL_FILE):
                df = clean_orders_df(pd.read_excel(EXCEL_FILE, sheet_name="All_Orders", dtype={"customerPhone": str}))
            else:
                df = clean_orders_df(pd.DataFrame(INITIAL_DEMO_ORDERS))
            orders_dict = {row["orderId"]: row for row in df.to_dict(orient="records")}
            firebase_request("orders", "PUT", orders_dict)
            write_local_excel_files(df)
            return df
        rows = list(cloud_data.values()) if isinstance(cloud_data, dict) else [r for r in cloud_data if r]
        df = clean_orders_df(pd.DataFrame(rows))
        write_local_excel_files(df)
        return df

    if not os.path.exists(EXCEL_FILE):
        if os.path.exists(CSV_BACKUP_FILE):
            df = clean_orders_df(pd.read_csv(CSV_BACKUP_FILE, dtype=str))
        else:
            df = clean_orders_df(pd.DataFrame(INITIAL_DEMO_ORDERS))
        write_local_excel_files(df)
        return df

    df = pd.read_excel(EXCEL_FILE, sheet_name="All_Orders", dtype={"customerPhone": str})
    return clean_orders_df(df)


# =========================================================================
# 4. PYTHON PLOTLY ANIMATED MULTI-CHART GENERATOR
# =========================================================================
def build_animated_chart_html(df: pd.DataFrame, mode: str, chart_type: str, metric: str) -> str:
    if metric == "revenue":
        col = "totalAmount"
        y_label = "Revenue (₹)"
    elif metric == "profit":
        col = "profit"
        y_label = "Gross Profit (₹)"
    else:
        col = "qty"
        y_label = "Units Sold (Pairs)"

    is_currency = metric in ("revenue", "profit")
    labels, values, title = [], [], ""

    if mode == "category":
        agg = df.groupby("category")[col].sum().to_dict() if not df.empty else {}
        labels = [c["name"] for c in CATEGORIES]
        values = [int(agg.get(c["name"], 0)) for c in CATEGORIES]
        title = f"{y_label} by Footwear Category"
    elif mode == "brand":
        agg = df.groupby("brand")[col].sum().to_dict() if not df.empty else {}
        labels = BRANDS
        values = [int(agg.get(b, 0)) for b in BRANDS]
        title = f"{y_label} by Brand"
    elif mode == "city":
        s = df.groupby("city")[col].sum().sort_values(ascending=False) if not df.empty else pd.Series(dtype=int)
        labels = list(s.index)
        values = [int(v) for v in s.values]
        title = f"City-Wise Demand — {y_label}"
    elif mode == "size":
        agg = df.groupby("size")[col].sum().to_dict() if not df.empty else {}
        labels = UK_SIZES
        values = [int(agg.get(sz, 0)) for sz in UK_SIZES]
        title = f"UK Size Distribution — {y_label}"
    elif mode == "age":
        agg = df.groupby("ageGroup")[col].sum().to_dict() if not df.empty else {}
        labels = AGE_GROUPS
        values = [int(agg.get(ag, 0)) for ag in AGE_GROUPS]
        title = f"Customer Age Group Segmentation — {y_label}"
    elif mode == "gender":
        agg = df.groupby("gender")[col].sum().to_dict() if not df.empty else {}
        labels = GENDERS
        values = [int(agg.get(g, 0)) for g in GENDERS]
        title = f"Customer Gender Segmentation — {y_label}"
    elif mode == "model":
        s = (
            df.groupby("productName")[col].sum().sort_values(ascending=False).head(10)
            if not df.empty else pd.Series(dtype=int)
        )
        labels = list(s.index)
        values = [int(v) for v in s.values]
        title = f"Top 10 Shoe Models — {y_label}"
    elif mode == "payment":
        s = df.groupby("paymentMethod")[col].sum() if not df.empty else pd.Series(dtype=int)
        labels = list(s.index)
        values = [int(v) for v in s.values]
        title = f"Payment Mode Breakdown — {y_label}"
    elif mode == "timeline":
        s = df.groupby("date")[col].sum().sort_index() if not df.empty else pd.Series(dtype=int)
        labels = list(s.index)
        running = 0
        for v in s.values:
            running += int(v)
            values.append(running)
        title = f"Cumulative {y_label} Growth Timeline"

    palette = [
        "#4f46e5", "#0ea5e9", "#10b981", "#f59e0b", "#8b5cf6",
        "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#0f172a"
    ]
    text_labels = [f"₹{v:,}" if is_currency else str(v) for v in values]

    if chart_type == "bar":
        bar_colors = [palette[i % len(palette)] for i in range(len(labels))]
        trace = go.Bar(
            x=labels,
            y=values,
            text=text_labels,
            textposition="outside",
            marker=dict(color=bar_colors),
            hovertemplate="<b>%{x}</b><br>" + y_label + ": %{y:,}<extra></extra>"
        )
    elif chart_type == "area":
        trace = go.Scatter(
            x=labels,
            y=values,
            mode="lines+markers+text",
            text=text_labels,
            textposition="top center",
            fill="tozeroy",
            fillcolor="rgba(79, 70, 229, 0.16)",
            line=dict(color="#4f46e5", width=3.5, shape="spline"),
            marker=dict(size=9, color="#0f172a", line=dict(width=2, color="#ffffff")),
            hovertemplate="<b>%{x}</b><br>" + y_label + ": %{y:,}<extra></extra>"
        )
    elif chart_type == "pie":
        trace = go.Pie(
            labels=labels,
            values=values,
            hole=0.46,
            marker=dict(colors=palette, line=dict(color="#ffffff", width=2)),
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>" + y_label + ": %{value:,} (%{percent})<extra></extra>"
        )
    else:
        trace = go.Scatter(
            x=labels,
            y=values,
            mode="lines+markers+text",
            text=text_labels,
            textposition="top center",
            line=dict(color="#4f46e5", width=3.5, shape="spline"),
            marker=dict(size=10, color="#0f172a", line=dict(width=2.5, color="#ffffff")),
            hovertemplate="<b>%{x}</b><br>" + y_label + ": %{y:,}<extra></extra>"
        )

    fig = go.Figure(data=[trace])
    max_val = max(values) if values else 10

    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=16, color="#0f172a", family="Inter, sans-serif")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,250,252,0.7)",
        font=dict(family="Inter, sans-serif", size=12, color="#334155"),
        height=400,
        margin=dict(l=40, r=25, t=55, b=65),
        hoverlabel=dict(bgcolor="#0f172a", font_size=12, font_color="#ffffff"),
        transition=dict(duration=650, easing="cubic-in-out")
    )

    if chart_type != "pie":
        fig.update_xaxes(showgrid=False, tickangle=-18)
        fig.update_yaxes(
            title_text=y_label,
            gridcolor="#e2e8f0",
            zeroline=True,
            zerolinecolor="#cbd5e1",
            range=[0, max_val * 1.24 if max_val > 0 else 10]
        )

    return fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
        config={"displayModeBar": True, "displaylogo": False}
    )


# =========================================================================
# 5. GLOBAL TEMPLATE HELPERS
# =========================================================================
@app.context_processor
def inject_globals():
    return {
        "current_user": session.get("user"),
        "fallback_img": REAL_SHOE_FALLBACK_URL
    }


@app.template_filter("inr")
def format_inr(value):
    return f"₹{int(value or 0):,}"


# =========================================================================
# 6. STOREFRONT, AUTH & ORDER ROUTES
# =========================================================================
@app.route("/")
def home():
    brand_counts = {b: sum(1 for p in PRODUCTS if p["brand"] == b) for b in BRANDS}
    featured_ids = ["NK-01", "AD-01", "CR-01", "SK-01", "SK-02", "BT-01", "WD-01", "SP-01"]
    featured = [p for p in PRODUCTS if p["id"] in featured_ids]
    return render_template(
        "home.html",
        active_page="home",
        brands=BRANDS,
        brand_counts=brand_counts,
        categories=CATEGORIES,
        featured=featured
    )


@app.route("/shop")
def shop():
    selected_brand = request.args.get("brand", "All")
    selected_category = request.args.get("category", "All")
    query = request.args.get("q", "").strip().lower()

    filtered = [
        p for p in PRODUCTS
        if (selected_brand == "All" or p["brand"] == selected_brand)
        and (selected_category == "All" or p["category"] == selected_category)
        and (
            not query
            or query in p["name"].lower()
            or query in p["brand"].lower()
            or query in p["category"].lower()
            or query in p["desc"].lower()
        )
    ]

    return render_template(
        "shop.html",
        active_page="shop",
        brands=BRANDS,
        categories=CATEGORIES,
        products=filtered,
        selected_brand=selected_brand,
        selected_category=selected_category,
        query=request.args.get("q", "")
    )


@app.route("/login")
def login_page():
    tab = request.args.get("tab", "customer-login")
    next_url = request.args.get("next", "")
    return render_template("login.html", active_page="login", tab=tab, next_url=next_url)


@app.route("/customer-login", methods=["POST"])
def customer_login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()
    next_url = request.form.get("next_url", "").strip()

    customers = load_customers()
    account = next((c for c in customers if c["email"].strip().lower() == email), None)

    if not account:
        flash("No account found with this email. Please create an account first.", "error")
        return redirect(url_for("login_page", tab="customer-signup", next=next_url))

    if str(account.get("password", "")).strip() != password:
        flash("Incorrect password. Please try again.", "error")
        return redirect(url_for("login_page", tab="customer-login", next=next_url))

    session["user"] = {
        "role": "customer",
        "name": account["name"],
        "email": account["email"],
        "phone": str(account.get("phone", "")),
        "city": account.get("city", ""),
        "gender": account.get("gender", "Male"),
        "ageGroup": account.get("ageGroup", "18-25")
    }
    flash(f"Welcome back, {account['name']}!", "success")
    return redirect(next_url or url_for("shop"))


@app.route("/customer-signup", methods=["POST"])
def customer_signup():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()
    city = request.form.get("city", "").strip()
    gender = request.form.get("gender", "Male").strip()
    age_group = request.form.get("age_group", "18-25").strip()
    password = request.form.get("password", "").strip()
    next_url = request.form.get("next_url", "").strip()

    customers = load_customers()
    if any(c["email"].strip().lower() == email for c in customers):
        flash("This email is already registered. Please sign in with your password.", "error")
        return redirect(url_for("login_page", tab="customer-login", next=next_url))

    new_cust = {
        "name": name,
        "email": email,
        "phone": phone,
        "city": city,
        "gender": gender,
        "ageGroup": age_group,
        "password": password
    }
    customers.append(new_cust)
    save_new_customer(new_cust, customers)

    session["user"] = {
        "role": "customer",
        "name": name,
        "email": email,
        "phone": phone,
        "city": city,
        "gender": gender,
        "ageGroup": age_group
    }
    flash(f"Account created! Welcome, {name}.", "success")
    return redirect(next_url or url_for("shop"))


@app.route("/admin-login", methods=["POST"])
def admin_login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if username == ADMIN_CREDENTIALS["username"] and password == ADMIN_CREDENTIALS["password"]:
        session["user"] = {"role": "admin", "name": "Administrator"}
        flash("Admin signed in successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    flash("Invalid admin username or password.", "error")
    return redirect(url_for("login_page", tab="admin-login"))


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out successfully.", "info")
    return redirect(url_for("home"))


@app.route("/checkout/<product_id>")
def checkout(product_id):
    user = session.get("user")
    if not user or user.get("role") != "customer":
        flash("Please login or create an account before placing an order.", "error")
        return redirect(url_for("login_page", tab="customer-login", next=url_for("checkout", product_id=product_id)))

    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        flash("Footwear model not found.", "error")
        return redirect(url_for("shop"))

    return render_template("checkout.html", active_page="shop", product=product)


@app.route("/place-order", methods=["POST"])
def place_order():
    user = session.get("user")
    if not user or user.get("role") != "customer":
        flash("Please sign in first.", "error")
        return redirect(url_for("login_page"))

    product_id = request.form.get("product_id")
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        return redirect(url_for("shop"))

    size = request.form.get("size", "UK 8")
    qty = max(1, int(request.form.get("qty", 1)))
    city = request.form.get("city", "").strip() or user.get("city", "India")
    payment_method = request.form.get("payment_method", "UPI")

    unit_price = int(product["price"])
    cost_price = int(product.get("cost_price", int(unit_price * 0.6)))
    total_amount = unit_price * qty
    profit = total_amount - (cost_price * qty)
    order_id = f"ORD-{random.randint(1000, 9999)}"

    new_order = {
        "orderId": order_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "customerName": user["name"],
        "customerEmail": user["email"],
        "customerPhone": user.get("phone", ""),
        "gender": user.get("gender", "Male"),
        "ageGroup": user.get("ageGroup", "18-25"),
        "city": city,
        "brand": product["brand"],
        "productId": product["id"],
        "productName": product["name"],
        "category": product["category"],
        "size": size,
        "qty": qty,
        "unitPrice": unit_price,
        "costPrice": cost_price,
        "totalAmount": total_amount,
        "profit": profit,
        "paymentMethod": payment_method,
        "status": "Confirmed"
    }

    df = load_orders_df()
    df = pd.concat([pd.DataFrame([new_order]), df], ignore_index=True)
    write_local_excel_files(df)
    firebase_request(f"orders/{order_id}", "PUT", new_order)

    flash("Order confirmed and saved to orders.xlsx!", "success")
    return redirect(url_for("receipt", order_id=order_id))


@app.route("/receipt/<order_id>")
def receipt(order_id):
    df = load_orders_df()
    match = df[df["orderId"] == order_id]
    if match.empty:
        flash("Receipt not found.", "error")
        return redirect(url_for("home"))

    order = match.iloc[0].to_dict()
    prod = next((p for p in PRODUCTS if p["id"] == order["productId"]), None)
    product_image = prod["image"] if prod else REAL_SHOE_FALLBACK_URL

    subject = quote(f"SoleMetrics Order Receipt #{order['orderId']} - {order['productName']}")
    body = quote(
        f"Hi {order['customerName']},\n\nThank you for shopping at SoleMetrics!\n\n"
        f"Order ID: {order['orderId']}\nDate: {order['date']}\nBrand: {order['brand']}\n"
        f"Footwear: {order['productName']} ({order['category']})\n"
        f"Size: {order['size']} | Qty: {order['qty']}\n"
        f"Total Paid: ₹{order['totalAmount']:,} ({order['paymentMethod']})\n"
        f"Delivery City: {order['city']}\n\nRegards,\nSoleMetrics Footwear Store"
    )
    mailto_link = f"mailto:{order['customerEmail']}?subject={subject}&body={body}"

    return render_template(
        "receipt.html",
        active_page="my-orders",
        order=order,
        product_image=product_image,
        mailto_link=mailto_link
    )


@app.route("/my-orders")
def my_orders():
    user = session.get("user")
    if not user or user.get("role") != "customer":
        flash("Please login to view your orders.", "error")
        return redirect(url_for("login_page", tab="customer-login", next=url_for("my_orders")))

    df = load_orders_df()
    my_df = df[df["customerEmail"].str.lower() == user["email"].lower()]
    orders = my_df.to_dict(orient="records")
    img_map = {p["id"]: p["image"] for p in PRODUCTS}

    return render_template("my_orders.html", active_page="my-orders", orders=orders, img_map=img_map)


# =========================================================================
# 7. PRIVATE ADMIN ANALYTICS ROUTES
# =========================================================================
@app.route("/admin")
def admin_dashboard():
    user = session.get("user")
    if not user or user.get("role") != "admin":
        flash("Authorized Admin login required.", "error")
        return redirect(url_for("login_page", tab="admin-login"))

    df = load_orders_df()

    chart_mode = request.args.get("chart", "category")
    chart_type = request.args.get("type", "bar")
    metric = request.args.get("metric", "units")
    filter_brand = request.args.get("brand", "All")
    filter_cat = request.args.get("category", "All")
    search_q = request.args.get("q", "").strip().lower()

    total_revenue = int(df["totalAmount"].sum()) if not df.empty else 0
    total_profit = int(df["profit"].sum()) if not df.empty else 0
    margin_pct = round((total_profit / total_revenue) * 100, 1) if total_revenue > 0 else 0.0
    total_orders = int(len(df))
    total_units = int(df["qty"].sum()) if not df.empty else 0
    top_brand = df.groupby("brand")["qty"].sum().idxmax() if not df.empty else "N/A"
    top_city = df.groupby("city")["qty"].sum().idxmax() if not df.empty else "N/A"

    kpis = [
        {"label": "Total Revenue", "value": f"₹{total_revenue:,}", "sub": "Gross top-line sales"},
        {"label": "Gross Profit", "value": f"₹{total_profit:,}", "sub": f"{margin_pct}% Net Margin"},
        {"label": "Total Orders", "value": total_orders, "sub": "Confirmed orders"},
        {"label": "Pairs Sold", "value": total_units, "sub": "Total units shipped"},
        {"label": "Top Brand", "value": top_brand, "sub": "Highest unit demand"},
        {"label": "Top City", "value": top_city, "sub": "Highest city demand"}
    ]

    chart_html = build_animated_chart_html(df, chart_mode, chart_type, metric)

    filtered_df = df.copy()
    if filter_brand != "All" and not filtered_df.empty:
        filtered_df = filtered_df[filtered_df["brand"] == filter_brand]
    if filter_cat != "All" and not filtered_df.empty:
        filtered_df = filtered_df[filtered_df["category"] == filter_cat]
    if search_q and not filtered_df.empty:
        mask = (
            filtered_df["orderId"].str.lower().str.contains(search_q)
            | filtered_df["customerName"].str.lower().str.contains(search_q)
            | filtered_df["customerEmail"].str.lower().str.contains(search_q)
            | filtered_df["productName"].str.lower().str.contains(search_q)
            | filtered_df["city"].str.lower().str.contains(search_q)
            | filtered_df["ageGroup"].str.lower().str.contains(search_q)
            | filtered_df["gender"].str.lower().str.contains(search_q)
        )
        filtered_df = filtered_df[mask]

    return render_template(
        "admin.html",
        active_page="admin",
        kpis=kpis,
        chart_mode=chart_mode,
        chart_type=chart_type,
        metric=metric,
        chart_html=chart_html,
        orders=filtered_df.to_dict(orient="records"),
        total_orders_count=total_orders,
        brands=BRANDS,
        categories=CATEGORIES,
        filter_brand=filter_brand,
        filter_cat=filter_cat,
        search_q=request.args.get("q", "")
    )


@app.route("/admin/update-status/<order_id>", methods=["POST"])
def admin_update_status(order_id):
    user = session.get("user")
    if not user or user.get("role") != "admin":
        return redirect(url_for("login_page", tab="admin-login"))

    new_status = request.form.get("status", "Confirmed")
    df = load_orders_df()
    df.loc[df["orderId"] == order_id, "status"] = new_status
    write_local_excel_files(df)
    firebase_request(f"orders/{order_id}/status", "PUT", new_status)
    flash(f"Order #{order_id} status updated to {new_status}.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete-order/<order_id>", methods=["POST"])
def admin_delete_order(order_id):
    user = session.get("user")
    if not user or user.get("role") != "admin":
        return redirect(url_for("login_page", tab="admin-login"))

    df = load_orders_df()
    df = df[df["orderId"] != order_id]
    write_local_excel_files(df)
    firebase_request(f"orders/{order_id}", "DELETE")
    flash(f"Order #{order_id} deleted.", "info")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/reset-demo", methods=["POST"])
def admin_reset_demo():
    user = session.get("user")
    if not user or user.get("role") != "admin":
        return redirect(url_for("login_page", tab="admin-login"))

    df = clean_orders_df(pd.DataFrame(INITIAL_DEMO_ORDERS))
    write_local_excel_files(df)
    if firebase_enabled():
        orders_dict = {row["orderId"]: row for row in df.to_dict(orient="records")}
        firebase_request("orders", "PUT", orders_dict)
    flash("Demo dataset restored.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/download-excel")
def admin_download_excel():
    user = session.get("user")
    if not user or user.get("role") != "admin":
        return redirect(url_for("login_page", tab="admin-login"))

    load_orders_df()
    return send_file(EXCEL_FILE, as_attachment=True, download_name="SoleMetrics_Orders_Master.xlsx")


if __name__ == "__main__":
    load_customers()
    load_orders_df()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)