# 🤖 Telegram Bot Setup

## Step 1: Create Telegram Bot

1. Open Telegram and find **@BotFather**
2. Send `/newbot`
3. Choose a name: `Harbour Space Assistant`
4. Choose a username: `harbourspace_assistant_bot` (must end with `_bot`)
5. Copy the token you receive (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

## Step 2: Add Token to .env

Add this line to your `.env` file:

```
TELEGRAM_BOT_TOKEN=your_token_here
```

## Step 3: Start FastAPI Server

In one terminal:

```bash
uvicorn main:app --reload --port 8888
```

## Step 4: Start Telegram Bot

In another terminal:

```bash
python telegram_bot.py
```

## Step 5: Test the Bot

1. Open Telegram
2. Find your bot by username
3. Send `/start`
4. Ask a question: "How to book TIE appointment?"

## Available Commands

- `/start` - Welcome message
- `/help` - Show help
- `/topics` - Show available topics
- `/popular` - Show popular questions

## Troubleshooting

**Bot doesn't respond:**
- Check if FastAPI server is running on port 8888
- Check if `TELEGRAM_BOT_TOKEN` is correct in `.env`
- Check bot logs for errors

**"Connection refused" error:**
- Make sure FastAPI server is running
- Check `API_BASE_URL` in `.env` (should be `http://127.0.0.1:8888`)

## Deploy to Production

For 24/7 operation, deploy to:
- **DigitalOcean** ($5/month)
- **Hetzner** ($4/month)
- **Railway.app** (free tier available)

See `DEPLOYMENT.md` for instructions.
