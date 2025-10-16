#!/usr/bin/env python3
"""
Telegram Bot for Student Life Companion
Connects to FastAPI backend and provides Q&A interface
"""

import os
import logging
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
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
    """Send welcome message and profile selection"""
    user_id = str(update.effective_user.id)
    
    # Check if user already has a profile
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/profile/{user_id}", timeout=5.0)
            data = response.json()
            
            if data.get("status") == "success":
                # User has profile, show welcome
                profile_name = {
                    "student-longterm": "📚 Student (long-term)",
                    "teacher-shortterm": "👨‍🏫 Teacher (3-9 weeks)",
                    "exchange-visiting": "🌍 Exchange/Visiting (3-9 weeks)",
                    "just-arrived": "🛬 Just Arrived",
                    "other": "🤷 Other"
                }.get(data.get("profile"), "Unknown")
                
                welcome_message = f"""
👋 **Welcome back to Harbour.Space Student Life Companion!**

Your profile: {profile_name}

**Just ask me anything!** For example:
• "How to book TIE appointment?"
• "Where to learn Spanish?"
• "What is empadronamiento?"

Type /profile to change your profile
Type /help to see available commands
"""
                await update.message.reply_text(welcome_message, parse_mode='Markdown')
                return
    except Exception as e:
        logger.error(f"Error checking profile: {e}")
    
    # No profile - show selection
    await show_profile_selection(update, context)


async def show_profile_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show profile selection buttons"""
    keyboard = [
        [InlineKeyboardButton("📚 Student (long-term)", callback_data="profile_student-longterm")],
        [InlineKeyboardButton("👨‍🏫 Teacher (3-9 weeks)", callback_data="profile_teacher-shortterm")],
        [InlineKeyboardButton("🌍 Exchange/Visiting (3-9 weeks)", callback_data="profile_exchange-visiting")],
        [InlineKeyboardButton("🛬 Just Arrived (first week)", callback_data="profile_just-arrived")],
        [InlineKeyboardButton("🤷 Other", callback_data="profile_other")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = """
👋 **Welcome to Harbour.Space Student Life Companion!**

Please select your profile to get personalized help:

📚 **Student (long-term)** - Full degree (1-4 years)
👨‍🏫 **Teacher** - Short-term teaching (3-9 weeks)
🌍 **Exchange/Visiting** - Exchange student (3-9 weeks)
🛬 **Just Arrived** - Survival guide (first week)
🤷 **Other** - I don't fit into these categories

Choose your profile:
"""
    
    if update.callback_query:
        await update.callback_query.message.edit_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')


async def profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle profile selection"""
    query = update.callback_query
    await query.answer()
    
    profile_type = query.data.replace("profile_", "")
    user_id = str(update.effective_user.id)
    
    # Save profile
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/profile",
                json={"user_id": user_id, "profile_type": profile_type},
                timeout=5.0
            )
            data = response.json()
            
            if data.get("status") == "success":
                profile_names = {
                    "student-longterm": "📚 Student (long-term)",
                    "teacher-shortterm": "👨‍🏫 Teacher (3-9 weeks)",
                    "exchange-visiting": "🌍 Exchange/Visiting (3-9 weeks)",
                    "just-arrived": "🛬 Just Arrived",
                    "other": "🤷 Other"
                }
                
                success_message = f"""
✅ **Profile set: {profile_names.get(profile_type)}**

I'll now show you relevant information for your profile!

**Just ask me anything!** For example:
• "How to book TIE appointment?"
• "Where to find apartment?"
• "How much does metro cost?"

Type /help to see available commands
Type /profile to change your profile
"""
                await query.message.edit_text(success_message, parse_mode='Markdown')
            else:
                await query.message.edit_text("❌ Error setting profile. Please try again with /profile")
                
    except Exception as e:
        logger.error(f"Error saving profile: {e}")
        await query.message.edit_text("❌ Error setting profile. Please try again with /profile")


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show profile selection"""
    await show_profile_selection(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message when /help command is issued"""
    help_text = """
**Available Commands:**

/start - Welcome message
/profile - Change your profile
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
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("topics", topics_command))
    application.add_handler(CommandHandler("popular", popular_command))
    application.add_handler(CallbackQueryHandler(profile_callback, pattern="^profile_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    logger.info("🤖 Starting Telegram bot...")
    logger.info(f"📡 API URL: {API_BASE_URL}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
