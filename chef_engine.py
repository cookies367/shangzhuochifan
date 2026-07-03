#!/usr/bin/env python3
"""
AI 厨师引擎 (Chef Engine)
负责接管游戏中的"回家做饭"环节，实现：
1. AI 自主决定做哪道菜（可自由发挥加食材）
2. AI 根据 mood 随机选择烹饪态度（认真/随意/醋意/恶搞）
3. 综合厨艺等级、熟练度、难度和态度，计算结果
4. 恶搞不涨经验，其他全涨
"""
import random
from market_data import ATTITUDE_RULES, MOOD_LIST, SPECIAL_RESULTS, VEGGIES, ITEM_SENSE_CAT

# 心情 → 态度权重映射（心情决定概率分布）
MOOD_ATTITUDE_WEIGHTS = {
    "happy":    {"Serious": 40, "Careless": 20, "Jealous": 5,  "Playful": 35},
    "normal":   {"Serious": 50, "Careless": 30, "Jealous": 10, "Playful": 10},
    "annoyed":  {"Serious": 20, "Careless": 50, "Jealous": 25, "Playful": 5},
    "jealous":  {"Serious": 15, "Careless": 15, "Jealous": 65, "Playful": 5},
    "playful":  {"Serious": 10, "Careless": 20, "Jealous": 5,  "Playful": 65},
    "tired":    {"Serious": 15, "Careless": 65, "Jealous": 10, "Playful": 10},
    "excited":  {"Serious": 35, "Careless": 15, "Jealous": 5,  "Playful": 45},
}


