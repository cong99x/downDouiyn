#!/usr/bin/env python
# -*- coding: utf-8 -*-


import argparse
import os
import sys
import json
import yaml
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path
import logging

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
# Renamed to douyin_logger to avoid conflicts
douyin_logger = logging.getLogger("DouYin")

# Safely use douyin_logger
try:
    import asyncio
    import aiohttp
    ASYNC_SUPPORT = True
except ImportError:
    ASYNC_SUPPORT = False
    douyin_logger.warning("aiohttp not installed, asynchronous download function unavailable")

from apiproxy.douyin.douyin import Douyin
from apiproxy.douyin.download import Download
from apiproxy.douyin import douyin_headers
from apiproxy.common import utils

@dataclass
class DownloadConfig:
    """Download Configuration Class"""
    link: List[str]
    path: Path
    music: bool = True
    cover: bool = True
    avatar: bool = True
    json: bool = True
    start_time: str = ""
    end_time: str = ""
    folderstyle: bool = True
    mode: List[str] = field(default_factory=lambda: ["post"])
    thread: int = 5
    cookie: Optional[str] = None
    database: bool = True
    number: Dict[str, int] = field(default_factory=lambda: {
        "post": 0, "like": 0, "allmix": 0, "mix": 0, "music": 0
    })
    increase: Dict[str, bool] = field(default_factory=lambda: {
        "post": False, "like": False, "allmix": False, "mix": False, "music": False
    })
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "DownloadConfig":
        """Load configuration from YAML file"""
        # Implementation for YAML config loading
        pass
        
    @classmethod 
    def from_args(cls, args) -> "DownloadConfig":
        """Load configuration from command line arguments"""
        # Implementation for parameter loading
        pass
        
    def validate(self) -> bool:
        """Validate configuration effectiveness"""
        # Implementation for validation logic
        pass

configModel = {
    "link": [],
    "path": os.getcwd(),
    "music": True,
    "cover": True,
    "avatar": True,
    "json": True,
    "start_time": "",
    "end_time": "",
    "folderstyle": True,
    "mode": ["post"],
    "number": {
        "post": 0,
        "like": 0,
        "allmix": 0,
        "mix": 0,
        "music": 0,
    },
    'database': True,
    "increase": {
        "post": False,
        "like": False,
        "allmix": False,
        "mix": False,
        "music": False,
    },
    "thread": 5,
    "cookie": os.environ.get("DOUYIN_COOKIE", "")
}

def argument():
    parser = argparse.ArgumentParser(description='Douyin Batch Download Tool Help')
    parser.add_argument("--cmd", "-C", help="Use command line (True) or configuration file (False). Default is False",
                        type=utils.str2bool, required=False, default=False)
    parser.add_argument("--link", "-l",
                        help="Share link or web URL for work (video/gallery), live, collection, music collection, or personal homepage. Multiple links can be set (remove text, ensure only URL, starting with https://v.douyin.com/ or https://www.douyin.com/)",
                        type=str, required=False, default=[], action="append")
    parser.add_argument("--path", "-p", help="Download save location, default is current directory",
                        type=str, required=False, default=os.getcwd())
    parser.add_argument("--music", "-m", help="Whether to download music from videos (True/False). Default is True",
                        type=utils.str2bool, required=False, default=True)
    parser.add_argument("--cover", "-c", help="Whether to download video covers (True/False). Default is True (effective for videos)",
                        type=utils.str2bool, required=False, default=True)
    parser.add_argument("--avatar", "-a", help="Whether to download author avatars (True/False). Default is True",
                        type=utils.str2bool, required=False, default=True)
    parser.add_argument("--json", "-j", help="Whether to save obtained metadata (True/False). Default is True",
                        type=utils.str2bool, required=False, default=True)
    parser.add_argument("--folderstyle", "-fs", help="File save style. Default is True",
                        type=utils.str2bool, required=False, default=True)
    parser.add_argument("--mode", "-M", help="When link is a personal homepage, set to download published works (post), liked works (like), or all user collections (mix). Default is post. Multiple modes can be set.",
                        type=str, required=False, default=[], action="append")
    parser.add_argument("--postnumber", help="Set number of homepage works to download. Default is 0 (all)",
                        type=int, required=False, default=0)
    parser.add_argument("--likenumber", help="Set number of liked works to download. Default is 0 (all)",
                        type=int, required=False, default=0)
    parser.add_argument("--allmixnumber", help="Set number of homepage collections to download. Default is 0 (all)",
                        type=int, required=False, default=0)
    parser.add_argument("--mixnumber", help="Set number of works to download in a single collection. Default is 0 (all)",
                        type=int, required=False, default=0)
    parser.add_argument("--musicnumber", help="Set number of works to download under music (soundtrack). Default is 0 (all)",
                        type=int, required=False, default=0)
    parser.add_argument("--database", "-d", help="Whether to use database. Default is True. If False, incremental updates are unavailable.",
                        type=utils.str2bool, required=False, default=True)
    parser.add_argument("--postincrease", help="Whether to enable incremental download for homepage works (True/False). Default is False",
                        type=utils.str2bool, required=False, default=False)
    parser.add_argument("--likeincrease", help="Whether to enable incremental download for homepage likes (True/False). Default is False",
                        type=utils.str2bool, required=False, default=False)
    parser.add_argument("--allmixincrease", help="Whether to enable incremental download for homepage collections (True/False). Default is False",
                        type=utils.str2bool, required=False, default=False)
    parser.add_argument("--mixincrease", help="Whether to enable incremental download for works in a single collection (True/False). Default is False",
                        type=utils.str2bool, required=False, default=False)
    parser.add_argument("--musicincrease", help="Whether to enable incremental download for works under music (soundtrack) (True/False). Default is False",
                        type=utils.str2bool, required=False, default=False)
    parser.add_argument("--thread", "-t",
                        help="Set number of threads. Default is 5",
                        type=int, required=False, default=5)
    parser.add_argument("--cookie", help="Set cookie, format: \"name1=value1; name2=value2;\"",
                        type=str, required=False, default='')
    parser.add_argument("--config", "-F", 
                       type=argparse.FileType('r', encoding='utf-8'),
                       help="Configuration file path")
    args = parser.parse_args()
    if args.thread <= 0:
        args.thread = 5

    return args


