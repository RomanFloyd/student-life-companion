#!/usr/bin/env python3
"""
Telegram Bot for Student Life Companion
Connects to FastAPI backend and provides Q&A interface
"""

import os
import logging
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8888")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in .env file!")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when /start command is issued"""
    welcome_message = """
👋 **Welcome to Harbour.Space Student Life Companion!**

I'm here to help you with:
🎓 University procedures (TIE, visa, enrollment)
🏠 Housing (empadronamiento, finding apartments)
💳 Banking & admin (bank accounts, NIE, taxes)
🚇 Transport (metro, T-Casual, airport)
🏥 Healthcare (TSI card, insurance)
📱 Mobile (SIM cards, phone plans)
🌆 Life in Barcelona (beaches, food, Spanish classes)

**Just ask me anything!** For example:
• "How to book TIE appointment?"
• "Where to learn Spanish?"
• "What is empadronamiento?"

Type /help to see available commands.
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message when /help command is issued"""
    help_text = """
**Available Commands:**

/start - Welcome message
/help - Show this help message
/topics - Show available topics
/popular - Show popular questions

**Just ask your question directly!**
No need for commands - I understand natural language.

Examples:
• "How much does metro cost?"
• "Where to find apartment?"
• "Can I work while studying?"
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def topics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available topics"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/topics", timeout=10.0)
            topics = response.json()
        
        topics_text = "**📚 Available Topics:**\n\n"
        for topic in topics:
            emoji = {
                "visa": "🎓",
                "housing": "🏠",
                "banking": "💳",
                "transport": "🚇",
                "healthcare": "🏥",
                "mobile": "📱",
                "life": "🌆",
                "university": "🎓",
                "admin": "📋",
                "work": "💼"
            }.get(topic["topic"], "📌")
            
            topics_text += f"{emoji} **{topic['topic'].title()}** ({topic['count']} questions)\n"
        
        await update.message.reply_text(topics_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error fetching topics: {e}")
        await update.message.reply_text("Sorry, couldn't fetch topics. Please try again later.")


async def popular_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show popular questions"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/popular?limit=5", timeout=10.0)
            popular = response.json()
        
        if not popular:
            await update.message.reply_text("No popular questions yet!")
            return
        
        popular_text = "**🔥 Popular Questions:**\n\n"
        for i, item in enumerate(popular, 1):
            popular_text += f"{i}. {item['question']}\n"
        
        popular_text += "\n_Just ask any of these questions!_"
        await update.message.reply_text(popular_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error fetching popular questions: {e}")
        await update.message.reply_text("Sorry, couldn't fetch popular questions. Please try again later.")


async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user questions"""
    user_question = update.message.text
    user_name = update.effective_user.first_name
    
    logger.info(f"Question from {user_name}: {user_question}")
    
    # Send "typing..." indicator
    await update.message.chat.send_action("typing")
    
    try:
        # Call FastAPI backend
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/ask",
                params={"query": user_question},
                timeout=30.0
            )
            data = response.json()
        
        # Format response
        answer = data["answer"]
        source = data["source"]
        
        # Add metadata
        response_text = f"{answer}\n\n"
        
        # Add steps if available
        if data.get("steps"):
            response_text += "\n**📋 Steps:**\n"
            for i, step in enumerate(data["steps"], 1):
                response_text += f"{i}. {step}\n"
        
        # Add source info
        source_emoji = "🤖" if source == "llm-groq" else "✅"
        source_label = "AI Assistant" if source == "llm-groq" else "Knowledge Base"
        response_text += f"\n{source_emoji} _Source: {source_label}_"
        
        # Add quick links if available
        if data.get("quick_links"):
            response_text += "\n\n**🔗 Quick Links:**"
            for link in data["quick_links"]:
                response_text += f"\n• [{link['label']}]({link['url']})"
        
        await update.message.reply_text(response_text, parse_mode='Markdown', disable_web_page_preview=True)
        
    except httpx.TimeoutException:
        await update.message.reply_text("⏱️ Request timed out. Please try again.")
    except Exception as e:
        logger.error(f"Error handling question: {e}")
        await update.message.reply_text(
            "❌ Sorry, something went wrong. Please try again or contact student.experience@harbour.space"
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")


def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("topics", topics_command))
    application.add_handler(CommandHandler("popular", popular_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    logger.info("🤖 Starting Telegram bot...")
    logger.info(f"📡 API URL: {API_BASE_URL}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
