import asyncio
import logging
import os
from datetime import datetime, timedelta

import aiosqlite
import dateparser
import httpx
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from ai
