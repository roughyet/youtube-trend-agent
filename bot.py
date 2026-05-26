import requests
import json
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Your APIs
YOUTUBE_API_KEY = "AIzaSyAb8pSoMtdIWtcmgs_eD2YB5Pj5twzdFQQ"
GEMINI_API_KEY = "AIzaSyDzzv6E6Q7AKuzm5hm2B3CRF79VhL2JkEc"
TELEGRAM_BOT_TOKEN = "8811553390:AAH_uBnZOXzqIKF1MWQ4LRRKTDlc1auK3EI"
TELEGRAM_CHAT_ID = 8811553390

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

SEARCH_TOPICS = [
    "Class 1 Bengali alphabet", "Class 2 Mathematics addition", "Class 3 English learning",
    "Class 4 Science animals", "Class 5 History Bangladesh", "Class 6 Geography maps",
    "Class 7 Physics motion", "Class 8 Chemistry elements", "Class 9 Biology cells",
    "Class 10 English literature", "Class 10 Bengali grammar", "Class 10 Mathematics algebra",
    "How to study effectively", "Online learning platform", "Exam preparation tips",
    "Physics tutorial", "Chemistry experiment", "History of Bangladesh", "Bangla literature",
    "Mathematics problem solving", "Biology practical", "English grammar rules",
    "Python programming", "Web development tutorial", "Artificial intelligence",
    "Mobile app development", "Cloud computing", "Cybersecurity", "JavaScript tutorial",
    "Data science", "Tech news", "Programming tips", "English grammar", "English pronunciation",
    "IELTS exam", "English speaking", "English vocabulary", "English writing", "English for beginners", "English conversation",
]

def get_youtube_search_volume(query, region="BD"):
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "regionCode": region,
            "order": "relevance",
            "maxResults": 50,
            "key": YOUTUBE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        results = response.json()
        search_volume = results.get("pageInfo", {}).get("totalResults", 0)
        items = results.get("items", [])
        
        top_title = "No results"
        top_channel = "N/A"
        
        if items:
            top_title = items[0]["snippet"]["title"][:55]
            top_channel = items[0]["snippet"]["channelTitle"]
        
        logger.info(f"✓ {query} - {search_volume:,}")
        
        return {
            "query": query,
            "search_volume": search_volume,
            "top_title": top_title,
            "top_channel": top_channel
        }
    
    except Exception as e:
        logger.error(f"❌ {query}: {e}")
        return {"query": query, "search_volume": 0, "top_title": "Error", "top_channel": "Error"}

def collect_all_search_data():
    logger.info(f"🔍 Collecting search data for {len(SEARCH_TOPICS)} topics...\n")
    all_data = []
    
    for i, topic in enumerate(SEARCH_TOPICS, 1):
        print(f"[{i:2d}/{len(SEARCH_TOPICS)}] {topic}")
        data = get_youtube_search_volume(topic)
        all_data.append(data)
        time.sleep(0.4)
    
    return all_data

def get_top_20_by_searches(all_data):
    ranked = sorted(all_data, key=lambda x: x["search_volume"], reverse=True)
    top_20 = ranked[:20]
    
    logger.info(f"\n📊 TOP 20 BY SEARCH VOLUME:\n")
    for i, item in enumerate(top_20, 1):
        logger.info(f"   #{i} {item['query']}: {item['search_volume']:,}")
    
    return top_20

def analyze_trends_with_ai(top_20):
    topics_str = "\n".join([
        f"{i}. {item['query']} ({item['search_volume']:,} searches)"
        for i, item in enumerate(top_20, 1)
    ])
    
    prompt = f"""Analyze these YouTube SEARCH TRENDS from Bangladesh.

TOP 20 MOST SEARCHED TOPICS:
{topics_str}

Provide:
1. Which topics are most searched
2. Educational vs Tech vs English learning trends
3. What this tells us about learners
4. Recommendations for content creators

Keep it under 200 words."""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return "Analysis unavailable"

def create_report(top_20, analysis):
    msg = "🎯 **YOUTUBE SEARCH TRENDS - BANGLADESH**\n\n"
    msg += "📊 **TOP 20 MOST SEARCHED TOPICS**\n"
    msg += ("=" * 50) + "\n\n"
    
    for i, item in enumerate(top_20, 1):
        vol = item['search_volume']
        bar = "█" * min(int(vol / 500000), 15)
        msg += f"**#{i}** {item['query']}\n"
        msg += f"     🔍 {vol:>15,} searches {bar}\n\n"
    
    msg += ("=" * 50) + "\n"
    msg += "💡 **TREND ANALYSIS**\n"
    msg += ("=" * 50) + "\n\n"
    msg += analysis
    msg += f"\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n✅ Analysis complete"
    
    return msg

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    msg_id = None
    
    try:
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text="🚀 **Search Trend Analysis Started**\n\n⏳ Analyzing YouTube searches...\n(~45 seconds)"
        )
        msg_id = msg.message_id
        
        logger.info(f"User {chat_id} started analysis\n")
        
        await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text="⏳ Step 1/4: Collecting search volume data...")
        all_data = collect_all_search_data()
        
        await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text="⏳ Step 2/4: Ranking by search volume...")
        top_20 = get_top_20_by_searches(all_data)
        
        await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text="⏳ Step 3/4: Generating AI insights...")
        analysis = analyze_trends_with_ai(top_20)
        
        await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text="⏳ Step 4/4: Formatting report...")
        
        report = create_report(top_20, analysis)
        
        if len(report) > 4096:
            chunks = [report[i:i+4090] for i in range(0, len(report), 4090)]
            for chunk in chunks:
                await context.bot.send_message(chat_id=chat_id, text=chunk, parse_mode="Markdown")
                time.sleep(0.2)
        else:
            await context.bot.send_message(chat_id=chat_id, text=report, parse_mode="Markdown")
        
        logger.info("✅ Report sent!\n")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        try:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Error: {str(e)}")
        except:
            pass

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """🤖 **YouTube Search Trend Bot**

**Commands:**
/start - Analyze search trends (45 seconds)
/help - Show this

**Analyzes:**
✓ SEARCH VOLUME (not video views)
✓ 38 topics: Class 1-10, Education, Tech, English
✓ Top 20 ranked by searches
✓ AI trend insights

**Works 24/7 in cloud** ☁️
"""
    await update.message.reply_text(text)

def main():
    print("\n" + "="*60)
    print("🤖 YouTube SEARCH TREND ANALYZER BOT")
    print("="*60)
    print("✓ Running 24/7 in cloud")
    print("✓ Analyzes SEARCH VOLUME (not views)")
    print("✓ API Keys: Configured")
    print("="*60)
    print("\nCommands:")
    print("  /start - Analyze trends")
    print("  /help  - Show help\n")
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    
    print("✅ Bot online. Waiting for commands...\n")
    app.run_polling()

if __name__ == "__main__":
    main()
