#调用AI对content打标签
import pandas as pd
import numpy as np
import google.generativeai as genai
from tqdm import tqdm
import time
import os
import json
from loguru import logger

GOOGLE_API_KEY = ""
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

#输入提示词
SYSTEM_PROMPT = """
你是一个 flomo 笔记软件的产品分析师。
你的任务是读取一条用户评论，并严格按照以下 JSON 格式进行分类：

{
  "topic": "...",
  "sentiment": "...",
  "type": "..."
}

合法的 "topic" 标签有: 
['同步', '编辑', '搜索', 'UI/设计', '价格', 'API/集成', '回顾', '竞品对比', '其他']

合法的 "sentiment" 标签有: 
['赞美', '建议', '痛点/抱怨', 'Bug报告', '疑问', '中性']

合法的 "type" 标签有: 
['功能请求', '使用场景', '问题反馈', '纯粹表扬', '无关']

如果评论内容无法判断，请在对应字段填入 "N/A"。
现在，请分析这条评论：
"""

def classify_comment(comment_content):
    """调用 AI API 来分类单条评论"""
    try:
        # 完整的提示词 = 系统指令 + 用户评论
        full_prompt = SYSTEM_PROMPT + comment_content
        
        response = model.generate_content(full_prompt)
        
        # 从 AI 的回复中提取 JSON 部分
        # (AI回复可能包含 "```json\n ... \n```", 需要解析)
        json_str = response.text.strip().replace('```json', '').replace('```', '')
        
        # 解析 JSON 字符串
        result_json = json.loads(json_str)
        return result_json
        
    except Exception as e:
        logger.error(f"分析失败: {e} | 内容: {comment_content[:20]}...")
        return {"topic": "Error", "sentiment": "Error", "type": "Error"}

# 3. 主程序：读取 Excel，处理，保存
def main():
    df_sample = pd.read_excel('output.xlsx')

    # 用 .apply() 来为每一行调用 AI
    logger.info("开始调用 AI 进行分类...")
    
    # 用一个列表来收集结果
    results = []
    for index, row in df_sample.iterrows():
        comment = row['content'] 
        if pd.isna(comment):
            results.append({})
            continue
            
        logger.info(f"正在分析第 {index} 条: {comment[:30]}...")
        ai_result = classify_comment(comment)
        results.append(ai_result)
        
        time.sleep(1) # 免费 API 有速率限制，每秒调一次
        
    # 将 JSON 结果列表转换成 DataFrame
    df_results = pd.DataFrame(results)
    
    # 将新生成的标签合并回原有的 DataFrame
    df_sample_classified = pd.concat([df_sample.reset_index(drop=True), df_results], axis=1)

    # 5. 保存到新的 Excel 文件
    logger.info("分析完成，正在保存到 output2.xlsx")
    df_sample_classified.to_excel("output2.xlsx", index=False)

if __name__ == "__main__":
    main()

