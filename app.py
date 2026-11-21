import io
import os
import re
import json
import random
import smtplib
import urllib.error
import urllib.request
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF

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
REVIEWS_CSV_FILE = os.path.join(BASE_DIR, "reviews_backup.csv")
CUSTOMERS_FILE = os.path.join(BASE_DIR, "customers.json")

AGE_GROUPS = ["Under 18", "18-25", "26-40", "41-55", "55+"]
GENDERS = ["Male", "Female", "Other"]
UK_SIZES = ["UK 6", "UK 7", "UK 8", "UK 9", "UK 10", "UK 11"]
COST_PRICE_MAP = {p["id"]: int(p.get("cost_price", int(p["price"] * 0.6))) for p in PRODUCTS}

INITIAL_DEMO_REVIEWS = [
    {"reviewId": "REV-101", "date": "2026-11-15", "customerName": "Aarav Verma", "customerEmail": "aarav.v@gmail.com", "brand": "Nike", "productId": "NK-01", "productName": "Nike Air Force 1 '07 Low", "rating": 5, "experienceTag": "Build Quality", "comment": "Premium leather finish and super comfortable cushioning for daily college wear.", "verifiedBuyer": "Yes"},
    {"reviewId": "REV-102", "date": "2026-11-16", "customerName": "Rajendra Prasad", "customerEmail": "rprasad@gmail.com", "brand": "Skechers", "productId": "SK-01", "productName": "Skechers Go Walk Flex Orthopedic", "rating": 5, "experienceTag": "Comfort & Fit", "comment": "Bought these for my morning walk—zero heel pain and effortless slip-on fit.", "verifiedBuyer": "Yes"},
    {"reviewId": "REV-103", "date": "2026-11-17", "customerName": "Kabir Mehta", "customerEmail": "kabir.m@gmail.com", "brand": "Crocs", "productId": "CR-01", "productName": "Crocs Classic Clog Unisex", "rating": 4, "experienceTag": "Lightweight", "comment": "Very light and easy to wash. Great ventilation for all-day indoor and outdoor use.", "verifiedBuyer": "Yes"},
    {"reviewId": "REV-104", "date": "2026-11-18", "customerName": "Sneha Gupta", "customerEmail": "sneha.g@gmail.com", "brand": "Skechers", "productId": "SK-02", "productName": "Skechers Ladies Arch Fit Pastel", "rating": 5, "experienceTag": "Comfort & Fit", "comment": "Arch support feels amazing during long standing hours and the pastel shade looks clean.", "verifiedBuyer": "Yes"},
    {"reviewId": "REV-105", "date": "2026-11-19", "customerName": "Pooja Sharma", "customerEmail": "pooja.s@gmail.com", "brand": "Sparx", "productId": "SP-01", "productName": "Sparx SFG-549 Anti-Skid Flip-Flops", "rating": 4, "experienceTag": "Value for Money", "comment": "Strong wet-surface grip and soft EVA sole at a very budget-friendly price.", "verifiedBuyer": "Yes"}
]


