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