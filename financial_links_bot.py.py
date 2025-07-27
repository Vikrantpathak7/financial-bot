import logging
import os
import sqlite3
import yfinance as yf
import requests
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# --- Constants ---
OWNER_ID = 1727394308 # <<< IMPORTANT: YOUR TELEGRAM ID
QUIZ_QUESTIONS = [
    {"question": "What does a high P/E Ratio generally signify?", "options": ["The stock is undervalued", "Investors expect high future growth", "The company has low debt"], "correct": 1, "explanation": "A high P/E ratio often indicates that investors are willing to pay a higher price for each unit of current earnings, usually because they expect earnings to grow significantly in the future."},
    {"question": "What is 'dollar-cost averaging'?", "options": ["Buying stocks only with USD", "Investing a fixed amount of money at regular intervals", "Selling stocks to average your cost basis"], "correct": 1, "explanation": "Dollar-cost averaging is an investment strategy where you invest a total sum of money in small increments over time instead of all at once. The goal is to reduce the impact of volatility."},
    {"question": "What is a 'blue-chip' stock?", "options": ["A stock that costs less than $1", "A stock from a new tech company", "A well-established, financially sound company"], "correct": 2, "explanation": "Blue-chip stocks are from large, reputable, and financially stable companies that have a long history of reliable performance."},
    {"question": "What is the primary benefit of a Systematic Investment Plan (SIP)?", "options": ["Guaranteed high returns", "Lump-sum investment profit", "Averaging cost & disciplined investing"], "correct": 2, "explanation": "SIPs help you invest regularly, which fosters discipline and averages out your purchase cost over time, reducing the risk of market timing."},
    {"question": "A mutual fund is essentially a...", "options": ["Type of savings account", "Pool of money from many investors", "Government bond"], "correct": 1, "explanation": "A mutual fund pools money from many people to invest in a diversified portfolio of stocks, bonds, or other assets."},
    {"question": "A 'bear market' is characterized by...", "options": ["Rising stock prices and optimism", "Falling stock prices and pessimism", "Volatile but stable prices"], "correct": 1, "explanation": "A bear market is a period of prolonged price declines and widespread pessimism. A 'bull market' is the opposite."},
    {"question": "The 'power of compounding' refers to...", "options": ["Earning returns on your initial investment only", "Combining different types of stocks", "Earning returns on both your principal and past returns"], "correct": 2, "explanation": "Compounding is the process where your investment returns themselves start generating their own returns, leading to exponential growth over time."}
]
FINANCIAL_LINKS =  {
    "ipo_resources": {
        "title": "🚀 IPO Resources",
        "description": "Track upcoming, live, and closed IPOs in the Indian market with these essential dashboards.",
        "links": [
            {"name": "Chittorgarh IPO Dashboard", "url": "https://www.chittorgarh.com/report/ipo-subscription-status-live-bidding-data-bse-nse/21/", "desc": "Excellent for live IPO subscription status and grey market premium (GMP) data."},
            {"name": "Zerodha IPO Dashboard", "url": "https://zerodha.com/ipo/", "desc": "A clean, user-friendly dashboard for upcoming, live, and closed IPOs."},
            {"name": "Moneycontrol IPO Center", "url": "https://www.moneycontrol.com/ipo/", "desc": "Comprehensive coverage of IPO news, analysis, and subscription data."},
            {"name": "NSE India - Upcoming Issues", "url": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo", "desc": "Official list of upcoming IPOs directly from the National Stock Exchange."},
        ]
    },
    "investment_banking": {
        "title": "🏦 Investment Banking",
        "description": "Professional-grade resources for market analysis, deal tracking, and regulatory research.",
        "links": [
            {"name": "Financial Times", "url": "https://www.ft.com/", "desc": "Global financial news, analysis, and commentary, essential for market awareness."},
            {"name": "Wall Street Journal", "url": "https://www.wsj.com/", "desc": "In-depth coverage of business, finance, and global markets."},
            {"name": "SEBI", "url": "https://www.sebi.gov.in/", "desc": "Securities and Exchange Board of India, for all Indian market regulations and filings."},
            {"name": "Ministry of Corporate Affairs (MCA)", "url": "https://www.mca.gov.in/", "desc": "Portal for accessing Indian corporate filings and data."},
            {"name": "SEC EDGAR", "url": "https://www.sec.gov/edgar/searchedgar/companysearch", "desc": "Database of all filings for US-listed companies, crucial for M&A research."},
            {"name": "Damodaran Online", "url": "http://pages.stern.nyu.edu/~adamodar/", "desc": "Prof. Aswath Damodaran's site, a top resource for valuation models and data."},
            {"name": "PitchBook", "url": "https://pitchbook.com/", "desc": "Leading data provider for M&A, private equity, and venture capital deals."},
            {"name": "Mergermarket", "url": "https://www.mergermarket.com/", "desc": "Provides forward-looking intelligence, data, and analysis on M&A."},
        ]
    },
    "investing": {
        "title": "📈 General Investing",
        "description": "Learn the fundamentals of investing and analyze stocks with these powerful tools.",
        "links": [
            {"name": "Investopedia", "url": "https://www.investopedia.com/", "desc": "An excellent resource for learning about investing concepts, financial terms, and market analysis."},
            {"name": "Zerodha Varsity", "url": "https://zerodha.com/varsity/", "desc": "A comprehensive and easy-to-understand guide to the Indian stock market."},
            {"name": "Screener.in", "url": "https://www.screener.in/", "desc": "A powerful stock analysis and screening tool for Indian stocks."},
            {"name": "TradingView", "url": "https://in.tradingview.com/", "desc": "Advanced charting tools and a social network for traders and investors."},
            {"name": "Morningstar India", "url": "https://www.morningstar.in/", "desc": "Provides independent investment research, including fund and stock analysis."},
        ]
    },
    "news": {
        "title": "📰 Financial News",
        "description": "Stay updated with the latest news from the financial world.",
        "links": [
            {"name": "The Economic Times Markets", "url": "https://economictimes.indiatimes.com/markets", "desc": "Top source for business news and financial markets in India."},
            {"name": "Livemint", "url": "https://www.livemint.com/", "desc": "In-depth coverage of business, finance, and policy news."},
            {"name": "Bloomberg Quint", "url": "https://www.bqprime.com/", "desc": "A leading business and financial news company in India."},
            {"name": "Reuters - Business & Finance", "url": "https://www.reuters.com/business/finance/", "desc": "Global financial news from one of the world's largest news agencies."},
        ]
    },
    "budgeting": {
        "title": "💰 Budgeting & Personal Finance",
        "description": "Tools and resources to help you manage your money and achieve financial goals.",
        "links": [
            {"name": "YNAB (You Need A Budget)", "url": "https://www.youneedabudget.com/", "desc": "A popular budgeting app and philosophy to help you gain control of your money."},
            {"name": "Mint", "url": "https://mint.intuit.com/", "desc": "A free app to track your spending, create budgets, and monitor your credit score."},
            {"name": "RBI - Financial Education", "url": "https://rbi.org.in/financialeducation/home.aspx", "desc": "Resources from the Reserve Bank of India on financial literacy."},
        ]
    },
    "taxes": {
        "title": "🧾 Taxes",
        "description": "Official portals and helpful resources for managing your taxes in India.",
        "links": [
            {"name": "Income Tax Department", "url": "https://www.incometax.gov.in/iec/foportal/", "desc": "The official portal for e-filing income tax returns in India."},
            {"name": "ClearTax", "url": "https://cleartax.in/", "desc": "A popular platform for tax filing, information, and expert assistance."},
            {"name": "Taxmann", "url": "https://www.taxmann.com/", "desc": "A leading source for resources on tax and corporate laws in India."},
        ]
    },
    "retirement": {
        "title": "🏖️ Retirement Planning",
        "description": "Plan for your future with these essential retirement resources.",
        "links": [
            {"name": "NPS Trust", "url": "http://www.npstrust.org.in/", "desc": "Official website for the National Pension System (NPS) in India."},
            {"name": "EPFO India", "url": "https://www.epfindia.gov.in/site_en/", "desc": "Official portal for the Employees' Provident Fund Organisation."},
            {"name": "Value Research - Pension", "url": "https://www.valueresearchonline.com/pension/", "desc": "Articles and tools related to retirement planning and pension funds."},
        ]
    },
    "real_estate": {
        "title": "🏠 Real Estate",
        "description": "Leading portals for buying, selling, and researching properties in India.",
        "links": [
            {"name": "MagicBricks", "url": "https://www.magicbricks.com/", "desc": "One of India's leading property portals for buying, selling, and renting."},
            {"name": "99acres", "url": "https://www.99acres.com/", "desc": "A major real estate portal for property search and information."},
            {"name": "Housing.com", "url": "https://housing.com/", "desc": "A platform for finding properties, with detailed locality information."},
        ]
    },
    "tools": {
        "title": "🛠️ Financial Tools",
        "description": "A collection of powerful calculators for all your financial planning needs.",
        "links": [
            {"name": "ET Money Calculators", "url": "https://www.etmoney.com/calculators", "desc": "A comprehensive suite of financial calculators for various needs."},
            {"name": "Groww Calculators", "url": "https://groww.in/calculators", "desc": "Easy-to-use calculators for SIP, lumpsum, brokerage, and more."},
            {"name": "Value Research Calculators", "url": "https://www.valueresearchonline.com/calculators/", "desc": "A wide range of calculators for mutual funds, insurance, and other investments."},
        ]
    },
    "crypto": {
        "title": "🪙 Cryptocurrency",
        "description": "Resources for news, tracking, and education on cryptocurrencies.",
        "links": [
            {"name": "CoinDesk", "url": "https://www.coindesk.com/", "desc": "A leading news site specializing in bitcoin and digital currencies."},
            {"name": "CoinMarketCap", "url": "https://coinmarketcap.com/", "desc": "Provides real-time market capitalization, pricing, and charts for cryptocurrencies."},
            {"name": "Binance Academy", "url": "https://academy.binance.com/en", "desc": "A free educational platform for learning about blockchain and cryptocurrency."},
        ]
    }
}

# --- Database Setup & Helpers ---
def db_query(query: str, params: tuple = ()):
    conn = sqlite3.connect("bot_users.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.commit()
    conn.close()
    return result

def setup_database():
    db_query("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_seen TEXT)")
    db_query("""
        CREATE TABLE IF NOT EXISTS watchlist (
            watchlist_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            ticker_symbol TEXT NOT NULL, UNIQUE(user_id, ticker_symbol)
        )""")

def log_user(user):
    if user: db_query("INSERT OR IGNORE INTO users (user_id, username, first_seen) VALUES (?, ?, datetime('now'))", (user.id, user.username))

async def cleanup_previous_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Deletes the last main message sent by the bot."""
    if 'last_message_id' in context.user_data:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data.pop('last_message_id'))
        except BadRequest as e:
            logging.warning(f"Could not delete message: {e}")

# --- UI & Formatting Helper Functions ---
def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    # <<< UPDATED: Helper function for reusability >>>
    keyboard = [
        [InlineKeyboardButton("📚 Financial Resources", callback_data="show_resources_menu")],
        [InlineKeyboardButton("📈 Live Market Data", callback_data="show_market_menu")],
        [InlineKeyboardButton("👀 My Watchlist", callback_data="show_watchlist")],
        [InlineKeyboardButton("🛠️ More Tools", callback_data="show_more_tools")]
    ]
    return InlineKeyboardMarkup(keyboard)

def is_in_watchlist(user_id: int, ticker_symbol: str) -> bool:
    res = db_query("SELECT 1 FROM watchlist WHERE user_id = ? AND ticker_symbol = ?", (user_id, ticker_symbol))
    return bool(res)

def create_stock_details_keyboard(ticker_symbol: str, user_id: int) -> InlineKeyboardMarkup:
    summary_url = f"https://finance.yahoo.com/quote/{ticker_symbol}"
    if is_in_watchlist(user_id, ticker_symbol):
        watchlist_button = InlineKeyboardButton("➖ Remove from Watchlist", callback_data=f"remove_from_details_{ticker_symbol}")
    else:
        watchlist_button = InlineKeyboardButton("➕ Add to Watchlist", callback_data=f"add_from_details_{ticker_symbol}")
    keyboard = [[InlineKeyboardButton("📊 Full Report (Yahoo Finance)", url=summary_url)], [watchlist_button], [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)

async def get_stock_price_message(ticker_symbol: str) -> str:
    try:
        info = yf.Ticker(ticker_symbol).info
        current_price = info.get('regularMarketPrice')
        if current_price is None: return f"Could not find data for `'{ticker_symbol}'`."
        currency_code = info.get('currency', ''); display_symbol = {'INR': '₹', 'USD': '$'}.get(currency_code, currency_code)
        company_name = info.get('longName', 'N/A'); change = info.get('regularMarketChange', 0); percent_change = info.get('regularMarketChangePercent', 0) * 100
        emoji = "📈" if change >= 0 else "📉"
        return (f"**{company_name} ({ticker_symbol})** {emoji}\n\n"
                f"**Live Price:** {display_symbol}{current_price:,.2f}\n"
                f"**Change:** {change:+.2f} ({percent_change:+.2f}%)\n\n"
                f"Click buttons below for a full report or to manage your watchlist.")
    except Exception as e:
        logging.error(f"Error in get_stock_price_message: {e}")
        return "Sorry, an error occurred while fetching the price."

# --- Main Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user = update.effective_user
    if user: log_user(user)

    await cleanup_previous_message(context, chat_id)
    
    reply_markup = get_main_menu_keyboard() # <<< UPDATED: Use helper
    welcome_text = "Welcome to **Zenith Finance**! 🧭\n\nYour trusted guide to the financial world. Please select an option to begin:"
    
    sent_message = await context.bot.send_message(chat_id=chat_id, text=welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    context.user_data['last_message_id'] = sent_message.message_id
    
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # <<< NEW: Owner-only command for bot statistics >>>
    """Shows bot usage statistics (owner only)."""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Sorry, this is an admin-only command.")
        return

    try:
        user_count_result = db_query("SELECT COUNT(*) FROM users;")
        user_count = user_count_result[0][0] if user_count_result else 0
        message = f"📊 **Bot Statistics**\n\nTotal Unique Users: `{user_count}`"
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error in stats_command: {e}")
        await update.message.reply_text("An error occurred while fetching stats.")

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await cleanup_previous_message(context, chat_id)
    
    if not context.args:
        sent_message = await update.message.reply_text("Usage: `/search <company name>`")
        context.user_data['last_message_id'] = sent_message.message_id
        return
        
    search_term = " ".join(context.args)
    sent_message = await update.message.reply_text(f"Searching for '{search_term}'...")
    try:
        response = requests.get(f"https://query1.finance.yahoo.com/v1/finance/search?q={search_term}", headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        quotes = response.json().get('quotes', [])
        if not quotes:
            await sent_message.edit_text(f"No results found for '{search_term}'.")
            return
        
        keyboard = []
        for q in quotes[:5]:
            symbol = q.get('symbol'); name = q.get('longname', 'N/A')
            if not symbol: continue
            keyboard.append([
                InlineKeyboardButton(f"{symbol} ({name[:25]})", callback_data=f"price_{symbol}"),
                InlineKeyboardButton("➕", callback_data=f"add_from_search_{symbol}")
            ])
        await sent_message.edit_text(f"Top results for '{search_term}':", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await sent_message.edit_text("Search service unavailable.")
    context.user_data['last_message_id'] = sent_message.message_id

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await cleanup_previous_message(context, chat_id)
    
    if not context.args:
        sent_message = await update.message.reply_text("Usage: `/price <TICKER>`")
        context.user_data['last_message_id'] = sent_message.message_id
        return
        
    ticker = " ".join(context.args).upper(); user_id = update.effective_user.id
    sent_message = await update.message.reply_text(f"Fetching data for `{ticker}`...", parse_mode='Markdown')
    message_text = await get_stock_price_message(ticker)
    await sent_message.edit_text(message_text, parse_mode='Markdown', reply_markup=create_stock_details_keyboard(ticker, user_id))
    context.user_data['last_message_id'] = sent_message.message_id

async def show_watchlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    query = update.callback_query
    
    if query: 
        await query.edit_message_text("Fetching your watchlist... ⏳")
    else: 
        await update.message.reply_text("Fetching your watchlist... ⏳")
    
    tickers = [row[0] for row in db_query("SELECT ticker_symbol FROM watchlist WHERE user_id = ?", (user_id,))]
    
    if not tickers:
        text = "Your watchlist is empty. Add stocks using the `/search` command."
        keyboard = [[InlineKeyboardButton("🔍 Search for a Stock", callback_data="show_market_menu")], [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="main_menu")]]
        if query:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    report_lines = ["**Your Watchlist Summary**\n"]
    keyboard = []
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            price = info.get('regularMarketPrice', 'N/A')
            change_pct = info.get('regularMarketChangePercent', 0) * 100
            currency_code = info.get('currency', '')
            display_symbol = {'INR': '₹', 'USD': '$'}.get(currency_code, currency_code)
            emoji = "📈" if change_pct >= 0 else "📉"
            report_lines.append(f"• `{ticker}`: {display_symbol}{price:,.2f} ({change_pct:+.2f}%) {emoji}")
            keyboard.append([InlineKeyboardButton(f"➖ Remove {ticker}", callback_data=f"remove_from_list_{ticker}")])
            await asyncio.sleep(0.1) # Be respectful to the API
        except: 
            report_lines.append(f"• `{ticker}`: Error fetching data")
    
    keyboard.append([InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="main_menu")])
    final_text = "\n".join(report_lines)
    if query:
        await query.edit_message_text(final_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # <<< UPDATED: Overhauled quiz logic >>>
    query = update.callback_query
    chat_id = update.effective_chat.id

    # Initialize or get the list of unasked question indices
    if 'unasked_quiz_indices' not in context.user_data or not context.user_data['unasked_quiz_indices']:
        indices = list(range(len(QUIZ_QUESTIONS)))
        random.shuffle(indices)
        context.user_data['unasked_quiz_indices'] = indices

    unasked_indices = context.user_data['unasked_quiz_indices']

    # Check if all questions have been asked
    if not unasked_indices:
        text = "🎉 **Quiz Complete!**\n\nYou've answered all the questions. Well done!"
        reply_markup = get_main_menu_keyboard()
        if query:
            await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        else: # Should not happen with buttons, but good practice
            await context.bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=reply_markup)
        # Clean up quiz data for the next round
        context.user_data.pop('unasked_quiz_indices', None)
        return

    # Pop the next question index to ensure it's not asked again
    question_index = unasked_indices.pop()
    question_data = QUIZ_QUESTIONS[question_index]

    context.user_data['correct_answer_index'] = question_data['correct']
    context.user_data['explanation'] = question_data['explanation']
    
    buttons = [[InlineKeyboardButton(option, callback_data=f"quiz_{i}")] for i, option in enumerate(question_data['options'])]
    reply_markup = InlineKeyboardMarkup(buttons)
    message_text = f"**Financial Quiz!** ({len(QUIZ_QUESTIONS) - len(unasked_indices)}/{len(QUIZ_QUESTIONS)})\n\n{question_data['question']}"
    
    if query:
        await query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await cleanup_previous_message(context, chat_id)
        sent_message = await context.bot.send_message(chat_id, message_text, reply_markup=reply_markup, parse_mode='Markdown')
        context.user_data['last_message_id'] = sent_message.message_id

# --- The Main Router for All Button Clicks ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    key = query.data
    user_id = query.from_user.id
    
    if key == "main_menu":
        await start(update, context)
        return

    if key == "start_quiz": # <<< UPDATED: Route to the new quiz function
        await start_quiz(update, context)
        return
        
    if key.startswith("price_"):
        ticker = key.split('_', 1)[1]
        await query.edit_message_text(f"Fetching price for `{ticker}`...", parse_mode='Markdown')
        message_text = await get_stock_price_message(ticker)
        await query.edit_message_text(text=message_text, parse_mode='Markdown', reply_markup=create_stock_details_keyboard(ticker, user_id))
    
    elif key.startswith("add_from_search_"):
        ticker = key.split('_', 3)[3]
        db_query("INSERT OR IGNORE INTO watchlist (user_id, ticker_symbol) VALUES (?, ?)", (user_id, ticker))
        await query.answer(f"✅ {ticker} added to Watchlist!")
        new_keyboard = []
        for row in query.message.reply_markup.inline_keyboard:
            price_button, add_button = row
            if add_button.callback_data == key:
                new_keyboard.append([price_button])
            else:
                new_keyboard.append(row)
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(new_keyboard))

    elif key.startswith("add_from_details_"):
        ticker = key.split('_', 3)[3]
        db_query("INSERT OR IGNORE INTO watchlist (user_id, ticker_symbol) VALUES (?, ?)", (user_id, ticker))
        await query.answer("✅ Added to Watchlist!")
        await query.edit_message_reply_markup(reply_markup=create_stock_details_keyboard(ticker, user_id))

    elif key.startswith("remove_from_details_"):
        ticker = key.split('_', 3)[3]
        db_query("DELETE FROM watchlist WHERE user_id = ? AND ticker_symbol = ?", (user_id, ticker))
        await query.answer("🗑️ Removed from Watchlist!")
        await query.edit_message_reply_markup(reply_markup=create_stock_details_keyboard(ticker, user_id))

    elif key.startswith("remove_from_list_"):
        ticker = key.split('_', 3)[3]
        db_query("DELETE FROM watchlist WHERE user_id = ? AND ticker_symbol = ?", (user_id, ticker))
        await query.answer(f"🗑️ {ticker} removed!")
        await show_watchlist_command(update, context)

    elif key.startswith("quiz_"):
        user_answer = int(key.split('_')[1])
        correct_answer = context.user_data.get('correct_answer_index')
        explanation = context.user_data.get('explanation')
        text = f"✅ **Correct!**\n\n_{explanation}_" if user_answer == correct_answer else f"❌ **Not Quite...**\n\n_{explanation}_"
        keyboard = [[InlineKeyboardButton("Next Question ➡️", callback_data="start_quiz")], [InlineKeyboardButton("⬅️ Back to Tools", callback_data="show_more_tools")]]
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif key == "show_watchlist": await show_watchlist_command(update, context)
    
    elif key == "show_more_tools":
        # Reset quiz progress if user navigates back to tools
        context.user_data.pop('unasked_quiz_indices', None) 
        keyboard = [
            [InlineKeyboardButton("🚀 Market Movers (Moneycontrol)", url="https://www.moneycontrol.com/stocks/marketstats/nsegainer/index.php")],
            [InlineKeyboardButton("🧠 Financial Quiz", callback_data="start_quiz")], # <<< UPDATED: This now resets the quiz
            [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="main_menu")]
        ]
        await query.edit_message_text("🛠️ **More Tools**\n\nSelect a tool to use:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif key == "show_market_menu":
        keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="main_menu")]]
        message = (
            "📈 **Live Market Data**\n\n"
            "Use `/search <company name>` to find a stock symbol.\n"
            "**Example:** `/search Apple`\n\n"
            "If you already know the symbol, use `/price <symbol>`.\n"
            "**Example:** `/price AAPL`"
        )
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        
    elif key == "show_resources_menu":
        keyboard = [[InlineKeyboardButton(FINANCIAL_LINKS[k]["title"], callback_data=k)] for k in sorted(FINANCIAL_LINKS.keys())]
        keyboard.append([InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="main_menu")])
        await query.edit_message_text("📚 **Financial Resources**\n\nSelect a category to explore:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif key in FINANCIAL_LINKS:
        category = FINANCIAL_LINKS[key]
        message = f"**{category['title']}**\n_{category['description']}_\n\n"
        for link in category["links"]:
            message += f"🔗 [{link['name']}]({link['url']}) - {link['desc']}\n"
        keyboard = [[InlineKeyboardButton("⬅️ Back to Resources", callback_data="show_resources_menu")]]
        await query.edit_message_text(text=message, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)

# --- Bot Startup ---
def main() -> None:
    # Use environment variable for token, with a placeholder for local testing
    TOKEN = os.environ.get("BOT_TOKEN", "8035433844:AAEVK7XMtfgrGFj__kInF0yCr3KuPdx6JEk")
    if TOKEN == "8035433844:AAEVK7XMtfgrGFj__kInF0yCr3KuPdx6JEk":
        logging.warning("Using a placeholder Bot Token. Please set the BOT_TOKEN environment variable.")
        
    application = Application.builder().token(TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats_command)) # <<< NEW: Added stats handler
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(CommandHandler("watchlist", show_watchlist_command))
    # application.add_handler(CommandHandler("quiz", start_quiz)) # optional: allow starting quiz with /quiz
    
    # Register the main callback handler for all buttons
    application.add_handler(CallbackQueryHandler(button_handler))

    # Set up the database and run the bot
    setup_database()
    application.run_polling()

if __name__ == "__main__":
    main()
