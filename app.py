import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime

st.set_page_config(page_title="શ્રી મણિધર એન્જિનિયરિંગ", layout="wide")

FACTORY_NAME = "શ્રી મણિધર એન્જિનિયરિંગ"
FACTORY_ADDRESS = "A/1 શ્રી હરિ એસ્ટેટ, ત્રિભુવન એસ્ટેટ ની બાજુમાં, લાલ બહાદુર શાસ્ત્રી રોડ, નરોડા મેમકો"

conn = sqlite3.connect('manidhar_db.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no TEXT,
    date TEXT,
    party_name TEXT,
    party_mobile TEXT,
    party_gst TEXT,
    is_gst_bill INTEGER,
    my_gst TEXT,
    item_name TEXT,
    qty REAL,
    rate REAL,
    base_amount REAL,
    gst_percent REAL,
    gst_amount REAL,
    total_amount REAL,
    payment_mode TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS party_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    party_name TEXT,
    txn_type TEXT,
    amount REAL,
    note TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    category TEXT,
    amount REAL,
    paid_by TEXT,
    note TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    daily_wage REAL
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS worker_attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    worker_name TEXT,
    attendance TEXT,
    advance REAL
)''')
conn.commit()

st.sidebar.markdown(f"## 🏭 {FACTORY_NAME}")
st.sidebar.caption(FACTORY_ADDRESS)

menu = st.sidebar.radio("મેનુ પસંદ કરો:", [
    "🧾 નવું બિલ બનાવો & પ્રિન્ટ",
    "📑 પાર્ટી વાઇઝ માસિક હિસાબ (ખાતાવહી)",
    "☕ પરચુરણ ખર્ચ (ચા-પાણી/રિપેરિંગ)",
    "👷 કારીગર હાજરી & ઉપાડ",
    "📊 આજનો મેળ (Dashboard)"
])

if menu == "🧾 નવું બિલ બનાવો & પ્રિન્ટ":
    st.subheader("🧾 નવું બિલિંગ (Invoice Generator)")

    with st.form("bill_form"):
        col1, col2 = st.columns(2)
        inv_no = f"SME-{datetime.now().strftime('%y%m%d%H%M')}"
        b_date = col1.date_input("બિલ તારીખ", date.today())
        party = col2.text_input("ગ્રાહક / પાર્ટીનું નામ *")
        mobile = col1.text_input("પાર્ટીનો મોબાઈલ નંબર")
        
        st.markdown("---")
        is_gst = st.radio("આ બિલમાં જીએસટી (GST) લગાવવો છે?", ["ના (સાદું બિલ / Non-GST)", "હા (GST સાથેનું બિલ)"], horizontal=True)
        
        my_gst_val = ""
        party_gst_val = ""
        gst_pct = 0.0

        if is_gst == "હા (GST સાથેનું બિલ)":
            gcol1, gcol2, gcol3 = st.columns(3)
            my_gst_val = gcol1.text_input("તમારો GST નંબર", placeholder="24AAAAA0000A1Z5")
            party_gst_val = gcol2.text_input("પાર્ટીનો GST નંબર (જો હોય તો)")
            gst_pct = gcol3.selectbox("GST ટકાવારી (%)", [18.0, 12.0, 5.0, 28.0])

        st.markdown("---")
        item = st.text_input("કામ / પ્રોડક્ટની વિગત (Item Description) *")
        
        col3, col4 = st.columns(2)
        qty = col3.number_input("નંગ / ક્વોન્ટિટી", min_value=1.0, value=1.0)
        rate = col4.number_input("ભાવ (દર નંગ ₹)", min_value=0.0, value=500.0)
        
        base_amt = qty * rate
        gst_amt = (base_amt * gst_pct / 100.0) if is_gst == "હા (GST સાથેનું બિલ)" else 0.0
        final_total = base_amt + gst_amt
        
        if is_gst == "હા (GST સાથેનું બિલ)":
            st.info(f"પાયાની રકમ: ₹ {base_amt:,.2f} | GST ({gst_pct}%): ₹ {gst_amt:,.2f} | **કુલ બિલ રકમ: ₹ {final_total:,.2f}**")
        else:
            st.info(f"**કુલ બિલ રકમ: ₹ {final_total:,.2f}**")
            
        pay_mode = st.selectbox("ચુકવણીનો પ્રકાર", ["બાકી (ઉધાર)", "રોકડ (Cash)", "ઓનલાઇન / બેંક (GPay/NEFT)"])
        btn_save = st.form_submit_button("💾 બિલ સેવ કરો અને પ્રિન્ટ તૈયાર કરો")

    if btn_save and party and item:
        cursor.execute('''INSERT INTO invoices 
            (invoice_no, date, party_name, party_mobile, party_gst, is_gst_bill, my_gst, item_name, qty, rate, base_amount, gst_percent, gst_amount, total_amount, payment_mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (inv_no, str(b_date), party, mobile, party_gst_val, 1 if "હા" in is_gst else 0, my_gst_val, item, qty, rate, base_amt, gst_pct, gst_amt, final_total, pay_mode))
        
        cursor.execute("INSERT INTO party_ledger (date, party_name, txn_type, amount, note) VALUES (?, ?, 'ઉધાર (Bill)', ?, ?)",
                       (str(b_date), party, final_total, f"Bill #{inv_no}"))
        
        if pay_mode != "બાકી (ઉધાર)":
            cursor.execute("INSERT INTO party_ledger (date, party_name, txn_type, amount, note) VALUES (?, ?, 'જમા (Paid)', ?, ?)",
                           (str(b_date), party, final_total, f"Paid via {pay_mode}"))
        conn.commit()
        st.success("✅ બિલ સફળતાપૂર્વક બની ગયું!")

        bill_title = "TAX INVOICE" if "હા" in is_gst else "ESTIMATE / CASH MEMO"
        gst_html_header = f"<p style='margin: 2px 0; font-size: 13px;'><b>GSTIN:</b> {my_gst_val}</p>" if my_gst_val else ""
        party_gst_html = f"<br><b>GSTIN:</b> {party_gst_val}" if party_gst_val else ""
        gst_table_header = "<th style='padding: 6px; text-align: right;'>GST</th>" if gst_amt > 0 else ""
        gst_table_row = f"<td style='padding: 8px 6px; text-align: right;'>{gst_pct}% (₹{gst_amt:,.2f})</td>" if gst_amt > 0 else ""

        bill_html = f"""
        <div id="printArea" style="border: 2px solid #000; padding: 20px; font-family: 'Segoe UI', Tahoma, sans-serif; background: #fff; color: #000; max-width: 600px; margin: auto; border-radius: 6px;">
            <div style="text-align: center; border-bottom: 2px solid #000; padding-bottom: 8px;">
                <span style="font-size: 12px; font-weight: bold; border: 1px solid #000; padding: 2px 8px; border-radius: 4px;">{bill_title}</span>
                <h2 style="margin: 8px 0 2px 0; color: #0d47a1;">{FACTORY_NAME}</h2>
                <p style="margin: 2px 0; font-size: 12px; line-height: 1.4;">{FACTORY_ADDRESS}</p>
                {gst_html_header}
            </div>
            
            <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 13px; border-bottom: 1px solid #ccc; padding-bottom: 8px;">
                <div>
                    <b>બિલ નં:</b> {inv_no}<br>
                    <b>તારીખ:</b> {b_date}
                </div>
                <div style="text-align: right;">
                    <b>ગ્રાહક:</b> {party}<br>
                    <b>ફોન:</b> {mobile}
                    {party_gst_html}
                </div>
            </div>

            <table style="width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13px;">
                <thead>
                    <tr style="background: #f1f1f1; border-top: 1px solid #000; border-bottom: 1px solid #000;">
                        <th style="padding: 6px; text-align: left;">વિગત</th>
                        <th style="padding: 6px; text-align: center;">નંગ</th>
                        <th style="padding: 6px; text-align: right;">ભાવ</th>
                        {gst_table_header}
                        <th style="padding: 6px; text-align: right;">કુલ (₹)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom: 1px solid #ddd;">
                        <td style="padding: 8px 6px;">{item}</td>
                        <td style="padding: 8px 6px; text-align: center;">{qty}</td>
                        <td style="padding: 8px 6px; text-align: right;">₹{rate:,.2f}</td>
                        {gst_table_row}
                        <td style="padding: 8px 6px; text-align: right; font-weight: bold;">₹{final_total:,.2f}</td>
                    </tr>
                </tbody>
            </table>

            <div style="text-align: right; margin-top: 15px; font-size: 15px;">
                <b>ચૂકવવાપાત્ર કુલ રકમ: ₹ {final_total:,.2f}</b><br>
                <small style="font-size: 12px; color: #555;">પેમેન્ટ સ્થિતિ: {pay_mode}</small>
            </div>
            
            <div style="margin-top: 40px; display: flex; justify-content: space-between; font-size: 12px;">
                <div>ગ્રાહકની સહી</div>
                <div style="text-align: right;">
                    <b>શ્રી મણિધર એન્જિનિયરિંગ</b><br><br><br>
                    સત્તાવાર સહી
                </div>
            </div>
        </div>
        <br>
        <div style="text-align: center;">
            <button onclick="window.print()" style="padding: 12px 28px; font-size: 16px; background-color: #0d47a1; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">
                🖨️ બિલ પ્રિન્ટ કરો / PDF ડાઉનલોડ
            </button>
        </div>
        """
        st.components.v1.html(bill_html, height=580, scrolling=True)