def yamlConfig():
    curPath = os.path.dirname(os.path.realpath(sys.argv[0]))
    yamlPath = os.path.join(curPath, "config.yml")
    
    try:
        with open(yamlPath, 'r', encoding='utf-8') as f:
            configDict = yaml.safe_load(f)
            
        # Simplify configuration updates using dictionary comprehension
        for key in configModel:
            if key in configDict:
                if isinstance(configModel[key], dict):
                    configModel[key].update(configDict[key] or {})
                else:
                    configModel[key] = configDict[key]
                    
        # Special handling for cookie
        if configDict.get("cookies"):
            cookieStr = "; ".join(f"{k}={v}" for k,v in configDict["cookies"].items())
            configModel["cookie"] = cookieStr
            
        # Special handling for end_time
        if configDict.get("end_time") == "now":
                configModel["end_time"] = time.strftime("%Y-%m-%d", time.localtime())
            
    except FileNotFoundError:
        douyin_logger.warning("config.yml not found")
    except Exception as e:
        douyin_logger.warning(f"Error parsing configuration file: {str(e)}")


def validate_config(config: dict) -> bool:
    """Validate configuration effectiveness"""
    required_keys = {
        'link': list,
        'path': str,
        'thread': int
    }
    
    for key, typ in required_keys.items():
        if key not in config or not isinstance(config[key], typ):
            douyin_logger.error(f"Invalid configuration item: {key}")
            return False
            
    if not all(isinstance(url, str) for url in config['link']):
        douyin_logger.error("Invalid link configuration format")
        return False
        
    return True


def main():
    start = time.time()

    # Configuration initialization
    args = argument()
    if args.cmd:
        update_config_from_args(args)
    else:
        yamlConfig()

    if not validate_config(configModel):
        return

    if not configModel["link"]:
        douyin_logger.error("Download link not set")
        return

    # Cookie processing
    if configModel["cookie"]:
        douyin_headers["Cookie"] = configModel["cookie"]

    # Path processing
    configModel["path"] = os.path.abspath(configModel["path"])
    os.makedirs(configModel["path"], exist_ok=True)
    douyin_logger.info(f"Data save path: {configModel['path']}")

    # Initialize downloader
    dy = Douyin(database=configModel["database"])
    dl = Download(
        thread=configModel["thread"],
        music=configModel["music"],
        cover=configModel["cover"],
        avatar=configModel["avatar"],
        resjson=configModel["json"],
        folderstyle=configModel["folderstyle"]
    )

    # Process each link
    for link in configModel["link"]:
        process_link(dy, dl, link)

    # Calculate duration
    duration = time.time() - start
    douyin_logger.info(f'\n[Download Complete]: Total time: {int(duration/60)} minutes {int(duration%60)} seconds\n')


