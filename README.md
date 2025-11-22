# Toyota SS.lv Telegram Bot 🚗

A real-time Telegram bot that monitors SS.lv (Latvia's largest classified ads site) for Toyota vehicle listings, with special focus on damaged/crashed vehicles and popular models like Land Cruiser and Hilux.

## 🌟 Features

### Smart Monitoring
- **Real-time notifications** for new Toyota listings
- **Multi-source monitoring**: Regular Toyota section + crash/defect section
- **Smart filtering**: Fuel-specific filters with crash page exceptions
- **40-second check intervals** for instant notifications

### Enhanced Crash Detection
- **Damage severity indicators**: 🚨 SMAGI BOJĀTS, ⚠️ VIDĒJI BOJĀTS, ✅ VIEGLI BOJĀTS
- **Crash type detection**: Fire damage, flood damage, accident damage
- **Condition analysis**: Percentage-based damage assessment
- **Visual labels** for quick damage identification

### Intelligent Features
- **Duplicate prevention**: Advanced listing tracking
- **Link escaping**: Proper Telegram URL formatting
- **Error handling**: Robust connection management
- **Logging**: Comprehensive activity tracking
- 🛡️ Robust error handling for network issues
- 📝 Clean, modular, and well-documented code

## Prerequisites

- Python 3.10 or higher
- A Telegram account
- Internet connection

## Installation

### 1. Clone or Download

Clone this repository or download the files to your local machine.

### 2. Install Dependencies

Open PowerShell in the project directory and run:

```powershell
pip install -r requirements.txt
```

This will install:
- `requests` - For HTTP requests
- `beautifulsoup4` - For HTML parsing
- `python-telegram-bot` - For Telegram bot functionality
- `python-dotenv` - For environment variable management

### 3. Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token provided by BotFather

### 4. Configure Environment Variables

1. Copy the example environment file:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit `.env` file and add your bot token:
   ```
   TELEGRAM_BOT_TOKEN=your_actual_bot_token_here
   ```

## Usage

### Running the Bot

Start the bot by running:

```powershell
python toyota_bot.py
```

You should see:
```
🤖 Toyota Defective Car Bot is running...
Press Ctrl+C to stop
```

### Bot Commands

Once the bot is running, open Telegram and find your bot:

- `/start` - Shows welcome message and available commands
- `/defective` - Searches and returns current defective Toyota listings

### Example Interaction

```
You: /defective

Bot: 🔍 Searching for defective Toyota listings...

Bot: 🚗 Found 2 defective Toyota listing(s):

1. Toyota Land Cruiser 100, defekti
💰 Price: 3500 €
🔗 Link: https://www.ss.lv/msg/lv/transport/...

2. Toyota Hilux, ar defektiem
💰 Price: 2800 €
🔗 Link: https://www.ss.lv/msg/lv/transport/...

⏰ Updated: 2025-11-10 14:30:45
```

## Optional: Enable Scheduled Checks

To enable automatic checking for new listings every 10 minutes:

1. Open `toyota_bot.py`
2. Find the following lines in the `main()` function (around line 275):
   ```python
   # Uncomment the following lines to enable automatic checking
   # job_queue = application.job_queue
   # job_queue.run_repeating(
   #     scheduled_check,
   #     interval=SCHEDULER_INTERVAL,
   #     first=10  # First run after 10 seconds
   # )
   ```
3. Uncomment them by removing the `#` symbols:
   ```python
   # Enable automatic checking
   job_queue = application.job_queue
   job_queue.run_repeating(
       scheduled_check,
       interval=SCHEDULER_INTERVAL,
       first=10  # First run after 10 seconds
   )
   ```

## Configuration

You can customize the bot by editing these variables in `toyota_bot.py`:

```python
# URL to scrape
SS_LV_URL = 'https://www.ss.lv/lv/transport/cars/toyota/all/sell/filter/'

# HTTP request timeout (seconds)
REQUEST_TIMEOUT = 10

# Scheduler interval (seconds) - default is 600 (10 minutes)
SCHEDULER_INTERVAL = 600

# Car models to filter
TARGET_MODELS = ['land cruiser', 'hilux']
```

## Project Structure

```
SS_bot_toyota/
├── toyota_bot.py          # Main bot script
├── requirements.txt       # Python dependencies
├── .env.example          # Example environment configuration
├── .env                  # Your actual configuration (not in git)
├── .gitignore           # Git ignore file
└── README.md            # This file
```

## How It Works

1. **Scraping**: The bot uses `requests` to fetch the HTML from ss.lv
2. **Parsing**: BeautifulSoup extracts car listings (title, price, link)
3. **Filtering**: Only Land Cruiser and Hilux with "defekt" keyword are kept
4. **Formatting**: Results are formatted into clean messages
5. **Delivery**: Messages are sent to users via Telegram

## Error Handling

The bot handles various error scenarios:

- ❌ **Network timeouts**: Graceful timeout with user-friendly message
- ❌ **HTTP errors**: Catches bad responses and connection issues
- ❌ **No results**: Friendly message when no defective cars are found
- ❌ **Parsing errors**: Continues processing even if individual listings fail

## Troubleshooting

### Bot doesn't start
- Check that `TELEGRAM_BOT_TOKEN` is set correctly in `.env`
- Verify all dependencies are installed: `pip install -r requirements.txt`

### No listings found
- The website structure may have changed
- Check if the URL is accessible: https://www.ss.lv/lv/transport/cars/toyota/all/sell/filter/
- Ensure internet connection is working

### Import errors
- Make sure you're using Python 3.10+: `python --version`
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`

## Security Notes

- ⚠️ Never commit your `.env` file with the actual bot token
- ⚠️ Keep your bot token secret
- ⚠️ The `.env` file is already in `.gitignore` to prevent accidental commits

## Future Enhancements

Possible improvements:
- 📢 Notify subscribed users when new defective cars are found
- 💾 Store listings in a database to track changes
- 🔔 Allow users to set custom filters (price range, year, etc.)
- 📊 Analytics on listing trends
- 🌍 Multi-language support

## License

This project is provided as-is for educational and personal use.

## Disclaimer

This bot is for personal use only. Please respect ss.lv's terms of service and robots.txt when scraping. Consider adding delays between requests if making frequent checks.

---

**Happy car hunting! 🚙**