elif menu == "📑 પાર્ટી વાઇઝ માસિક હિસાબ (ખાતાવહી)":
    st.subheader("📑 પાર્ટી વાઇઝ માસિક ખાતાવહી & સ્ટેટમેન્ટ")
    parties = [p[0] for p in cursor.execute("SELECT DISTINCT party_name FROM party_ledger").fetchall()]
    
    if parties:
        sel_party = st.selectbox("પાર્ટી પસંદ કરો:", parties)
        df_party = pd.read_sql(f"SELECT date as 'તારીખ', txn_type as 'પ્રકાર', amount as 'રકમ (₹)', note as 'વિગત' FROM party_ledger WHERE party_name = '{sel_party}' ORDER BY date DESC", conn)
        
        tot_udhar = df_party[df_party['પ્રકાર'].str.contains('ઉધાર')]['રકમ (₹)'].sum()
        tot_jama = df_party[df_party['પ્રકાર'].str.contains('જમા')]['રકમ (₹)'].sum()
        balance = tot_udhar - tot_jama
        
        col1, col2, col3 = st.columns(3)
        col1.metric("કુલ માલ લીધો", f"₹ {tot_udhar:,.2f}")
        col2.metric("કુલ ચૂકવેલ (જમા)", f"₹ {tot_jama:,.2f}")
        col3.metric("બાકી નીકળતી રકમ", f"₹ {balance:,.2f}", delta_color="inverse")
        
        st.write("### લેવડ-દેવડની વિગત (સ્ટેટમેન્ટ):")
        st.dataframe(df_party, use_container_width=True)
        
        with st.expander("➕ આ પાર્ટી પાસેથી રૂપિયા જમા લેવા (Payment Entry)"):
            with st.form("party_pay"):
                p_date = st.date_input("તારીખ", date.today())
                p_amt = st.number_input("મળેલી રકમ (₹)", min_value=1.0)
                p_rem = st.text_input("વિગત (દા.ત. રોકડા આપ્યા / GPay)")
                if st.form_submit_button("જમા કરો"):
                    cursor.execute("INSERT INTO party_ledger (date, party_name, txn_type, amount, note) VALUES (?, ?, 'જમા (Paid)', ?, ?)",
                                   (str(p_date), sel_party, p_amt, p_rem))
                    conn.commit()
                    st.success("જમા એન્ટ્રી સફળ થઈ ગઈ!")
                    st.rerun()
    else:
        st.info("હજુ સુધી કોઈ પાર્ટી સાથે વ્યવહાર નોંધાયો નથી.")

