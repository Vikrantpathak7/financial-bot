import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- Financial Resources ---
# Each category now has an emoji and a 'description' to guide the user.
FINANCIAL_LINKS = {
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

# --- Telegram Bot Commands ---

# ***** EDITED FUNCTION *****
# The 'start' function now accepts either an 'Update' or a 'CallbackQuery' object.
# This makes it flexible enough to be called by a command (/start) or a button press ("Back to Main Menu").
async def start(update: Update | CallbackQuery, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message with a menu of categories."""
    keyboard = []
    # Create a button for each category, sorted for consistency
    sorted_keys = sorted(FINANCIAL_LINKS.keys())
    for key in sorted_keys:
        button = InlineKeyboardButton(FINANCIAL_LINKS[key]["title"], callback_data=key)
        keyboard.append([button]) # Each button on its own row

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "Welcome to **Zenith Finance**! 🧭\n\n"
        "Your trusted guide to the financial world. I provide curated links to the best resources for investing, market news, and personal finance.\n\n"
        "Please select a category below to get started:"
    )
    
    # This logic checks what kind of object 'update' is.
    if isinstance(update, CallbackQuery):
        # This block runs if 'start' was called from a button press.
        # 'update' is the CallbackQuery object itself.
        query = update
        await query.answer() # Acknowledge the button press
        await query.edit_message_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    elif isinstance(update, Update) and update.message:
        # This block runs if 'start' was called by a command like /start.
        # 'update' is the full Update object.
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """The /help command will now just show the main menu again."""
    # This correctly passes the full Update object to the start function.
    await start(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles button clicks from the main menu."""
    query = update.callback_query
    await query.answer()  # Acknowledge the button press immediately

    category_key = query.data
    
    if category_key == "main_menu":
        # This now works because the 'start' function can handle the 'query' object.
        await start(query, context) # Pass the CallbackQuery object to the start function
        return

    if category_key in FINANCIAL_LINKS:
        category = FINANCIAL_LINKS[category_key]
        
        message = f"**{category['title']}**\n_{category['description']}_\n\n"
        for link in category["links"]:
            message += f"🔗 [{link['name']}]({link['url']})\n"
            message += f"   - {link['desc']}\n\n"
            
        # Create the "Back to Menu" button
        keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Edit the message text and the reply markup in two steps.
        # First, update the text to show the links.
        await query.edit_message_text(
            text=message,
            parse_mode='Markdown',
            disable_web_page_preview=True,
            reply_markup=reply_markup # Add the button at the same time
        )


def main() -> None:
    """Start the bot."""
    # --- IMPROVED TOKEN HANDLING ---
    # It's recommended to use an environment variable for your bot token for security.
    # Name the environment variable "BOT_TOKEN".
    TOKEN = os.environ.get("BOT_TOKEN")

    # If you are testing locally and don't want to set environment variables,
    # you can uncomment the following line and paste your token.
    TOKEN = "8035433844:AAEVK7XMtfgrGFj__kInF0yCr3KuPdx6JEk" 

    if not TOKEN:
        logging.error("ERROR: Bot token not found. Please set the 'BOT_TOKEN' environment variable or paste it directly into the code.")
        return
        
    application = Application.builder().token(TOKEN).build()

    # Add handlers for start and help commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Add handler for button clicks
    application.add_handler(CallbackQueryHandler(button_handler))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