# =========================================================================
# 1. AUTOMATIC ORDER CONFIRMATION EMAIL ENGINE (BREVO API + SMTP)
# =========================================================================
def send_order_confirmation_email(order_items: list, display_order_id: str, grand_total: int):
    if not order_items:
        return

    sender_email = os.environ.get("SENDER_EMAIL", "").strip()
    brevo_key = os.environ.get("BREVO_API_KEY", "").strip()
    smtp_login = os.environ.get("BREVO_SMTP_LOGIN", "").strip() or sender_email

    if not sender_email or not brevo_key:
        print("EMAIL SKIPPED: SENDER_EMAIL or BREVO_API_KEY is missing in Render Environment.")
        return

    first = order_items[0]
    to_email = str(first.get("customerEmail", "")).strip()
    to_name = str(first.get("customerName", "Customer")).strip()
    if not to_email:
        return

    total_pairs = sum(int(i.get("qty", 1)) for i in order_items)
    rows_html = ""
    for item in order_items:
        rows_html += f"""
        <tr>
          <td style="padding:12px 10px;border-bottom:1px solid #e4e4e7;font-size:13px;color:#18181b;">
            <span style="font-size:10px;font-weight:700;color:#4f46e5;text-transform:uppercase;display:block;">{item['brand']}</span>
            <b>{item['productName']}</b>
          </td>
          <td style="padding:12px 10px;border-bottom:1px solid #e4e4e7;font-size:13px;color:#52525b;text-align:center;">
            {item['size']}
          </td>
          <td style="padding:12px 10px;border-bottom:1px solid #e4e4e7;font-size:13px;color:#52525b;text-align:center;">
            {item['qty']}
          </td>
          <td style="padding:12px 10px;border-bottom:1px solid #e4e4e7;font-size:13px;color:#18181b;font-weight:700;text-align:right;">
            &#8377;{int(item['totalAmount']):,}
          </td>
        </tr>
        """

    subject = f"Your Order Has Been Confirmed (#{display_order_id}) — SoleMetrics"
    html_body = f"""
    <div style="font-family:'Inter',Arial,sans-serif;background:#f4f4f5;padding:28px 16px;">
      <div style="max-width:580px;margin:0 auto;background:#ffffff;border:1px solid #e4e4e7;border-radius:18px;overflow:hidden;">
        <div style="background:#09090b;color:#ffffff;padding:24px 28px;">
          <span style="display:inline-block;padding:4px 10px;border-radius:999px;background:rgba(16,185,129,0.18);color:#6ee7b7;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;">
            &#10003; Order Confirmed
          </span>
          <h1 style="margin:10px 0 4px;font-size:22px;letter-spacing:-0.4px;">Your Order Has Been Confirmed!</h1>
          <p style="margin:0;font-size:12px;color:#a1a1aa;">SoleMetrics Footwear Studio &bull; Order #{display_order_id}</p>
        </div>

        <div style="padding:26px 28px;">
          <p style="margin:0 0 12px;font-size:14px;color:#18181b;">Hi <b>{to_name}</b>,</p>
          <p style="margin:0 0 20px;font-size:13px;color:#52525b;line-height:1.6;">
            Thank you for shopping with <b>SoleMetrics</b>. Your order has been confirmed and is now being packed for dispatch. Here is your complete order summary:
          </p>

          <div style="background:#fafafa;border:1px solid #e4e4e7;border-radius:12px;padding:14px 16px;margin-bottom:20px;font-size:12px;color:#52525b;line-height:1.7;">
            <div><b style="color:#18181b;">Order ID:</b> #{display_order_id}</div>
            <div><b style="color:#18181b;">Order Date:</b> {first['date']}</div>
            <div><b style="color:#18181b;">Delivery City:</b> {first['city']}</div>
            <div><b style="color:#18181b;">Payment Mode:</b> {first['paymentMethod']}</div>
          </div>

          <table style="width:100%;border-collapse:collapse;margin-bottom:18px;">
            <thead>
              <tr style="background:#f4f4f5;color:#52525b;font-size:11px;text-transform:uppercase;">
                <th style="padding:10px;text-align:left;">Footwear</th>
                <th style="padding:10px;text-align:center;">Size</th>
                <th style="padding:10px;text-align:center;">Qty</th>
                <th style="padding:10px;text-align:right;">Price</th>
              </tr>
            </thead>
            <tbody>
              {rows_html}
            </tbody>
          </table>

          <div style="background:#09090b;color:#ffffff;padding:14px 18px;border-radius:12px;font-size:14px;">
            <table style="width:100%;border-collapse:collapse;">
              <tr>
                <td style="color:#d4d4d8;font-size:12px;">Total Paid ({total_pairs} Pair{'s' if total_pairs > 1 else ''})</td>
                <td style="text-align:right;font-size:17px;font-weight:800;color:#ffffff;">&#8377;{grand_total:,}</td>
              </tr>
            </table>
          </div>

          <p style="margin:22px 0 0;font-size:12px;color:#71717a;line-height:1.5;">
            You can download your PDF tax invoice anytime from the <b>My Orders</b> section on SoleMetrics.
          </p>
        </div>
      </div>
    </div>
    """

    # Primary: Brevo HTTPS API (xkeysib-...)
    if brevo_key.startswith("xkeysib-"):
        payload = {
            "sender": {"name": "SoleMetrics Store", "email": sender_email},
            "to": [{"email": to_email, "name": to_name}],
            "subject": subject,
            "htmlContent": html_body
        }
        req = urllib.request.Request(
            "https://api.brevo.com/v3/smtp/email",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "accept": "application/json",
                "api-key": brevo_key,
                "content-type": "application/json",
                "User-Agent": "SoleMetrics-Store/1.0"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                print(f"SUCCESS: Email sent to {to_email} (Status {resp.status})")
                return
        except urllib.error.HTTPError as e:
            err_detail = e.read().decode("utf-8", errors="ignore")
            print(f"BREVO API HTTP ERROR {e.code}: {err_detail}")
            return
        except Exception as e:
            print(f"BREVO API CONNECTION ERROR: {e}")
            return

    # Fallback: Brevo SMTP Relay (xsmtpsib-...)
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"SoleMetrics Store <{sender_email}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP("smtp-relay.brevo.com", 587, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_login, brevo_key)
            server.sendmail(sender_email, to_email, msg.as_string())
            print(f"SUCCESS: Email sent via SMTP to {to_email}")
    except Exception as e:
        print(f"BREVO SMTP ERROR (Port 587 blocked on Render Free Tier): {e}")


# =========================================================================
# 2. FIREBASE CLOUD SYNC HELPERS
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
# 3. CUSTOMER ACCOUNT STORAGE
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
# 4. REVIEWS STORAGE (PANDAS + EXCEL + FIREBASE)
# =========================================================================
def clean_reviews_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=list(INITIAL_DEMO_REVIEWS[0].keys()))
    df = df.fillna("")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(5).clip(1, 5).astype(int)
    if "verifiedBuyer" not in df.columns:
        df["verifiedBuyer"] = "No"
    if "experienceTag" not in df.columns:
        df["experienceTag"] = "Comfort & Fit"
    return df