def process_link(dy, dl, link):
    """Process download logic for a single link"""
    douyin_logger.info("-" * 80)
    douyin_logger.info(f"[  Info  ]: Requesting link: {link}")
    
    try:
        url = dy.getShareLink(link)
        key_type, key = dy.getKey(url)
        
        handlers = {
            "user": handle_user_download,
            "mix": handle_mix_download,
            "music": handle_music_download,
            "aweme": handle_aweme_download,
            "live": handle_live_download
        }
        
        handler = handlers.get(key_type)
        if handler:
            handler(dy, dl, key)
        else:
            douyin_logger.warning(f"[  Warning  ]: Unknown link type: {key_type}")
    except Exception as e:
        douyin_logger.error(f"Error processing link: {str(e)}")


def handle_user_download(dy, dl, key):
    """Handle user homepage download"""
    douyin_logger.info("[  Info  ]: Requesting works on user homepage")
    data = dy.getUserDetailInfo(sec_uid=key)
    nickname = ""
    if data and data.get('user'):
        nickname = utils.replaceStr(data['user']['nickname'])

    userPath = os.path.join(configModel["path"], f"user_{nickname}_{key}")
    os.makedirs(userPath, exist_ok=True)

    for mode in configModel["mode"]:
        douyin_logger.info("-" * 80)
        douyin_logger.info(f"[  Info  ]: Requesting user homepage mode: {mode}")
        
        if mode in ('post', 'like'):
            _handle_post_like_mode(dy, dl, key, mode, userPath)
        elif mode == 'mix':
            _handle_mix_mode(dy, dl, key, userPath)

def _handle_post_like_mode(dy, dl, key, mode, userPath):
    """Handle download for post/like mode"""
    datalist = dy.getUserInfo(
        key, 
        mode, 
        35, 
        configModel["number"][mode], 
        configModel["increase"][mode],
        start_time=configModel.get("start_time", ""),
        end_time=configModel.get("end_time", "")
    )
    
    if not datalist:
        return
        
    modePath = os.path.join(userPath, mode)
    os.makedirs(modePath, exist_ok=True)
    
    dl.userDownload(awemeList=datalist, savePath=modePath)

def _handle_mix_mode(dy, dl, key, userPath):
    """Handle download for collection (mix) mode"""
    mixIdNameDict = dy.getUserAllMixInfo(key, 35, configModel["number"]["allmix"])
    if not mixIdNameDict:
        return
 
    modePath = os.path.join(userPath, "mix")
    os.makedirs(modePath, exist_ok=True)

    for mix_id, mix_name in mixIdNameDict.items():
        douyin_logger.info(f'[  Info  ]: Downloading works in collection [{mix_name}]')
        mix_file_name = utils.replaceStr(mix_name)
        datalist = dy.getMixInfo(
            mix_id, 
            35, 
            0, 
            configModel["increase"]["allmix"], 
            key,
            start_time=configModel.get("start_time", ""),
            end_time=configModel.get("end_time", "")
        )
        
        if datalist:
            dl.userDownload(awemeList=datalist, savePath=os.path.join(modePath, mix_file_name))
            douyin_logger.info(f'[  Info  ]: Download complete for works in collection [{mix_name}]')

def handle_mix_download(dy, dl, key):
    """Handle single collection download"""
    douyin_logger.info("[  Info  ]: Requesting works in single collection")
    try:
        datalist = dy.getMixInfo(
            key, 
            35, 
            configModel["number"]["mix"], 
            configModel["increase"]["mix"], 
            "",
            start_time=configModel.get("start_time", ""),
            end_time=configModel.get("end_time", "")
        )
        
        if not datalist:
            douyin_logger.error("Failed to obtain collection information")
            return
            
        mixname = utils.replaceStr(datalist[0]["mix_info"]["mix_name"])
        mixPath = os.path.join(configModel["path"], f"mix_{mixname}_{key}")
        os.makedirs(mixPath, exist_ok=True)
        dl.userDownload(awemeList=datalist, savePath=mixPath)
    except Exception as e:
        douyin_logger.error(f"Error processing collection: {str(e)}")

