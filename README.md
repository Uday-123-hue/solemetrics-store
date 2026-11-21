# SoleMetrics — Multi-Brand Footwear E-Commerce & BI Analytics Platform

**Live Storefront:** [https://solemetrics-store-1.onrender.com](https://solemetrics-store-1.onrender.com)

SoleMetrics is a full-stack footwear e-commerce web application integrated with a real-time Business Intelligence (BI) analytics dashboard. Built with Python, Flask, Pandas, and Plotly, it bridges customer storefront operations with automated profit margin tracking, multi-sheet Excel reporting, and cloud synchronization.

---

## Key Features

### Customer Storefront & Checkout
* **Multi-Brand Catalog:** Browse footwear across 10 global & Indian brands (Nike, Adidas, Skechers, Crocs, Bata, Woodland, Sparx, Puma, Campus, Red Tape) and 10 specialized categories with live search and filtering.
* **Product Detail & Multi-Item Cart:** Interactive UK size selection, quantity controls, similar product recommendations, and session-based multi-item cart management.
* **Automated Order Confirmations & PDF Invoices:** Generates downloadable itemized tax invoices (`fpdf2`) and dispatches instant HTML order confirmation emails via the Brevo API.
* **Verified Customer Reviews:** Star ratings, experience tags, and automatic `Verified Buyer` badge detection cross-checked against order history.
* **Adaptive Minimal Luxury UI:** Responsive mobile/desktop interface featuring a 3-mode theme switcher (**Light**, **Obsidian Night**, and **System Default**).

### Admin Business Intelligence Dashboard
* **Executive KPIs:** Live calculation of Gross Revenue, Gross Profit, Net Margin %, Total Orders, Units Sold, Top Brand, and Average Rating.
* **Interactive Plotly Visualizations:** Dynamic Bar, Line, Area, and Donut charts across 10 analytical dimensions (Category, Brand, City, UK Size, Age Group, Gender, Top Models, Payment Mode, Cumulative Timeline, and Brand Ratings).
* **7-Sheet Automated Excel Master Export:** Generates a structured `.xlsx` workbook (`All_Orders`, `Brand_Profit_Summary`, `Category_Profit_Summary`, `City_And_Demographics`, `Customer_Reviews`, `Product_Ratings_Summary`, and `Registered_Customers`).
* **Dual Persistence:** Syncs live orders, reviews, and customer profiles with **Firebase Realtime Database** alongside local Excel/CSV backups.

---

## Tech Stack

* **Backend:** Python, Flask, Gunicorn
* **Data Analytics & Visualization:** Pandas, Plotly, OpenPyXL
* **PDF & Email Automation:** FPDF2, Brevo Transactional Email API
* **Database & Sync:** Firebase Realtime Database, Excel (`.xlsx`), CSV, JSON
* **Frontend:** HTML5, Tailwind CSS, Custom CSS3 Variables, Vanilla JavaScript

---

## Local Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Uday-123-hue/solemetrics-store.git](https://github.com/Uday-123-hue/solemetrics-store.git)
   cd solemetrics-store