def load_reviews_df() -> pd.DataFrame:
    if firebase_enabled():
        cloud_rev = firebase_request("reviews", "GET")
        if cloud_rev is None:
            if os.path.exists(REVIEWS_CSV_FILE):
                df = clean_reviews_df(pd.read_csv(REVIEWS_CSV_FILE, dtype=str))
            else:
                df = clean_reviews_df(pd.DataFrame(INITIAL_DEMO_REVIEWS))
            rev_dict = {row["reviewId"]: row for row in df.to_dict(orient="records")}
            firebase_request("reviews", "PUT", rev_dict)
            df.to_csv(REVIEWS_CSV_FILE, index=False)
            return df
        rows = list(cloud_rev.values()) if isinstance(cloud_rev, dict) else [r for r in cloud_rev if r]
        df = clean_reviews_df(pd.DataFrame(rows))
        df.to_csv(REVIEWS_CSV_FILE, index=False)
        return df

    if os.path.exists(REVIEWS_CSV_FILE):
        return clean_reviews_df(pd.read_csv(REVIEWS_CSV_FILE, dtype=str))

    df = clean_reviews_df(pd.DataFrame(INITIAL_DEMO_REVIEWS))
    df.to_csv(REVIEWS_CSV_FILE, index=False)
    return df


# =========================================================================
# 5. PANDAS EXCEL + PROFIT & RATINGS ANALYTICS ENGINE
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


