# 第二種讓群益API元件可導入Python code內用的物件宣告
import comtypes.client
import os

# 載入SKCOM.dll (確保在當前目錄)
dll_path = os.path.split(os.path.realpath(__file__))[0] + r'\SKCOM.dll'
if os.path.exists(dll_path):
    comtypes.client.GetModule(dll_path)
    print(f"✅ 成功載入SKCOM.dll: {dll_path}")
else:
    print(f"❌ 找不到SKCOM.dll: {dll_path}")

import comtypes.gen.SKCOMLib as sk

# 初始化Global_IID變數
Global_IID = None

def SetID(id):
    iid = id
    global Global_IID
    Global_IID = iid
    print(f"🔧 [Global] SetID called: {Global_IID}")

global skO, skC, skQ, skR, skOSQ, skOOQ

skO = comtypes.client.CreateObject(sk.SKOrderLib,interface=sk.ISKOrderLib)

skC = comtypes.client.CreateObject(sk.SKCenterLib,interface=sk.ISKCenterLib)

skQ = comtypes.client.CreateObject(sk.SKQuoteLib,interface=sk.ISKQuoteLib)

skR = comtypes.client.CreateObject(sk.SKReplyLib,interface=sk.ISKReplyLib)

skOSQ = comtypes.client.CreateObject(sk.SKOSQuoteLib,interface=sk.ISKOSQuoteLib)

skOOQ = comtypes.client.CreateObject(sk.SKOOQuoteLib,interface=sk.ISKOOQuoteLib)