class ChefEngine:
    """AI 厨师核心逻辑"""

    def __init__(self, game_state):
        """
        :param game_state: 主游戏引擎对象（需要读 chef_status 和 recipe_book）
        """
        self.game = game_state
        self.chef = game_state.chef_status
        self.recipes = game_state.recipe_book

    def roll_mood(self):
        """每天早上 Roll 一次今日心情"""
        mood = random.choice(MOOD_LIST)
        self.chef["mood"] = mood
        return mood

    def roll_attitude(self):
        """根据心情随机抽取今日烹饪态度"""
        mood = self.chef.get("mood", "normal")
        weights_dict = MOOD_ATTITUDE_WEIGHTS.get(mood, MOOD_ATTITUDE_WEIGHTS["normal"])
        attitudes = list(weights_dict.keys())
        weights = list(weights_dict.values())
        choice = random.choices(attitudes, weights=weights, k=1)[0]
        self.chef["attitude"] = choice
        return choice

    def get_attitude_desc(self, attitude_key):
        """获取态度的演出文案"""
        rule = ATTITUDE_RULES.get(attitude_key, ATTITUDE_RULES["Serious"])
        return random.choice(rule.get("desc_pool", ["TA开始做饭了。"]))

    def calculate_success(self, recipe_id, attitude_key):
        """
        核心计算：判定本次烹饪的成功率
        公式：基础厨艺*2 + 熟练度*0.5 - 难度*10 + 态度修正 + 随机数
        """
        recipe = self.recipes.get(recipe_id, {})
        difficulty = recipe.get("difficulty", 3)
        proficiency = recipe.get("proficiency", 0)
        base_level = self.chef.get("cooking_level", 10)

        # 成功率基准值
        base_score = base_level * 2 + proficiency * 0.5 - difficulty * 10
        
        # 态度修正
        attitude_bonus = ATTITUDE_RULES.get(attitude_key, {}).get("success_bonus", 0)
        
        # 最终分数（百分制）
        final_score = base_score + attitude_bonus + random.randint(-15, 15)
        
        # 恶搞态度强制偏向恶作剧结果
        if attitude_key == "Playful":
            if random.random() < 0.7:
                return "prank"
        
        # 判定结果档位
        if final_score >= 85:
            return "perfect"
        elif final_score >= 60:
            return "normal"
        elif final_score >= 35:
            return "flaw"   # 有点小瑕疵
        else:
            # 认真态度保底——低级厨师再菜也不至于炸厨房
            if attitude_key == "Serious":
                return "flaw"  # 至少"味道一般/有点咸了"，不会直接炸
            if attitude_key == "Jealous":
                return "flaw"  # 醋意重但不至于搞砸
            return "disaster"

    def generate_outcome(self, result_type, attitude_key, recipe_id=None, custom_ingredients=None):
        """
        根据计算结果和态度生成最终的演出文案
        """
        recipe_name = self.recipes.get(recipe_id, {}).get("name", "这道菜")
        custom_ingredients = custom_ingredients or []
        
        attitude_desc = self.get_attitude_desc(attitude_key)
        
        outcome_lines = [f"🍳 {attitude_desc}"]
        
        # 食材列表
        if custom_ingredients:
            outcome_lines.append(f"TA决定用这些来做：{'、'.join(custom_ingredients)}")

        # 中间过程（极简版，主要靠态度演出）
        if attitude_key == "Playful":
            outcome_lines.append("TA往锅里加了点完全不相干的东西，一边做一边坏笑。")
        elif attitude_key == "Jealous":
            outcome_lines.append("TA边切菜边嘀咕着什么，力气明显大了点。")

        # 结果文案
        result_descs = {
            "perfect": [
                f"「{recipe_name}」做好了。色香味俱全！",
                "完美！火候拿捏得刚刚好，摆盘也像模像样。"
            ],
            "normal": [
                f"「{recipe_name}」端上桌了。虽然普通，但味道还行。",
                "做完了。看着一般，但吃着还行。"
            ],
            "flaw": [
                f"「{recipe_name}」做好了……稍微有点小瑕疵。",
                "菜做好了。颜色看着一般，可能差了点火候。"
            ],
            "disaster": [
                f"「{recipe_name}」……翻车了。厨房一片狼藉。",
                "锅里冒出一阵黑烟。TA尴尬地把一块不明物体铲到盘子里。"
            ],
            "prank": [
                "TA端着盘子走出来，脸上带着得意的笑容——这绝对不是正常菜。",
                "这道菜的卖相非常可疑。"
            ]
        }
        outcome_lines.append(random.choice(result_descs.get(result_type, result_descs["normal"])))

        # 特殊结果（非完美时可能触发）
        if result_type != "perfect":
            # 触发概率 40%
            if random.random() < 0.4:
                # 根据结果类型和态度筛选特殊事件
                if result_type == "prank" or attitude_key == "Playful":
                    pool = ["sugar_salt", "mystery_meat", "soul_food"]
                elif result_type == "disaster":
                    pool = ["burnt", "rubber"]
                elif result_type == "flaw":
                    pool = ["no_salt", "rubber"]
                else:
                    pool = ["soul_food", "no_salt"]
                
                special_key = random.choice(pool)
                special = SPECIAL_RESULTS.get(special_key)
                if special:
                    outcome_lines.append(f"⚠️ 【{special['name']}】{special['desc']}")

        return "\n".join(outcome_lines)

    def settle_exp(self, result_type, attitude_key, recipe_id):
        """
        结算经验值。
        规则：只要不是恶搞(Playful)态度，厨艺和熟练度必定上涨。
        """
        attitude_rule = ATTITUDE_RULES.get(attitude_key, {})
        exp_gain_text = []
        
        if attitude_rule.get("no_exp_gain"):
            exp_gain_text.append("（恶搞做饭不积累经验，纯属瞎玩。）")
            return "\n".join(exp_gain_text)

        # 涨厨艺等级
        old_level = self.chef.get("cooking_level", 10)
        # 难度越高的菜涨得越多，翻车也能学到教训
        recipe = self.recipes.get(recipe_id, {})
        difficulty = recipe.get("difficulty", 3)
        
        level_gain = 1 + difficulty // 3  # 难度1-2涨1点，3-5涨2点，6+涨3点
        if result_type == "perfect":
            level_gain += 1
        
        new_level = old_level + level_gain
        self.chef["cooking_level"] = new_level
        exp_gain_text.append(f"✨ 厨艺等级：{old_level} → {new_level}")

        # 涨熟练度
        old_prof = recipe.get("proficiency", 0)
        new_prof = min(100, old_prof + random.randint(8, 15))
        
        if recipe_id in self.recipes:
            self.recipes[recipe_id]["proficiency"] = new_prof
            if old_prof == 0:
                exp_gain_text.append(f"📝 「{self.recipes[recipe_id].get('name', recipe_id)}」首次制作，熟练度解锁！({new_prof}/100)")
            elif old_prof < 100:
                exp_gain_text.append(f"📝 「{self.recipes[recipe_id].get('name', recipe_id)}」熟练度：{old_prof} → {new_prof}")
            if new_prof == 100:
                exp_gain_text.append(f"🎓 「{self.recipes[recipe_id].get('name', recipe_id)}」熟练度已满！以后做这道菜稳如老狗。")

        return "\n".join(exp_gain_text)

    def improvise_cook(self, ingredients, forced_attitude=None):
        """
        强行制作：根据现有食材匹配最接近的菜谱，生成怪名菜。
        :param ingredients: 玩家手头的食材列表 ["肉末", "小白菜"]
        :param forced_attitude: 可指定态度
        """
        attitude_key = forced_attitude or self.roll_attitude()
        
        # 找食材重合度最高的菜谱
        best_match = None
        best_overlap = 0
        for rid, recipe in self.recipes.items():
            overlap = len(set(ingredients) & set(recipe.get("ingredients", [])))
            if overlap > best_overlap:
                best_overlap = overlap
                best_match = rid
        
        # 生成菜名
        ing_str = "、".join(ingredients)
        if best_match and best_overlap >= 1:
            base_name = self.recipes[best_match].get("name", best_match)
            weird_name = f"{ing_str}之{base_name}风味版"
            recipe_id = best_match
            difficulty_mod = 1  # 有参考菜谱，难度+1
        else:
            weird_name = f"乱炖{ing_str}"
            recipe_id = None  # 走神秘料理逻辑
            difficulty_mod = 3
        
        # 创建临时菜谱
        temp_id = f"improv_{hash(ing_str) % 10000}"
        self.recipes[temp_id] = {
            "name": weird_name,
            "difficulty": self.recipes.get(recipe_id, {}).get("difficulty", 3) + difficulty_mod if recipe_id else 4 + difficulty_mod,
            "proficiency": 0,
            "type": "improvised"
        }
        
        # 走正常烹饪流程
        result_type = self.calculate_success(temp_id, attitude_key)
        outcome = self.generate_outcome(result_type, attitude_key, temp_id, ingredients)
        exp_text = self.settle_exp(result_type, attitude_key, temp_id)
        
        # 组装输出
        mood_name_map = {"happy": "开心", "normal": "平静", "annoyed": "烦躁",
                         "jealous": "吃醋", "playful": "想玩", "tired": "疲惫", "excited": "兴奋"}
        attitude_name = ATTITUDE_RULES.get(attitude_key, {}).get("name", attitude_key)
        
        final_output = [
            f"🧑‍🍳 今日心情：{mood_name_map.get(self.chef.get('mood'), '?')} | 烹饪态度：{attitude_name}",
            "",
            f"📦 只有{ing_str}，TA决定强行制作——",
            f"🍳 {weird_name}",
            "",
            outcome,
            ""
        ]
        if exp_text:
            final_output.append(exp_text)
        
        return "\n".join(final_output)

    def cook(self, recipe_id=None, custom_ingredients=None, forced_attitude=None):
        """
        完整的烹饪流程入口。
        AI 可以传入 recipe_id（已有菜谱），或只传 custom_ingredients（自由发挥）。
        """
        # 1. 决定态度
        attitude_key = forced_attitude or self.roll_attitude()
        
        # 2. 如果没有指定 recipe_id，临时生成一个"神秘料理"
        if not recipe_id or recipe_id not in self.recipes:
            temp_id = "mystery_dish"
            self.recipes[temp_id] = {
                "name": "神秘料理",
                "difficulty": 4,
                "proficiency": 0,
                "type": "dark_cuisine"
            }
            recipe_id = temp_id

        # 3. 计算成功率
        result_type = self.calculate_success(recipe_id, attitude_key)
        
        # 4. 生成演出
        outcome = self.generate_outcome(result_type, attitude_key, recipe_id, custom_ingredients)
        
        # 5. 结算经验
        exp_text = self.settle_exp(result_type, attitude_key, recipe_id)
        
        # 6. 组装最终输出
        mood_name_map = {"happy": "开心", "normal": "平静", "annoyed": "烦躁", 
                         "jealous": "吃醋", "playful": "想玩", "tired": "疲惫", "excited": "兴奋"}
        attitude_name = ATTITUDE_RULES.get(attitude_key, {}).get("name", attitude_key)
        
        final_output = []
        final_output.append(f"🧑‍🍳 今日心情：{mood_name_map.get(self.chef.get('mood'), '?')} | 烹饪态度：{attitude_name}")
        final_output.append("")
        final_output.append(outcome)
        final_output.append("")
        if exp_text:
            final_output.append(exp_text)
        
        return "\n".join(final_output)