def write_local_excel_files(df: pd.DataFrame, customers_list: list = None, reviews_df: pd.DataFrame = None):
    df.to_csv(CSV_BACKUP_FILE, index=False)
    rev_df = reviews_df if reviews_df is not None else load_reviews_df()
    rev_df.to_csv(REVIEWS_CSV_FILE, index=False)

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

    if not rev_df.empty:
        ratings_summary = rev_df.groupby(["brand", "productName"], as_index=False).agg(
            Total_Reviews=("reviewId", "count"),
            Avg_Rating=("rating", "mean")
        )
        ratings_summary["Avg_Rating"] = ratings_summary["Avg_Rating"].round(2)
    else:
        ratings_summary = pd.DataFrame(columns=["brand", "productName", "Total_Reviews", "Avg_Rating"])

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
            rev_df.to_excel(writer, sheet_name="Customer_Reviews", index=False)
            ratings_summary.to_excel(writer, sheet_name="Product_Ratings_Summary", index=False)
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
# 6. PYTHON PLOTLY ADAPTIVE LIGHT/DARK MULTI-CHART GENERATOR
# =========================================================================
def build_animated_chart_html(df: pd.DataFrame, mode: str, chart_type: str, metric: str, rev_df: pd.DataFrame = None) -> str:
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

    if mode == "ratings":
        rdf = rev_df if rev_df is not None else load_reviews_df()
        agg = rdf.groupby("brand")["rating"].mean().round(2).to_dict() if not rdf.empty else {}
        labels = BRANDS
        values = [float(agg.get(b, 0)) for b in BRANDS]
        y_label = "Avg Rating (★)"
        is_currency = False
        title = "Brand Star Ratings (out of 5)"
    elif mode == "category":
        agg = df.groupby("category")[col].sum().to_dict() if not df.empty else {}
        labels = [c["name"] for c in CATEGORIES]
        values = [int(agg.get(c["name"], 0)) for c in CATEGORIES]
        title = f"{y_label} by Category"
    elif mode == "brand":
        agg = df.groupby("brand")[col].sum().to_dict() if not df.empty else {}
        labels = BRANDS
        values = [int(agg.get(b, 0)) for b in BRANDS]
        title = f"{y_label} by Brand"
    elif mode == "city":
        s = df.groupby("city")[col].sum().sort_values(ascending=False) if not df.empty else pd.Series(dtype=int)
        labels = list(s.index)
        values = [int(v) for v in s.values]
        title = f"City Demand — {y_label}"
    elif mode == "size":
        agg = df.groupby("size")[col].sum().to_dict() if not df.empty else {}
        labels = UK_SIZES
        values = [int(agg.get(sz, 0)) for sz in UK_SIZES]
        title = f"UK Size — {y_label}"
    elif mode == "age":
        agg = df.groupby("ageGroup")[col].sum().to_dict() if not df.empty else {}
        labels = AGE_GROUPS
        values = [int(agg.get(ag, 0)) for ag in AGE_GROUPS]
        title = f"Age Group — {y_label}"
    elif mode == "gender":
        agg = df.groupby("gender")[col].sum().to_dict() if not df.empty else {}
        labels = GENDERS
        values = [int(agg.get(g, 0)) for g in GENDERS]
        title = f"Gender — {y_label}"
    elif mode == "model":
        s = (
            df.groupby("productName")[col].sum().sort_values(ascending=False).head(8)
            if not df.empty else pd.Series(dtype=int)
        )
        labels = [name[:18] + "…" if len(name) > 18 else name for name in s.index]
        values = [int(v) for v in s.values]
        title = f"Top Models — {y_label}"
    elif mode == "payment":
        s = df.groupby("paymentMethod")[col].sum() if not df.empty else pd.Series(dtype=int)
        labels = list(s.index)
        values = [int(v) for v in s.values]
        title = f"Payment Mode — {y_label}"
    elif mode == "timeline":
        s = df.groupby("date")[col].sum().sort_index() if not df.empty else pd.Series(dtype=int)
        labels = [str(d)[5:] for d in s.index]
        running = 0
        for v in s.values:
            running += int(v)
            values.append(running)
        title = f"Cumulative {y_label}"

    palette = [
        "#6366f1", "#0ea5e9", "#10b981", "#f59e0b", "#8b5cf6",
        "#ec4899", "#14b8a6", "#f97316", "#3b82f6", "#64748b"
    ]
    if mode == "ratings":
        text_labels = [f"{v}★" if v > 0 else "" for v in values]
    elif is_currency:
        text_labels = [f"₹{v:,}" if v > 0 else "" for v in values]
    else:
        text_labels = [str(v) if v > 0 else "" for v in values]

    if chart_type == "bar":
        bar_colors = [palette[i % len(palette)] for i in range(len(labels))]
        trace = go.Bar(
            x=labels,
            y=values,
            text=text_labels,
            textposition="auto",
            marker=dict(color=bar_colors),
            hovertemplate="<b>%{x}</b><br>" + y_label + ": %{y}<extra></extra>"
        )
    elif chart_type == "area":
        trace = go.Scatter(
            x=labels,
            y=values,
            mode="lines+markers",
            fill="tozeroy",
            fillcolor="rgba(99, 102, 241, 0.16)",
            line=dict(color="#6366f1", width=3, shape="spline"),
            marker=dict(size=8, color="#6366f1", line=dict(width=2, color="#ffffff")),
            hovertemplate="<b>%{x}</b><br>" + y_label + ": %{y}<extra></extra>"
        )
    elif chart_type == "pie":
        trace = go.Pie(
            labels=labels,
            values=values,
            hole=0.50,
            marker=dict(colors=palette, line=dict(color="rgba(148,163,184,0.25)", width=1.5)),
            textinfo="percent",
            textposition="inside",
            hovertemplate="<b>%{label}</b><br>" + y_label + ": %{value} (%{percent})<extra></extra>"
        )
    else:
        trace = go.Scatter(
            x=labels,
            y=values,
            mode="lines+markers",
            line=dict(color="#6366f1", width=3, shape="spline"),
            marker=dict(size=9, color="#6366f1", line=dict(width=2, color="#ffffff")),
            hovertemplate="<b>%{x}</b><br>" + y_label + ": %{y}<extra></extra>"
        )

    fig = go.Figure(data=[trace])
    max_val = max(values) if values else 10

    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>",
            x=0.02,
            font=dict(size=14, color="#18181b", family="Plus Jakarta Sans, Inter, sans-serif")
        ),
        autosize=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(148,163,184,0.05)",
        font=dict(family="Inter, sans-serif", size=11, color="#52525b"),
        height=360,
        margin=dict(l=12, r=12, t=48, b=35),
        uniformtext_minsize=9,
        uniformtext_mode="hide",
        hoverlabel=dict(bgcolor="#18181b", font_size=12, font_color="#ffffff"),
        transition=dict(duration=550, easing="cubic-in-out")
    )

    if chart_type == "pie":
        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.06,
                xanchor="center",
                x=0.5,
                font=dict(size=10)
            )
        )
    else:
        fig.update_xaxes(
            showgrid=False,
            tickangle=-35,
            automargin=True,
            tickfont=dict(size=10)
        )
        y_max = 5.6 if mode == "ratings" else (max_val * 1.18 if max_val > 0 else 10)
        fig.update_yaxes(
            title_text="",
            gridcolor="#e4e4e7",
            zeroline=True,
            zerolinecolor="#d4d4d8",
            automargin=True,
            tickfont=dict(size=10),
            range=[0, y_max]
        )

    return fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
        config={"responsive": True, "displayModeBar": "hover", "displaylogo": False}
    )


