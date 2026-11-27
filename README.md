# 👟 SoleMetrics — Multi-Brand Footwear Store & Executive BI Studio

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Analytics-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Interactive_BI-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)
![PWA](https://img.shields.io/badge/PWA-Installable_App-5A0FC8?style=for-the-badge&logo=pwa&logoColor=white)

**SoleMetrics** is a full-stack e-commerce Progressive Web App (PWA) and real-time Business Intelligence (BI) platform built with **Python (Flask)**, **Pandas**, **Plotly**, and **Firebase**. It combines an Amazon/iOS-inspired mobile-first storefront with an executive analytics dashboard that automatically syncs orders, customer demographics, profit margins, and verified reviews into multi-sheet Excel workbooks.

---

## ✨ Key Features

### 🛍️ Storefront & Customer Experience
- **Smart Live Search & Catalog Filtering:** Instant client-side search dropdown with product thumbnails alongside multi-brand (10 brands) and multi-category (10 footwear categories) filtering.
- **Product Detail & Conversion Tools:**
  - Interactive UK size selector (`UK 6` – `UK 11`) and sticky mobile quick-buy bar.
  - **Live Pincode Delivery Estimator:** Calculates city-specific delivery timelines and COD/UPI eligibility with `localStorage` persistence.
  - **Frequently Bought Together:** Dynamic combo bundle builder (Sneaker + Care Kit / Crew Socks) with real-time price calculation and single-tap bundle checkout.
  - **Recently Viewed Shelf:** Session-backed browsing history row across Home and Explore screens.
- **Wishlist, Cart & Order Lifecycle:** Persistent wishlist for registered accounts, multi-item shopping bag, automated Gmail order confirmations, live order stage tracking (`Confirmed` → `Packed` → `Shipped` → `Delivered`), and instant **PDF Tax Invoice** downloads via `FPDF`.
- **Progressive Web App (PWA) & Adaptive Dark Mode:** Installable on Android and iOS with a custom procedurally generated sneaker app icon (`Pillow`-free pure Python PNG encoder), service worker offline caching, and Light / OLED Dark / System theme switching.

### 📊 Executive Admin BI Dashboard
- **Global Power BI-Style Slicers:** Filter simultaneously by **Brand**, **Category**, **Order Status**, **Payment Mode**, **Date Range**, and keyword search—dynamically updating KPIs, charts, matrices, and order tables together.
- **6 Live Executive KPIs:** Tracks Total Revenue, Average Order Value (AOV), Gross Profit, Net Margin %, Order Volume, Pairs Sold, Top Brand, and Average Customer Rating.
- **Interactive Plotly Visualizations:**
  - Multi-dimension switcher (`Category`, `Brand`, `City`, `Top Models`, `UK Size`, `Age Group`, `Gender`, `Payment`, `Timeline`, `Star Ratings`) across `Bar`, `Line`, `Area`, and `Donut` geometries.
  - Side-by-side **Revenue vs. Gross Profit** grouped bar chart and **Order Fulfillment Pipeline** donut chart.
- **P&L & Customer Intelligence:** Live **Brand Profitability & Margin Matrix**, **VIP Customer Leaderboard** with Repeat Buyer Rate %, and 1-click exports to **Master Multi-Sheet Excel (`.xlsx`)** and **Filtered CSV**.

---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python, Flask, Jinja2 |
| **Data & Analytics** | Pandas, OpenPyXL, Plotly |
| **Cloud & Persistence** | Firebase Realtime Database (REST API), Multi-Sheet Excel (`orders.xlsx`), CSV & JSON Stores |
| **Document & Email Automation** | FPDF (Tax Invoice PDFs), Google Apps Script Gmail Webhook |
| **Frontend & Mobile** | HTML5, Custom Responsive CSS Utilities, Tailwind CSS, JavaScript, PWA (`manifest.json` + `sw.js`) |

---

## 📁 Project Structure

```text
SoleMetrics/
├── app.py                  # Main Flask server, BI engine, Plotly builders, PDF & PWA routes
├── data.py                 # Product catalog, brand/category metadata & seed orders
├── requirements.txt        # Python dependencies
├── static/
│   └── style.css           # Self-contained mobile-first utilities, animations & dark mode
├── templates/
│   ├── base.html           # Frosted glass header, mobile bottom tab bar & PWA install logic
│   ├── home.html           # Hero showcase, smart search, recently viewed & brand chips
│   ├── shop.html           # Filterable catalog grid with instant search
│   ├── product.html        # Pincode checker, combo bundle box, reviews & sticky buy bar
│   ├── cart.html           # Shopping bag management
│   ├── checkout.html       # Order checkout & payment selection
│   ├── receipt.html        # Order confirmation & PDF invoice download
│   ├── my_orders.html      # Customer order history & live tracking
│   ├── wishlist.html       # Saved footwear items
│   ├── reviews.html        # Verified buyer ratings & review submission
│   ├── login.html          # Customer Sign In / Sign Up & Admin access
│   └── admin.html          # Executive BI dashboard, Plotly charts & order fulfillment
└── README.md
