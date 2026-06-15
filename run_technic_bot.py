"""
Wall Street Technic Bot ni loyiha ildizidan ishga tushirish uchun launcher.

Lokal:  python run_technic_bot.py
Hostda: Procfile dagi `technic` jarayoni shu faylni chaqiradi.
"""
import asyncio
import os
import sys

BOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "wallstreet", "technic_bot")
sys.path.insert(0, BOT_DIR)

import bot  # noqa: E402

if __name__ == "__main__":
    asyncio.run(bot.main())