# =========================================================================
# 7. CART & GLOBAL TEMPLATE HELPERS
# =========================================================================
def get_cart_details():
    raw_cart = session.get("cart", {})
    prod_map = {p["id"]: p for p in PRODUCTS}
    items = []
    total_qty = 0
    grand_total = 0

    for item_key, entry in raw_cart.items():
        pid = entry.get("product_id")
        prod = prod_map.get(pid)
        if not prod:
            continue
        size = entry.get("size", "UK 8")
        qty = max(1, int(entry.get("qty", 1)))
        unit_price = int(prod["price"])
        subtotal = unit_price * qty
        total_qty += qty
        grand_total += subtotal
        items.append({
            "key": item_key,
            "product": prod,
            "size": size,
            "qty": qty,
            "unitPrice": unit_price,
            "subtotal": subtotal
        })

    return items, total_qty, grand_total


@app.context_processor
def inject_globals():
    raw_cart = session.get("cart", {})
    cart_count = sum(int(v.get("qty", 1)) for v in raw_cart.values()) if isinstance(raw_cart, dict) else 0
    return {
        "current_user": session.get("user"),
        "fallback_img": REAL_SHOE_FALLBACK_URL,
        "cart_count": cart_count
    }


@app.template_filter("inr")
def format_inr(value):
    return f"₹{int(value or 0):,}"


# =========================================================================
# 8. STOREFRONT, PRODUCT DETAIL, CART, AUTH & ORDER ROUTES
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


@app.route("/product/<product_id>")
def product_detail(product_id):
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        flash("Footwear model not found.", "error")
        return redirect(url_for("shop"))

    rev_df = load_reviews_df()
    prod_rev_df = rev_df[rev_df["productId"] == product_id] if not rev_df.empty else pd.DataFrame()
    product_reviews = prod_rev_df.to_dict(orient="records") if not prod_rev_df.empty else []
    avg_rating = round(float(prod_rev_df["rating"].mean()), 1) if not prod_rev_df.empty else 0.0

    similar = [
        p for p in PRODUCTS
        if p["id"] != product_id and (p["category"] == product["category"] or p["brand"] == product["brand"])
    ][:4]

    return render_template(
        "product.html",
        active_page="shop",
        product=product,
        uk_sizes=UK_SIZES,
        product_reviews=product_reviews,
        avg_rating=avg_rating,
        similar=similar
    )


@app.route("/cart")
def cart_page():
    items, total_qty, grand_total = get_cart_details()
    return render_template(
        "cart.html",
        active_page="cart",
        items=items,
        total_qty=total_qty,
        grand_total=grand_total
    )


@app.route("/add-to-cart/<product_id>", methods=["GET", "POST"])
def add_to_cart(product_id):
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        flash("Footwear model not found.", "error")
        return redirect(url_for("shop"))

    size = request.values.get("size", "UK 8").strip() or "UK 8"
    qty = max(1, min(10, int(request.values.get("qty", 1))))
    action = request.values.get("action", "cart")

    cart = session.get("cart", {})
    if not isinstance(cart, dict):
        cart = {}

    item_key = f"{product_id}__{size}"
    if item_key in cart:
        cart[item_key]["qty"] = min(10, int(cart[item_key].get("qty", 1)) + qty)
    else:
        cart[item_key] = {
            "product_id": product_id,
            "size": size,
            "qty": qty
        }

    session["cart"] = cart
    session.modified = True

    if action == "buy_now":
        return redirect(url_for("checkout"))

    flash(f"Added {product['name']} ({size}) to your cart.", "success")
    return redirect(request.referrer or url_for("cart_page"))


@app.route("/update-cart", methods=["POST"])
def update_cart():
    item_key = request.form.get("item_key", "")
    qty = int(request.form.get("qty", 1))
    cart = session.get("cart", {})

    if item_key in cart:
        if qty <= 0:
            cart.pop(item_key, None)
        else:
            cart[item_key]["qty"] = min(10, qty)
        session["cart"] = cart
        session.modified = True

    return redirect(url_for("cart_page"))


@app.route("/remove-from-cart/<item_key>", methods=["GET", "POST"])
def remove_from_cart(item_key):
    cart = session.get("cart", {})
    if item_key in cart:
        cart.pop(item_key, None)
        session["cart"] = cart
        session.modified = True
        flash("Item removed from cart.", "info")
    return redirect(url_for("cart_page"))


