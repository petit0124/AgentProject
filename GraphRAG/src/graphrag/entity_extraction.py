"""实体抽取模块 - 从文本中识别实体和关系"""
import json
import re
from typing import List, Dict, Any, Optional
from loguru import logger


class EntityExtractor:
    """实体抽取器 - 使用LLM从文本中提取实体和关系"""
    
    # 支持的实体类型
    ENTITY_TYPES = [
        "PERSON",          # 人物
        "ORGANIZATION",    # 组织
        "LOCATION",        # 地点
        "EVENT",           # 事件
        "CONCEPT",         # 概念
        "TECHNOLOGY",      # 技术
        "PRODUCT",         # 产品
        "DATE",            # 日期
        "OTHER",           # 其他
    ]
    
    def __init__(self, llm_adapter):
        """初始化实体抽取器
        
        Args:
            llm_adapter: LLM适配器
        """
        self.llm_adapter = llm_adapter
    
    def extract_entities_and_relations(
        self,
        text: str,
        chunk_id: str,
    ) -> Dict[str, Any]:
        """从文本中提取实体和关系
        
        Args:
            text: 输入文本
            chunk_id: 文本块ID
            
        Returns:
            包含实体和关系的字典
        """
        logger.info(f"正在从文本块 {chunk_id} 提取实体...")
        
        try:
            # 构建提取prompt
            prompt = self._build_extraction_prompt(text)
            
            # 调用LLM
            response = self.llm_adapter.generate(
                prompt=prompt,
                system_prompt=self._get_system_prompt(),
                temperature=0.0,
            )
            
            # 解析响应
            result = self._parse_response(response, chunk_id)
            
            logger.info(f"提取到 {len(result['entities'])} 个实体, {len(result['relationships'])} 个关系")
            
            return result
            
        except Exception as e:
            logger.error(f"实体抽取失败: {e}")
            return {
                "entities": [],
                "relationships": [],
                "source_chunk": chunk_id
            }
    
    def _get_system_prompt(self) -> str:
        """获取系统prompt"""
        return """你是一个专业的知识图谱构建助手。你的任务是从文本中准确提取实体和它们之间的关系。

要求：
1. 仔细阅读文本，识别所有重要的实体
2. 确定实体之间的语义关系
3. 以JSON格式返回结果
4. 确保提取的信息准确且有意义"""
    
    def _build_extraction_prompt(self, text: str) -> str:
        """构建实体抽取prompt"""
        entity_types_str = ", ".join(self.ENTITY_TYPES)
        
        prompt = f"""请从以下文本中提取所有相关的实体和关系。

## 实体类型
支持的实体类型包括：{entity_types_str}

## 文本内容
{text}

## 输出格式
请以JSON格式返回，包含以下字段：

```json
{{
  "entities": [
    {{
      "name": "实体名称",
      "type": "实体类型（从上述类型中选择）",
      "description": "简短描述（1-2句话）"
    }}
  ],
  "relationships": [
    {{
      "source": "源实体名称",
      "target": "目标实体名称", 
      "type": "关系类型（如：创建、属于、位于、影响等）",
      "description": "关系描述"
    }}
  ]
}}
```

## 注意事项
- 只提取文本中明确提到的实体
- 关系必须基于文本中的实际内容
- 实体名称要准确且一致
- 如果没有明确的实体或关系，返回空列表

请开始提取："""
        
        return prompt
    
    def _parse_response(self, response: str, chunk_id: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 处理响应可能是list的情况
            if isinstance(response, list):
                # 如果是list，取第一个元素或合并
                if response:
                    response = response[0] if isinstance(response[0], str) else str(response[0])
                else:
                    response = "{}"
            
            # 确保response是字符串
            response = str(response)
            
            # 尝试从响应中提取JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
            else:
                # 如果没有找到JSON，尝试整体解析
                data = json.loads(response)
            
            # 验证和标准化数据
            entities = []
            for entity in data.get("entities", []):
                if "name" in entity and "type" in entity:
                    entities.append({
                        "name": entity["name"].strip(),
                        "type": entity.get("type", "OTHER").upper(),
                        "description": entity.get("description", ""),
                        "source_chunk": chunk_id
                    })
            
            relationships = []
            for rel in data.get("relationships", []):
                if "source" in rel and "target" in rel:
                    relationships.append({
                        "source": rel["source"].strip(),
                        "target": rel["target"].strip(),
                        "type": rel.get("type", "RELATED_TO"),
                        "description": rel.get("description", ""),
                        "source_chunk": chunk_id
                    })
            
            return {
                "entities": entities,
                "relationships": relationships,
                "source_chunk": chunk_id
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"响应内容: {str(response)[:200]}...")
            return {
                "entities": [],
                "relationships": [],
                "source_chunk": chunk_id
            }
        except Exception as e:
            logger.error(f"响应解析失败: {e}")
            logger.error(f"响应类型: {type(response)}, 内容: {str(response)[:200]}...")
            return {
                "entities": [],
                "relationships": [],
                "source_chunk": chunk_id
            }
    
    def deduplicate_entities(self, all_entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """实体去重和合并
        
        Args:
            all_entities: 所有提取的实体列表
            
        Returns:
            去重后的实体列表
        """
        logger.info(f"开始去重 {len(all_entities)} 个实体...")
        
        # 使用实体名称作为key进行去重
        entity_map = {}
        
        for entity in all_entities:
            name = entity["name"].lower()
            
            if name not in entity_map:
                entity_map[name] = entity
            else:
                # 合并描述
                existing = entity_map[name]
                if entity.get("description") and entity["description"] not in existing.get("description", ""):
                    existing["description"] = f"{existing.get('description', '')} {entity['description']}".strip()
                
                # 合并来源
                if "source_chunks" not in existing:
                    existing["source_chunks"] = [existing.pop("source_chunk", "")]
                if entity.get("source_chunk"):
                    existing["source_chunks"].append(entity["source_chunk"])
        
        deduplicated = list(entity_map.values())
        logger.info(f"去重后剩余 {len(deduplicated)} 个实体")
        
        return deduplicated
    
    def deduplicate_relationships(self, all_relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """关系去重
        
        Args:
            all_relationships: 所有提取的关系列表
            
        Returns:
            去重后的关系列表
        """
        logger.info(f"开始去重 {len(all_relationships)} 个关系...")
        
        # 使用 (source, target, type) 作为key
        rel_map = {}
        
        for rel in all_relationships:
            key = (
                rel["source"].lower(),
                rel["target"].lower(),
                rel.get("type", "RELATED_TO")
            )
            
            if key not in rel_map:
                rel_map[key] = rel
        
        deduplicated = list(rel_map.values())
        logger.info(f"去重后剩余 {len(deduplicated)} 个关系")
        
        return deduplicated