elif menu == "☕ પરચુરણ ખર્ચ (ચા-પાણી/રિપેરિંગ)":
    st.subheader("☕ રોજિંદો પરચુરણ ખર્ચ (Petty Cash)")
    with st.form("exp_form"):
        e_date = st.date_input("તારીખ", date.today())
        cat = st.selectbox("ખર્ચ શેનો થયો?", ["ચા-પાણી & નાસ્તો", "લેથ / મશીનરી રિપેરિંગ & ઓઇલ", "ટેમ્પો / ટ્રાન્સપોર્ટ ભાડું", "હાર્ડવેર / ટૂલ્સ ખરીદી", "લાઈટ બિલ / ફેક્ટરી પરચુરણ"])
        amt = st.number_input("રકમ (₹)", min_value=1.0)
        paid_from = st.selectbox("ચૂકવણી મોડ", ["Cash (રોકડ)", "Online / UPI"])
        note = st.text_input("વિગત / કોને આપ્યા")
        if st.form_submit_button("ખર્ચ સેવ કરો"):
            cursor.execute("INSERT INTO expenses (date, category, amount, paid_by, note) VALUES (?, ?, ?, ?, ?)",
                           (str(e_date), cat, amt, paid_from, note))
            conn.commit()
            st.success("ખર્ચ નોંધાઈ ગયો!")

    st.subheader("આજના ખર્ચાનું લિસ્ટ")
    df_exp = pd.read_sql(f"SELECT date as 'તારીખ', category as 'ખર્ચ', amount as 'રકમ', note as 'નોંધ' FROM expenses ORDER BY id DESC LIMIT 10", conn)
    st.dataframe(df_exp, use_container_width=True)

