"""
Telegram bot notification adapter.

Sends a formatted ZIP intelligence summary to a Telegram chat whenever
a user searches a ZIP code. Notifications are fire-and-forget (non-blocking).

Setup:
  1. Open Telegram → search @BotFather → /newbot → follow prompts.
  2. Copy the bot token (looks like 123456789:AABBccdd...).
  3. Send any message to your new bot.
  4. Get your chat ID: https://api.telegram.org/bot<TOKEN>/getUpdates
     Look for "chat":{"id":<YOUR_CHAT_ID>}
  5. Add to backend/.env:
       TELEGRAM_BOT_TOKEN=123456789:AABBccdd...
       TELEGRAM_CHAT_ID=123456789
"""
from __future__ import annotations

import logging
import ssl
import threading
import urllib.parse
import urllib.error
import urllib.request
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from app.adapters.contracts import ZipSummary

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def _format_message(summary: "ZipSummary") -> str:
    return (
        f"📍 *ZIP {summary.zip_code} Search*\n"
        f"\n"
        f"🌐 *Network*\n"
        f"  Signal: `{summary.signal_score:.1f}` | Internet: `{summary.consistency_score:.1f}`\n"
        f"  Download: `{summary.avg_download_mbps:.1f} Mbps` | Upload: `{summary.avg_upload_mbps:.1f} Mbps`\n"
        f"  Providers: `{summary.provider_count}`\n"
        f"\n"
        f"🏥 *Healthcare*\n"
        f"  Score: `{summary.healthcare_access_score:.1f}` | Hospitals: `{summary.hospital_count}`\n"
        f"\n"
        f"🏠 *Real Estate*\n"
        f"  Home Value: `${summary.median_home_value:,}` | Ownership: `{summary.home_ownership_rate:.1f}%`\n"
        f"  Vacancy: `{summary.vacancy_rate:.1f}%`\n"
        f"\n"
        f"👥 *Demographics*\n"
        f"  Population: `{summary.population_total:,}` | Income: `${summary.median_income:,}`\n"
        f"\n"
        f"📊 *Scores*\n"
        f"  Overall: `{summary.overall_score:.1f}` | Market: `{summary.market_attractiveness_score:.1f}`\n"
        f"  Opportunity: `{summary.network_opportunity_score:.1f}`"
    )


def _send(token: str, chat_id: str, text: str) -> None:
    try:
        url = _TELEGRAM_API.format(token=token)
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }

        try:
            with httpx.Client(timeout=10.0, verify=False) as client:
                resp = client.post(
                    url,
                    json=payload,
                    headers={
                        "User-Agent": "Mozilla/5.0",
                        "Accept": "application/json",
                    },
                )
            if not resp.is_success:
                # Some networks block scripted POSTs and return HTML 403 pages.
                is_html_block = "text/html" in resp.headers.get("content-type", "") or resp.text.lstrip().startswith("<!DOCTYPE")
                if resp.status_code == 403 and is_html_block:
                    with httpx.Client(timeout=10.0, verify=False) as client:
                        get_resp = client.get(
                            url,
                            params=payload,
                            headers={
                                "User-Agent": "Mozilla/5.0",
                                "Accept": "application/json",
                            },
                        )
                    if get_resp.is_success:
                        return
                    logger.warning("Telegram notification failed (GET fallback): %s %s", get_resp.status_code, get_resp.text[:200])
                else:
                    logger.warning("Telegram notification failed: %s %s", resp.status_code, resp.text[:200])
        except Exception as httpx_exc:
            # Fallback for environments with broken CA chain/proxy SSL interception.
            data = httpx.Request("POST", url, json=payload).read()
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json",
                },
                method="POST",
            )
            context = ssl._create_unverified_context()
            try:
                with urllib.request.urlopen(req, context=context, timeout=10.0) as response:
                    if response.status < 200 or response.status >= 300:
                        body = response.read(200).decode("utf-8", errors="replace")
                        logger.warning("Telegram notification failed: %s %s", response.status, body)
            except urllib.error.URLError:
                # Final fallback: use GET with query params to bypass POST-blocking proxies.
                query = urllib.parse.urlencode(payload)
                get_req = urllib.request.Request(
                    f"{url}?{query}",
                    headers={
                        "User-Agent": "Mozilla/5.0",
                        "Accept": "application/json",
                    },
                    method="GET",
                )
                with urllib.request.urlopen(get_req, context=context, timeout=10.0) as response:
                    if response.status < 200 or response.status >= 300:
                        body = response.read(200).decode("utf-8", errors="replace")
                        logger.warning("Telegram notification failed (urllib GET fallback): %s %s", response.status, body)
    except Exception as exc:
        logger.warning("Telegram notification error: %s", exc)


def notify_zip_search(token: str, chat_id: str, summary: "ZipSummary") -> None:
    """Fire-and-forget: send ZIP summary notification in a background thread."""
    if not token or not chat_id:
        return

    text = _format_message(summary)
    thread = threading.Thread(target=_send, args=(token, chat_id, text), daemon=True)
    thread.start()
