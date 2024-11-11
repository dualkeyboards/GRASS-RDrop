# _includes/core.py
import asyncio
import random
import ssl
import json
import time
import uuid
from websockets_proxy import Proxy, proxy_connect
from fake_useragent import UserAgent
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from python_socks._errors import ProxyConnectionError
from loguru import logger
from _includes.proxies_manager import update_file, get_proxy_name
from _includes.errors_handler import handle_generic_error

async def connect_to_wss(proxy_url, device_id, user_id, stats, removed_proxies, retry_counts):
    user_agent = UserAgent()
    random_user_agent = user_agent.random

    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 5)
            custom_headers = {"User-Agent": random_user_agent}
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            urilist = ["wss://proxy.wynd.network:4444/", "wss://proxy.wynd.network:4650/"]
            uri = random.choice(urilist)
            server_hostname = "proxy.wynd.network"

            protocol = proxy_url.split("://")[0]
            if protocol in ["socks4", "socks5", "http"]:
                try:
                    proxy = Proxy.from_url(proxy_url)
                except Exception as e:
                    logger.error(f"Error creating proxy object: {e}")
                    retur
            else:
                logger.error(f"Unsupported proxy type: {protocol}")
                return

            async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, server_hostname=server_hostname,
                                     extra_headers=custom_headers) as websocket:

                async def send_ping():
                    while True:
                        try:
                            if websocket.closed:
                                break
                            send_message = json.dumps({"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                            proxy_ip = get_proxy_name(proxy_url)
                            logger.log("PING", f"PINGING to: {proxy_ip}")
                            await websocket.send(send_message)
                            stats['pings'] += 1
                            update_file("proxies_ping.txt", proxy_url) 
                            await asyncio.sleep(10)
                        except ConnectionClosedOK:
                            proxy_ip = get_proxy_name(proxy_url)
                            logger.warning(f"Connection closed gracefully during PING to {proxy_ip}")
                            break
                        except ConnectionClosedError:
                            proxy_ip = get_proxy_name(proxy_url)
                            logger.error(f"Connection closed unexpectedly during PING to {proxy_ip}")
                            break

                await asyncio.sleep(1)
                ping_task = asyncio.create_task(send_ping())

                while True:
                    try:
                        response = await websocket.recv()
                        message = json.loads(response)
                        proxy_ip = get_proxy_name(proxy_url)
                        if message.get("action") == "AUTH":
                            logger.log("AUTHENTICATION", f"AUTHENTICATION request from: {proxy_ip}")
                            auth_response = {
                                "id": message["id"],
                                "origin_action": "AUTH",
                                "result": {
                                    "browser_id": device_id,
                                    "user_id": user_id,
                                    "user_agent": custom_headers['User-Agent'],
                                    "timestamp": int(time.time()),
                                    "device_type": "desktop",
                                    "version": "4.28.2",
                                }
                            }
                            logger.log("AUTHENTICATION", f"AUTHENTICATION reply to: {proxy_ip}")
                            await websocket.send(json.dumps(auth_response))
                            update_file("proxies_auth.txt", proxy_url)

                        elif message.get("action") == "PONG":
                            logger.log("PONG", f"PONG received from - {proxy_ip}")
                            stats['pongs'] += 1
                            pong_response = {"id": message["id"], "origin_action": "PONG"}
                            await websocket.send(json.dumps(pong_response))
                            update_file("proxies_pong.txt", proxy_url)
                    except ConnectionClosedError:
                        proxy_ip = get_proxy_name(proxy_url)
                        logger.error(f"Connection closed while receiving data")
                        break
                    except OSError as e:
                        if "WinError 121" in str(e):
                            proxy_ip = get_proxy_name(proxy_url)
                            logger.error(f"Semaphore timeout expired - {proxy_ip}. Retrying connection...")
                            await asyncio.sleep(10)
                            break

        except ProxyConnectionError:
            proxy_ip = get_proxy_name(proxy_url)
            logger.error(f"Connection refused - {proxy_ip}")
            removed_proxies += 1
            update_file("proxies_error.txt", proxy_url)
            await asyncio.sleep(10)
            break
        except Exception as e:
            await handle_generic_error(proxy_url, removed_proxies, retry_counts, e)
            if retry_counts.get(proxy_url, 0) >= 2:
                break 
            await asyncio.sleep(10)