def handle_music_download(dy, dl, key):
    """Handle music work download"""
    douyin_logger.info("[  Info  ]: Requesting works under music (soundtrack)")
    datalist = dy.getMusicInfo(key, 35, configModel["number"]["music"], configModel["increase"]["music"])

    if datalist:
        musicname = utils.replaceStr(datalist[0]["music"]["title"])
        musicPath = os.path.join(configModel["path"], f"music_{musicname}_{key}")
        os.makedirs(musicPath, exist_ok=True)
        dl.userDownload(awemeList=datalist, savePath=musicPath)

def handle_aweme_download(dy, dl, key):
    """Handle single work download"""
    douyin_logger.info("[  Info  ]: Requesting single work")
    
    # Maximum retry count
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            douyin_logger.info(f"[  Info  ]: Attempt {retry_count+1} to obtain work information")
            result = dy.getAwemeInfo(key)
            
            if not result:
                douyin_logger.error("[  Error  ]: Failed to obtain work information")
                retry_count += 1
                if retry_count < max_retries:
                    douyin_logger.info("[  Info  ]: Waiting 5 seconds before retrying...")
                    time.sleep(5)
                continue
            
            # Use returned dictionary directly
            datanew = result
            
            if datanew:
                awemePath = os.path.join(configModel["path"], "aweme")
                os.makedirs(awemePath, exist_ok=True)
                
                # Check video URL before download
                video_url = datanew.get("video", {}).get("play_addr", {}).get("url_list", [])
                if not video_url or len(video_url) == 0:
                    douyin_logger.error("[  Error  ]: Unable to obtain video URL")
                    retry_count += 1
                    if retry_count < max_retries:
                        douyin_logger.info("[  Info  ]: Waiting 5 seconds before retrying...")
                        time.sleep(5)
                    continue
                    
                douyin_logger.info(f"[  Info  ]: Video URL obtained, preparing download")
                dl.userDownload(awemeList=[datanew], savePath=awemePath)
                douyin_logger.info(f"[  Success  ]: Video download complete")
                return True
            else:
                douyin_logger.error("[  Error  ]: Work data is empty")
                
            retry_count += 1
            if retry_count < max_retries:
                douyin_logger.info("[  Info  ]: Waiting 5 seconds before retrying...")
                time.sleep(5)
                
        except Exception as e:
            douyin_logger.error(f"[  Error  ]: Error processing work: {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                douyin_logger.info("[  Info  ]: Waiting 5 seconds before retrying...")
                time.sleep(5)
    
    douyin_logger.error("[  Failure  ]: Maximum retry count reached, unable to download video")

def handle_live_download(dy, dl, key):
    """Handle live download"""
    douyin_logger.info("[  Info  ]: Performing live parsing")
    live_json = dy.getLiveInfo(key)
    
    if configModel["json"] and live_json:
        livePath = os.path.join(configModel["path"], "live")
        os.makedirs(livePath, exist_ok=True)
        
        live_file_name = utils.replaceStr(f"{key}{live_json['nickname']}")
        json_path = os.path.join(livePath, f"{live_file_name}.json")
        
        douyin_logger.info("[  Info  ]: Saving obtained information to result.json")
        with open(json_path, "w", encoding='utf-8') as f:
            json.dump(live_json, f, ensure_ascii=False, indent=2)

# Conditionally define async function
if ASYNC_SUPPORT:
    async def download_file(url, path):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(path, 'wb') as f:
                        f.write(await response.read())
                    return True
        return False

def update_config_from_args(args):
    """Update configuration from command line arguments"""
    configModel["link"] = args.link
    configModel["path"] = args.path
    configModel["music"] = args.music
    configModel["cover"] = args.cover
    configModel["avatar"] = args.avatar
    configModel["json"] = args.json
    configModel["folderstyle"] = args.folderstyle
    configModel["mode"] = args.mode if args.mode else ["post"]
    configModel["thread"] = args.thread
    configModel["cookie"] = args.cookie
    configModel["database"] = args.database
    
    # Update number dictionary
    configModel["number"]["post"] = args.postnumber
    configModel["number"]["like"] = args.likenumber
    configModel["number"]["allmix"] = args.allmixnumber
    configModel["number"]["mix"] = args.mixnumber
    configModel["number"]["music"] = args.musicnumber
    
    # Update increase dictionary
    configModel["increase"]["post"] = args.postincrease
    configModel["increase"]["like"] = args.likeincrease
    configModel["increase"]["allmix"] = args.allmixincrease
    configModel["increase"]["mix"] = args.mixincrease
    configModel["increase"]["music"] = args.musicincrease

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
