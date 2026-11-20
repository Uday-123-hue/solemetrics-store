# Admin Username & Password
ADMIN_CREDENTIALS = {
    "username": "admin",
    "password": "admin123"
}

# Optional: Firebase Realtime Database URL (Local mode ke liye khali chhod sakte ho)
FIREBASE_DB_URL = "https://solemetrics-dbff1-default-rtdb.firebaseio.com"

REAL_SHOE_FALLBACK_URL = (
    "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80"
)

BRANDS = [
    "Nike", "Adidas", "Puma", "Skechers", "Crocs",
    "Bata", "Woodland", "Campus", "Sparx", "Hush Puppies"
]

CATEGORIES = [
    {"name": "Sneakers", "image": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=600&q=80", "tag": "Street & Casual"},
    {"name": "Running", "image": "https://images.unsplash.com/photo-1551107696-a4b0c5a0d9a2?auto=format&fit=crop&w=600&q=80", "tag": "High Cushion"},
    {"name": "Formal", "image": "https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?auto=format&fit=crop&w=600&q=80", "tag": "Office & Events"},
    {"name": "High-Tops", "image": "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=600&q=80", "tag": "Ankle Support"},
    {"name": "Ladies", "image": "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?auto=format&fit=crop&w=600&q=80", "tag": "Women Collection"},
    {"name": "Kids", "image": "https://images.unsplash.com/photo-1514989940723-e8e51635b782?auto=format&fit=crop&w=600&q=80", "tag": "Junior & School"},
    {"name": "Senior Comfort", "image": "https://images.unsplash.com/photo-1539185441755-769473a23570?auto=format&fit=crop&w=600&q=80", "tag": "Orthopedic Care"},
    {"name": "Slippers", "image": "https://images.unsplash.com/photo-1603487742131-4160ec999306?auto=format&fit=crop&w=600&q=80", "tag": "Daily Home Wear"},
    {"name": "Flip-Flops", "image": "https://images.unsplash.com/photo-1562183241-b937e95585b6?auto=format&fit=crop&w=600&q=80", "tag": "Beach & Monsoon"},
    {"name": "Crocs & Clogs", "image": "https://images.unsplash.com/photo-1626379616459-b2ce1d9decbc?auto=format&fit=crop&w=600&q=80", "tag": "Croslite Foam"}
]

# Har shoe me 'price' (Selling Price) aur 'cost_price' (Wholesale Cost) dono added hain
PRODUCTS = [
    # NIKE
    {"id": "NK-01", "brand": "Nike", "name": "Nike Air Force 1 '07 Low", "category": "Sneakers", "price": 7495, "cost_price": 4500, "rating": "4.9", "badge": "Bestseller", "image": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=800&q=80", "desc": "Crisp leather upper with encapsulated Nike Air cushioning for all-day comfort."},
    {"id": "NK-02", "brand": "Nike", "name": "Nike Pegasus 42 Road Runner", "category": "Running", "price": 10995, "cost_price": 6800, "rating": "4.8", "badge": "Pro Runner", "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80", "desc": "Responsive ReactX foam midsole with breathable mesh for daily mileage."},
    {"id": "NK-03", "brand": "Nike", "name": "Nike Court Vision Mid High-Top", "category": "High-Tops", "price": 5995, "cost_price": 3600, "rating": "4.7", "badge": "Classic", "image": "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=800&q=80", "desc": "80s basketball-inspired padded high-top collar with durable rubber sole."},

    # ADIDAS
    {"id": "AD-01", "brand": "Adidas", "name": "Adidas Samba OG White", "category": "Sneakers", "price": 9999, "cost_price": 6200, "rating": "4.9", "badge": "Trending", "image": "https://images.unsplash.com/photo-1518002171953-a080ee817e1f?auto=format&fit=crop&w=800&q=80", "desc": "Full-grain leather upper with suede T-toe overlay and gum rubber sole."},
    {"id": "AD-02", "brand": "Adidas", "name": "Adidas Runfalcon 5 Cloudfoam", "category": "Running", "price": 4599, "cost_price": 2700, "rating": "4.6", "badge": "Value Pick", "image": "https://images.unsplash.com/photo-1551107696-a4b0c5a0d9a2?auto=format&fit=crop&w=800&q=80", "desc": "Lightweight 290g runner with Cloudfoam cushioning and high-grip outsole."},
    {"id": "AD-03", "brand": "Adidas", "name": "Adidas Adilette Comfort Slides", "category": "Slippers", "price": 2999, "cost_price": 1650, "rating": "4.8", "badge": "Soft Footbed", "image": "https://images.unsplash.com/photo-1603487742131-4160ec999306?auto=format&fit=crop&w=800&q=80", "desc": "Contoured Cloudfoam Plus footbed for plush indoor and post-workout comfort."},

    # PUMA
    {"id": "PM-01", "brand": "Puma", "name": "Puma Court Shatter Low", "category": "Sneakers", "price": 3499, "cost_price": 2050, "rating": "4.7", "badge": "SoftFoam+", "image": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?auto=format&fit=crop&w=800&q=80", "desc": "Clean tennis-inspired silhouette paired with step-in SoftFoam+ sockliner."},
    {"id": "PM-02", "brand": "Puma", "name": "Puma Velocity Nitro 3", "category": "Running", "price": 8999, "cost_price": 5400, "rating": "4.8", "badge": "Nitrogen Foam", "image": "https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?auto=format&fit=crop&w=800&q=80", "desc": "Nitrogen-injected midsole with PUMAGRIP all-surface traction rubber."},

    # SKECHERS
    {"id": "SK-01", "brand": "Skechers", "name": "Skechers Go Walk Flex Orthopedic", "category": "Senior Comfort", "price": 4499, "cost_price": 2600, "rating": "4.9", "badge": "Doctor Recommended", "image": "https://images.unsplash.com/photo-1539185441755-769473a23570?auto=format&fit=crop&w=800&q=80", "desc": "Hands-free slip-on with Air-Cooled Goga Mat arch support for seniors."},
    {"id": "SK-02", "brand": "Skechers", "name": "Skechers Ladies Arch Fit Pastel", "category": "Ladies", "price": 4999, "cost_price": 2900, "rating": "4.8", "badge": "Women Favorite", "image": "https://images.unsplash.com/photo-1560769629-975ec94e6a86?auto=format&fit=crop&w=800&q=80", "desc": "Podiatrist-certified arch support with ultra-lightweight knit upper."},

    # CROCS
    {"id": "CR-01", "brand": "Crocs", "name": "Crocs Classic Clog Unisex", "category": "Crocs & Clogs", "price": 3995, "cost_price": 2100, "rating": "4.9", "badge": "Iconic Comfort", "image": "https://images.unsplash.com/photo-1626379616459-b2ce1d9decbc?auto=format&fit=crop&w=800&q=80", "desc": "Water-friendly Croslite foam construction with ventilation ports."},
    {"id": "CR-02", "brand": "Crocs", "name": "Crocs Kids Crocband Clog", "category": "Kids", "price": 2795, "cost_price": 1450, "rating": "4.8", "badge": "Easy Wash", "image": "https://images.unsplash.com/photo-1514989940723-e8e51635b782?auto=format&fit=crop&w=800&q=80", "desc": "Lightweight, non-marking Croslite clogs built for active kids."},

    # BATA
    {"id": "BT-01", "brand": "Bata", "name": "Bata Ambassador Black Oxford", "category": "Formal", "price": 1799, "cost_price": 1050, "rating": "4.6", "badge": "Office Essential", "image": "https://images.unsplash.com/photo-1614252369475-531eba835eb1?auto=format&fit=crop&w=800&q=80", "desc": "Polished formal lace-up oxford with cushioned insole for office wear."},
    {"id": "BT-02", "brand": "Bata", "name": "Bata Ladies Comfit Block Heels", "category": "Ladies", "price": 1599, "cost_price": 900, "rating": "4.7", "badge": "Festive & Work", "image": "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?auto=format&fit=crop&w=800&q=80", "desc": "Balanced low block heel with anti-slip sole and padded toe bed."},
    {"id": "BT-03", "brand": "Bata", "name": "Bata Bubblegummers Kids Sneaker", "category": "Kids", "price": 1199, "cost_price": 680, "rating": "4.7", "badge": "Kids Choice", "image": "https://images.unsplash.com/photo-1514989940723-e8e51635b782?auto=format&fit=crop&w=800&q=80", "desc": "Soft cushioned collar and flexible sole crafted for school comfort."},

    # WOODLAND
    {"id": "WD-01", "brand": "Woodland", "name": "Woodland Camel Nubuck High-Top", "category": "High-Tops", "price": 3895, "cost_price": 2300, "rating": "4.8", "badge": "All-Terrain", "image": "https://images.unsplash.com/photo-1520639888713-7851133b1ed0?auto=format&fit=crop&w=800&q=80", "desc": "Genuine nubuck leather upper with rugged lugged rubber outsole."},
    {"id": "WD-02", "brand": "Woodland", "name": "Woodland Tan Leather Derby", "category": "Formal", "price": 3195, "cost_price": 1900, "rating": "4.6", "badge": "Genuine Leather", "image": "https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?auto=format&fit=crop&w=800&q=80", "desc": "Handcrafted tan leather formal derby combining polish and durability."},

    # CAMPUS
    {"id": "CM-01", "brand": "Campus", "name": "Campus North Plus Knit Runner", "category": "Running", "price": 1699, "cost_price": 950, "rating": "4.6", "badge": "Budget Runner", "image": "https://images.unsplash.com/photo-1600185365926-3a2ce3cdb9eb?auto=format&fit=crop&w=800&q=80", "desc": "Memory-foam insole with air-capsule heel for everyday runs."},
    {"id": "CM-02", "brand": "Campus", "name": "Campus Ladies Raise Casual Sneaker", "category": "Ladies", "price": 1499, "cost_price": 820, "rating": "4.7", "badge": "Lightweight", "image": "https://images.unsplash.com/photo-1587563871167-1ee9c731aefb?auto=format&fit=crop&w=800&q=80", "desc": "Featherlight women’s everyday sneaker with breathable mesh."},

    # SPARX
    {"id": "SP-01", "brand": "Sparx", "name": "Sparx SFG-549 Anti-Skid Flip-Flops", "category": "Flip-Flops", "price": 349, "cost_price": 180, "rating": "4.7", "badge": "Monsoon Grip", "image": "https://images.unsplash.com/photo-1562183241-b937e95585b6?auto=format&fit=crop&w=800&q=80", "desc": "Cushioned EVA footbed with wet-surface anti-skid grooves."},
    {"id": "SP-02", "brand": "Sparx", "name": "Sparx Ortho-Soft Home Slippers", "category": "Slippers", "price": 499, "cost_price": 250, "rating": "4.6", "badge": "Acupressure Sole", "image": "https://images.unsplash.com/photo-1603487742131-4160ec999306?auto=format&fit=crop&w=800&q=80", "desc": "Soft memory-cushion house slippers ideal for elders and indoor comfort."},

    # HUSH PUPPIES
    {"id": "HP-01", "brand": "Hush Puppies", "name": "Hush Puppies Bounce Leather Loafer", "category": "Senior Comfort", "price": 3999, "cost_price": 2350, "rating": "4.9", "badge": "Zero-Break-In", "image": "https://images.unsplash.com/photo-1533867617858-e7b97e060509?auto=format&fit=crop&w=800&q=80", "desc": "Supple full-grain leather slip-on with shock-absorbing Bounce pods."},
    {"id": "HP-02", "brand": "Hush Puppies", "name": "Hush Puppies Executive Brown Derby", "category": "Formal", "price": 4299, "cost_price": 2500, "rating": "4.8", "badge": "Premium Formal", "image": "https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?auto=format&fit=crop&w=800&q=80", "desc": "Classic executive dress derby with breathable leather lining."}
]

INITIAL_DEMO_ORDERS = [
    {"orderId": "ORD-1041", "date": "2026-11-14", "customerName": "Aarav Verma", "customerEmail": "aarav.v@example.com", "customerPhone": "9829011223", "gender": "Male", "ageGroup": "18-25", "city": "Jaipur", "brand": "Nike", "productId": "NK-01", "productName": "Nike Air Force 1 '07 Low", "category": "Sneakers", "size": "UK 9", "qty": 1, "unitPrice": 7495, "costPrice": 4500, "totalAmount": 7495, "profit": 2995, "paymentMethod": "UPI", "status": "Delivered"},
    {"orderId": "ORD-1042", "date": "2026-11-15", "customerName": "Sneha Gupta", "customerEmail": "sneha.g@example.com", "customerPhone": "9414055667", "gender": "Female", "ageGroup": "26-40", "city": "Kota", "brand": "Skechers", "productId": "SK-02", "productName": "Skechers Ladies Arch Fit Pastel", "category": "Ladies", "size": "UK 6", "qty": 1, "unitPrice": 4999, "costPrice": 2900, "totalAmount": 4999, "profit": 2099, "paymentMethod": "Credit/Debit Card", "status": "Delivered"},
    {"orderId": "ORD-1043", "date": "2026-11-16", "customerName": "Rajendra Prasad", "customerEmail": "rprasad@example.com", "customerPhone": "9828123456", "gender": "Male", "ageGroup": "55+", "city": "Udaipur", "brand": "Skechers", "productId": "SK-01", "productName": "Skechers Go Walk Flex Orthopedic", "category": "Senior Comfort", "size": "UK 8", "qty": 2, "unitPrice": 4499, "costPrice": 2600, "totalAmount": 8998, "profit": 3798, "paymentMethod": "UPI", "status": "Shipped"},
    {"orderId": "ORD-1044", "date": "2026-11-17", "customerName": "Kabir Mehta", "customerEmail": "kabir.m@example.com", "customerPhone": "9782099881", "gender": "Male", "ageGroup": "18-25", "city": "Delhi", "brand": "Crocs", "productId": "CR-01", "productName": "Crocs Classic Clog Unisex", "category": "Crocs & Clogs", "size": "UK 8", "qty": 2, "unitPrice": 3995, "costPrice": 2100, "totalAmount": 7990, "profit": 3790, "paymentMethod": "UPI", "status": "Delivered"},
    {"orderId": "ORD-1045", "date": "2026-11-18", "customerName": "Ananya Joshi", "customerEmail": "ananya.j@example.com", "customerPhone": "9660044332", "gender": "Female", "ageGroup": "18-25", "city": "Pune", "brand": "Adidas", "productId": "AD-01", "productName": "Adidas Samba OG White", "category": "Sneakers", "size": "UK 7", "qty": 1, "unitPrice": 9999, "costPrice": 6200, "totalAmount": 9999, "profit": 3799, "paymentMethod": "Credit/Debit Card", "status": "Shipped"},
    {"orderId": "ORD-1046", "date": "2026-11-19", "customerName": "Vikram Rathore", "customerEmail": "vikram.r@example.com", "customerPhone": "9461122334", "gender": "Male", "ageGroup": "26-40", "city": "Kota", "brand": "Bata", "productId": "BT-01", "productName": "Bata Ambassador Black Oxford", "category": "Formal", "size": "UK 9", "qty": 2, "unitPrice": 1799, "costPrice": 1050, "totalAmount": 3598, "profit": 1498, "paymentMethod": "Cash on Delivery", "status": "Confirmed"},
    {"orderId": "ORD-1047", "date": "2026-11-19", "customerName": "Pooja Sharma", "customerEmail": "pooja.s@example.com", "customerPhone": "9928877665", "gender": "Female", "ageGroup": "41-55", "city": "Jodhpur", "brand": "Sparx", "productId": "SP-01", "productName": "Sparx SFG-549 Anti-Skid Flip-Flops", "category": "Flip-Flops", "size": "UK 7", "qty": 3, "unitPrice": 349, "costPrice": 180, "totalAmount": 1047, "profit": 507, "paymentMethod": "UPI", "status": "Confirmed"}
]