@app.route("/reviews")
def reviews_page():
    selected_product_id = request.args.get("product_id", "NK-01")
    rev_df = load_reviews_df()
    reviews = rev_df.to_dict(orient="records")

    avg_rating = round(float(rev_df["rating"].mean()), 1) if not rev_df.empty else 0.0
    star_counts = {s: int((rev_df["rating"] == s).sum()) if not rev_df.empty else 0 for s in [5, 4, 3, 2, 1]}

    return render_template(
        "reviews.html",
        active_page="reviews",
        products=PRODUCTS,
        selected_product_id=selected_product_id,
        reviews=reviews,
        avg_rating=avg_rating,
        star_counts=star_counts
    )


@app.route("/submit-review", methods=["POST"])
def submit_review():
    user = session.get("user")
    if user and user.get("role") == "customer":
        customer_name = user["name"]
        customer_email = user["email"].strip().lower()
    else:
        customer_name = request.form.get("customer_name", "").strip()
        customer_email = request.form.get("customer_email", "").strip().lower()

    product_id = request.form.get("product_id", "NK-01")
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product or not customer_name or not customer_email:
        flash("Please fill in all review details.", "error")
        return redirect(url_for("reviews_page"))

    if not re.fullmatch(r"[a-zA-Z0-9._%+-]+@gmail\.com", customer_email):
        flash("Please enter a valid Gmail address ending with @gmail.com.", "error")
        return redirect(url_for("reviews_page", product_id=product_id))

    rating = max(1, min(5, int(request.form.get("rating", 5))))
    experience_tag = request.form.get("experience_tag", "Comfort & Fit").strip()
    comment = request.form.get("comment", "").strip()

    orders_df = load_orders_df()
    is_verified = False
    if not orders_df.empty:
        is_verified = bool(
            (
                (orders_df["customerEmail"].str.lower() == customer_email)
                & (orders_df["productId"] == product_id)
            ).any()
        )

    review_id = f"REV-{random.randint(100, 9999)}"
    new_review = {
        "reviewId": review_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "customerName": customer_name,
        "customerEmail": customer_email,
        "brand": product["brand"],
        "productId": product["id"],
        "productName": product["name"],
        "rating": rating,
        "experienceTag": experience_tag,
        "comment": comment,
        "verifiedBuyer": "Yes" if is_verified else "No"
    }

    rev_df = load_reviews_df()
    rev_df = pd.concat([pd.DataFrame([new_review]), rev_df], ignore_index=True)
    write_local_excel_files(orders_df, reviews_df=rev_df)
    firebase_request(f"reviews/{review_id}", "PUT", new_review)

    flash("Thank you! Your review has been published.", "success")
    return redirect(url_for("product_detail", product_id=product_id))


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

    if not re.fullmatch(r"[a-zA-Z0-9._%+-]+@gmail\.com", email):
        flash("Please enter a valid Gmail address ending with @gmail.com.", "error")
        return redirect(url_for("login_page", tab="customer-login", next=next_url))

    customers = load_customers()
    account = next((c for c in customers if c["email"].strip().lower() == email), None)

    if not account:
        flash("No account found with this Gmail. Please create an account first.", "error")
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

    if len(name) < 2:
        flash("Please enter your full name.", "error")
        return redirect(url_for("login_page", tab="customer-signup", next=next_url))

    if not re.fullmatch(r"[a-zA-Z0-9._%+-]+@gmail\.com", email):
        flash("Please enter a valid Gmail address ending with @gmail.com.", "error")
        return redirect(url_for("login_page", tab="customer-signup", next=next_url))

    if not re.fullmatch(r"\d{10}", phone):
        flash("Please enter a valid 10-digit mobile number.", "error")
        return redirect(url_for("login_page", tab="customer-signup", next=next_url))

    if len(password) < 4:
        flash("Password must be at least 4 characters long.", "error")
        return redirect(url_for("login_page", tab="customer-signup", next=next_url))

    customers = load_customers()
    if any(c["email"].strip().lower() == email for c in customers):
        flash("This Gmail is already registered. Please sign in with your password.", "error")
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
    flash(f"Account created! Welcome to SoleMetrics, {name}.", "success")
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


@app.route("/checkout")
@app.route("/checkout/<product_id>")
def checkout(product_id=None):
    if product_id:
        return redirect(url_for("add_to_cart", product_id=product_id, action="buy_now"))

    user = session.get("user")
    if not user or user.get("role") != "customer":
        flash("Please login or create an account before placing an order.", "error")
        return redirect(url_for("login_page", tab="customer-login", next=url_for("checkout")))

    items, total_qty, grand_total = get_cart_details()
    if not items:
        flash("Your cart is empty. Add footwear before checkout.", "info")
        return redirect(url_for("shop"))

    return render_template(
        "checkout.html",
        active_page="cart",
        items=items,
        total_qty=total_qty,
        grand_total=grand_total
    )