elif menu == "👷 કારીગર હાજરી & ઉપાડ":
    st.subheader("👷 કારીગરોનો હિસાબ")
    
    t1, t2 = st.tabs(["હાજરી & ઉપાડ એન્ટ્રી", "નવો કારીગર ઉમેરો"])
    with t2:
        with st.form("worker_add"):
            w_name = st.text_input("કારીગરનું પૂરું નામ")
            w_wage = st.number_input("રોજિંદો પગાર / દિહાડી દર (₹)", min_value=0.0)
            if st.form_submit_button("કારીગર સેવ કરો") and w_name:
                try:
                    cursor.execute("INSERT INTO workers (name, daily_wage) VALUES (?, ?)", (w_name, w_wage))
                    conn.commit()
                    st.success("કારીગર ઉમેરાઈ ગયો!")
                except:
                    st.error("આ કારીગર પહેલેથી મોજૂદ છે.")

    with t1:
        w_list = [w[0] for w in cursor.execute("SELECT name FROM workers").fetchall()]
        if w_list:
            with st.form("att_entry"):
                a_date = st.date_input("તારીખ", date.today())
                a_worker = st.selectbox("કારીગર", w_list)
                a_status = st.selectbox("હાજરી", ["હાજર (Full Day)", "અડધો દિવસ (Half Day)", "ગેરહાજર (Absent)"])
                a_adv = st.number_input("આજે ઉપાડ લીધો હોય તો રકમ (₹)", min_value=0.0)
                if st.form_submit_button("હાજરી & ઉપાડ નોંધો"):
                    cursor.execute("INSERT INTO worker_attendance (date, worker_name, attendance, advance) VALUES (?, ?, ?, ?)",
                                   (str(a_date), a_worker, a_status, a_adv))
                    conn.commit()
                    st.success("એન્ટ્રી સેવ થઈ ગઈ!")
        else:
            st.info("પહેલા બાજુના ટેબમાંથી કારીગરનું નામ ઉમેરો.")

elif menu == "📊 આજનો મેળ (Dashboard)":
    st.subheader("📊 ફેક્ટરી સમરી & રોજમેળ")
    today = str(date.today())
    
    t_sales = pd.read_sql(f"SELECT SUM(total_amount) FROM invoices WHERE date='{today}'", conn).iloc[0,0] or 0.0
    t_exp = pd.read_sql(f"SELECT SUM(amount) FROM expenses WHERE date='{today}'", conn).iloc[0,0] or 0.0
    
    c1, c2 = st.columns(2)
    c1.metric("આજનું કુલ વેચાણ (બિલિંગ)", f"₹ {t_sales:,.2f}")
    c2.metric("આજનો કુલ પરચુરણ ખર્ચ", f"₹ {t_exp:,.2f}")
