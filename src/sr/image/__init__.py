from typing import List

import numpy as np
from cv2.typing import MatLike

from basic.img import MatchResultList
from sr.image.image_holder import TemplateImage


class ImageMatcher:

    def get_template(self, template_id: str) -> TemplateImage:
        """
        获取对应模板图片
        :param template_id: 模板id
        :return: 模板图片
        """
        pass

    def match_image(self, source: MatLike, template: MatLike,
                    threshold: float = 0.5, mask: np.ndarray = None,
                    ignore_inf: bool = True):
        """
        在原图中 匹配模板
        :param source: 原图
        :param template: 模板图片
        :param threshold: 匹配阈值
        :param mask: 掩码
        :param ignore_inf: 是否忽略无限大的结果
        :return: 所有匹配结果
        """
        pass

    def match_template(self, source: MatLike, template_id: str, template_type: str = 'origin',
                       threshold: float = 0.5,
                       mask: np.ndarray = None,
                       ignore_template_mask: bool = False,
                       ignore_inf: bool = True) -> MatchResultList:
        """
        在原图中 匹配模板 如果模板图中有掩码图 会自动使用
        :param source: 原图
        :param template_id: 模板id
        :param template_type: 使用哪种类型模板
        :param threshold: 匹配阈值
        :param mask: 额外使用的掩码 与原模板掩码叠加
        :param ignore_template_mask: 是否忽略模板自身的掩码
        :param ignore_inf: 是否忽略无限大的结果
        :return: 所有匹配结果
        """
        pass

    def match_template_with_rotation(self, source: MatLike, template_id: str,
                                     threshold: float = 0.5,
                                     mask: np.ndarray = None,
                                     ignore_inf: bool = True) -> dict:
        """
        在原图中 对模板进行360度旋转匹配
        :param source: 原图
        :param template_id: 模板id
        :param threshold: 匹配阈值
        :param mask: 掩码
        :param ignore_inf: 是否忽略无限大的结果
        :return: 每个选择角度的匹配结果
        """
        pass


class OcrMatcher:

    def run_ocr(self, image: MatLike, threshold: float = 0.5) -> dict:
        """
        对图片进行OCR 返回所有匹配结果
        :param image: 图片
        :param threshold: 匹配阈值
        :return: {key_word: []}
        """
        pass

    def match_words(self, image: MatLike, words: List[str], threshold: float = 0.5) -> dict:
        """
        在图片中查找关键词 返回所有词对应的位置
        :param image: 图片
        :param words: 关键词
        :param threshold: 匹配阈值
        :return: {key_word: []}
        """
        all_match_result: dict = self.run_ocr(image, threshold)
        match_key = set()
        for k in all_match_result.keys():
            for w in words:
                if k.find(w) != -1:
                    match_key.add(k)
                    break

        return {key: all_match_result[key] for key in match_key if key in all_match_result}