@app.route("/place-order", methods=["POST"])
def place_order():
    user = session.get("user")
    if not user or user.get("role") != "customer":
        flash("Please sign in first.", "error")
        return redirect(url_for("login_page"))

    items, total_qty, grand_total = get_cart_details()
    if not items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("shop"))

    city = request.form.get("city", "").strip() or user.get("city", "India")
    payment_method = request.form.get("payment_method", "UPI")
    today_str = datetime.now().strftime("%Y-%m-%d")
    base_code = f"ORD-{random.randint(1000, 9999)}"

    new_rows = []
    for idx, item in enumerate(items, start=1):
        prod = item["product"]
        unit_price = int(prod["price"])
        cost_price = int(prod.get("cost_price", int(unit_price * 0.6)))
        qty = int(item["qty"])
        total_amount = unit_price * qty
        profit = total_amount - (cost_price * qty)
        order_id = base_code if len(items) == 1 else f"{base_code}-{idx}"

        row = {
            "orderId": order_id,
            "date": today_str,
            "customerName": user["name"],
            "customerEmail": user["email"],
            "customerPhone": user.get("phone", ""),
            "gender": user.get("gender", "Male"),
            "ageGroup": user.get("ageGroup", "18-25"),
            "city": city,
            "brand": prod["brand"],
            "productId": prod["id"],
            "productName": prod["name"],
            "category": prod["category"],
            "size": item["size"],
            "qty": qty,
            "unitPrice": unit_price,
            "costPrice": cost_price,
            "totalAmount": total_amount,
            "profit": profit,
            "paymentMethod": payment_method,
            "status": "Confirmed"
        }
        new_rows.append(row)
        firebase_request(f"orders/{order_id}", "PUT", row)

    df = load_orders_df()
    df = pd.concat([pd.DataFrame(new_rows), df], ignore_index=True)
    write_local_excel_files(df)

    # Automatically send confirmation email to customer
    send_order_confirmation_email(new_rows, base_code, grand_total)

    session["cart"] = {}
    session.modified = True

    flash("Your order has been confirmed! A confirmation email has been sent.", "success")
    return redirect(url_for("receipt", order_id=new_rows[0]["orderId"]))


def get_order_group(order_id: str):
    df = load_orders_df()
    if df.empty:
        return []
    parts = order_id.split("-")
    base_prefix = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else order_id
    group_df = df[(df["orderId"] == order_id) | (df["orderId"].str.startswith(base_prefix + "-"))]
    if group_df.empty:
        return []
    return group_df.to_dict(orient="records")


@app.route("/receipt/<order_id>")
def receipt(order_id):
    order_items = get_order_group(order_id)
    if not order_items:
        flash("Receipt not found.", "error")
        return redirect(url_for("home"))

    first = order_items[0]
    parts = first["orderId"].split("-")
    display_order_id = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else first["orderId"]
    grand_total = sum(int(i["totalAmount"]) for i in order_items)
    total_pairs = sum(int(i["qty"]) for i in order_items)
    img_map = {p["id"]: p["image"] for p in PRODUCTS}

    return render_template(
        "receipt.html",
        active_page="my-orders",
        order=first,
        order_items=order_items,
        display_order_id=display_order_id,
        grand_total=grand_total,
        total_pairs=total_pairs,
        img_map=img_map
    )


