import re

string = '4.64 h@o.DU 09/19 vSY:/ 先让雪球走，再去追，最后抱住，渝爱太会玩了 # 大熊猫渝爱 # 渝爱  https://v.douyin.com/ApwLGpzCqnE/ 复制此链接，打开Dou音搜索，直接观看视频！'
# Regex from apiproxy/douyin/douyin.py line 53
regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

try:
    matches = re.findall(regex, string)
    print(f"Input: {string}")
    print(f"Matches: {matches}")
    if matches:
        print(f"Extracted: {matches[0]}")
    else:
        print("No match found")
except Exception as e:
    print(f"Error: {e}")
