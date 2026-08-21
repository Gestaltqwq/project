"""大模型服务：LLMService 类（openai 兼容协议）

【AI 方案 §3】模型 qwen/deepseek/glm 等 OpenAI 兼容服务；
未配 LLM_API_KEY 时 client=None，系统照常运行，仅邮件功能不可用。
"""
import json
import re
from typing import Optional

from app.core.config import settings

# AI 方案 §3.3：Prompt 四要素 = 角色设定 + 客户画像 + 任务要求 + 输出格式
DEFAULT_PROMPT_TEMPLATE = """你是资深保险营销文案专家。请根据以下客户画像，撰写一封专业且有温度的个性化车险营销邮件。

【客户画像】
- 性别：{gender}，年龄：{age}岁，{driving_license}驾照
- 车龄：{vehicle_age}，车辆是否曾受损：{vehicle_damage}
- 当前年保费：{annual_premium}元
- 购买意向评分：{predicted_prob}（0~1，越高意向越强）

【写作要求】
1. 结合客户的具体车龄、受损情况、保费水平，分析其车险需求痛点，给出针对性建议
2. 突出本司车险的核心保障价值，用具体场景说明（如事故理赔、维修保障）
3. 语气专业、亲切、有温度，符合资深保险顾问身份
4. 正文 300~500 字，结构完整：
   - 亲切的问候与称呼
   - 客户痛点/需求分析
   - 本司产品价值与个性化推荐
   - 明确的行动号召（CTA，如"立即预约专属顾问咨询"）
   - 落款与联系方式
5. 正文使用规范的 HTML 格式（<p>、<strong>、<ul> 等标签）

仅返回严格 JSON，不要任何其他文字或 markdown 包裹，格式：
{{"subject":"简洁有吸引力的邮件主题（≤20字）","content":"HTML格式的完整邮件正文"}}"""


class LLMService:
    def __init__(self):
        # 未配 API_KEY → client=None（降级，不阻断业务）
        self.client = None
        if settings.LLM_API_KEY:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=settings.LLM_API_KEY,
                    base_url=settings.LLM_API_BASE,
                    timeout=settings.LLM_TIMEOUT,
                )
            except ImportError:
                self.client = None

    def test_connection(self) -> bool:
        """测试连通性"""
        if not self.client:
            return False
        try:
            self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
            )
            return True
        except Exception:
            return False

    def generate_email(self, customer: dict, prompt_template: Optional[str] = None) -> dict:
        """生成营销邮件 → {success, subject, content, error, usage_tokens}

        - 失败返回 {success: False, error}（业务层据此标记 status=failed）
        - 严格 JSON 解析，兼容 markdown 包裹（```json）
        """
        if not self.client:
            return {"success": False, "error": "LLM_API_KEY 未配置"}

        prompt = (prompt_template or DEFAULT_PROMPT_TEMPLATE)
        prompt = _fill_customer(prompt, customer)  # 反编码为自然语言后填入

        try:
            resp = self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,  # AI 方案 §3.3：平衡创造力与稳定性
            )
            content = resp.choices[0].message.content.strip()
            # 清理 markdown 包裹
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)

            parsed = json.loads(content)
            subject = str(parsed.get("subject", ""))
            body = str(parsed.get("content", parsed if isinstance(parsed, str) else ""))
            return {
                "success": True,
                "subject": subject,
                "content": body,
                "usage_tokens": getattr(resp.usage, "total_tokens", None),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


def _fill_customer(template: str, customer: dict) -> str:
    """把客户编码值反编码为自然语言后填入模板（AI 方案 §4.1 语义还原）"""
    mapping = {
        "gender": "男" if customer.get("gender") == "Male" else "女",
        "age": str(customer.get("age", "")),
        "driving_license": "有" if customer.get("driving_license") else "无",
        "vehicle_age": str(customer.get("vehicle_age", "")),
        "vehicle_damage": "曾受损" if customer.get("vehicle_damage") == "Yes" else "无受损",
        "annual_premium": str(customer.get("annual_premium", "")),
        "predicted_prob": f"{customer.get('predicted_prob', 0):.2f}" if customer.get("predicted_prob") else "",
    }
    for key, val in mapping.items():
        template = template.replace("{" + key + "}", val)
    return template