@app.route("/invoice-pdf/<order_id>")
def download_invoice_pdf(order_id):
    order_items = get_order_group(order_id)
    if not order_items:
        flash("Invoice not found.", "error")
        return redirect(url_for("home"))

    first = order_items[0]
    parts = first["orderId"].split("-")
    display_order_id = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else first["orderId"]
    grand_total = sum(int(i["totalAmount"]) for i in order_items)

    pdf = FPDF()
    pdf.add_page()

    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 36, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_xy(14, 10)
    pdf.cell(120, 10, "SOLEMETRICS", ln=False)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(62, 10, "TAX INVOICE", align="R", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_x(14)
    pdf.cell(120, 6, "Multi-Brand Footwear Store | India", ln=False)
    pdf.cell(62, 6, f"Invoice #{display_order_id}", align="R", ln=True)

    pdf.set_text_color(30, 41, 59)
    pdf.set_xy(14, 44)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(95, 6, "BILLED TO:", ln=False)
    pdf.cell(87, 6, "ORDER DETAILS:", align="R", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(14)
    pdf.cell(95, 6, f"{first['customerName']}", ln=False)
    pdf.cell(87, 6, f"Order Date: {first['date']}", align="R", ln=True)

    pdf.set_x(14)
    pdf.cell(95, 6, f"Email: {first['customerEmail']}", ln=False)
    pdf.cell(87, 6, f"Payment Mode: {first['paymentMethod']}", align="R", ln=True)

    pdf.set_x(14)
    pdf.cell(95, 6, f"Delivery City: {first['city']}", ln=False)
    pdf.cell(87, 6, f"Status: {first['status']}", align="R", ln=True)

    pdf.ln(10)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_draw_color(203, 213, 225)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_x(14)
    pdf.cell(12, 9, "#", border=1, fill=True, align="C")
    pdf.cell(86, 9, "Footwear Model & Brand", border=1, fill=True)
    pdf.cell(22, 9, "Size", border=1, fill=True, align="C")
    pdf.cell(16, 9, "Qty", border=1, fill=True, align="C")
    pdf.cell(22, 9, "Price", border=1, fill=True, align="R")
    pdf.cell(24, 9, "Amount", border=1, fill=True, align="R", ln=True)

    pdf.set_font("Helvetica", "", 9)
    for idx, item in enumerate(order_items, start=1):
        label = f"{item['brand']} - {item['productName']}"
        if len(label) > 44:
            label = label[:42] + ".."
        pdf.set_x(14)
        pdf.cell(12, 9, str(idx), border=1, align="C")
        pdf.cell(86, 9, label, border=1)
        pdf.cell(22, 9, str(item["size"]), border=1, align="C")
        pdf.cell(16, 9, str(item["qty"]), border=1, align="C")
        pdf.cell(22, 9, f"Rs. {int(item['unitPrice']):,}", border=1, align="R")
        pdf.cell(24, 9, f"Rs. {int(item['totalAmount']):,}", border=1, align="R", ln=True)

    pdf.ln(4)
    pdf.set_x(126)
    pdf.set_fill_color(15, 23, 42)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(70, 11, f"Grand Total: Rs. {grand_total:,}", border=0, fill=True, align="R", ln=True)

    pdf.set_text_color(100, 116, 139)
    pdf.set_font("Helvetica", "I", 9)
    pdf.ln(14)
    pdf.set_x(14)
    pdf.cell(182, 6, "Thank you for shopping with SoleMetrics! This is a computer-generated invoice.", align="C", ln=True)

    pdf_bytes = bytes(pdf.output())
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"SoleMetrics_Invoice_{display_order_id}.pdf"
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
# 9. PRIVATE ADMIN ANALYTICS ROUTES
# =========================================================================
@app.route("/admin")
def admin_dashboard():
    user = session.get("user")
    if not user or user.get("role") != "admin":
        flash("Authorized Admin login required.", "error")
        return redirect(url_for("login_page", tab="admin-login"))

    df = load_orders_df()
    rev_df = load_reviews_df()

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
    avg_rating = round(float(rev_df["rating"].mean()), 1) if not rev_df.empty else 0.0

    kpis = [
        {"label": "Total Revenue", "value": f"₹{total_revenue:,}", "sub": "Gross top-line sales"},
        {"label": "Gross Profit", "value": f"₹{total_profit:,}", "sub": f"{margin_pct}% Net Margin"},
        {"label": "Total Orders", "value": total_orders, "sub": "Confirmed orders"},
        {"label": "Pairs Sold", "value": total_units, "sub": "Total units shipped"},
        {"label": "Top Brand", "value": top_brand, "sub": "Highest unit demand"},
        {"label": "Avg Rating", "value": f"{avg_rating} ★", "sub": f"{len(rev_df)} customer reviews"}
    ]

    chart_html = build_animated_chart_html(df, chart_mode, chart_type, metric, rev_df)

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
        reviews=rev_df.to_dict(orient="records"),
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


@app.route("/admin/delete-review/<review_id>", methods=["POST"])
def admin_delete_review(review_id):
    user = session.get("user")
    if not user or user.get("role") != "admin":
        return redirect(url_for("login_page", tab="admin-login"))

    rev_df = load_reviews_df()
    rev_df = rev_df[rev_df["reviewId"] != review_id]
    write_local_excel_files(load_orders_df(), reviews_df=rev_df)
    firebase_request(f"reviews/{review_id}", "DELETE")
    flash(f"Review #{review_id} deleted.", "info")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/reset-demo", methods=["POST"])
def admin_reset_demo():
    user = session.get("user")
    if not user or user.get("role") != "admin":
        return redirect(url_for("login_page", tab="admin-login"))

    df = clean_orders_df(pd.DataFrame(INITIAL_DEMO_ORDERS))
    rev_df = clean_reviews_df(pd.DataFrame(INITIAL_DEMO_REVIEWS))
    write_local_excel_files(df, reviews_df=rev_df)
    if firebase_enabled():
        firebase_request("orders", "PUT", {row["orderId"]: row for row in df.to_dict(orient="records")})
        firebase_request("reviews", "PUT", {row["reviewId"]: row for row in rev_df.to_dict(orient="records")})
    flash("Demo orders & reviews restored.", "success")
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
    load_reviews_df()
    load_orders_df()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)