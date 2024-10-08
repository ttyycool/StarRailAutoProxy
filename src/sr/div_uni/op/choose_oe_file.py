import time
from typing import Optional

from basic import str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.context.context import Context, get_context
from sr.div_uni.screen_div_uni import ScreenDivUni
from sr.operation import StateOperation, OperationOneRoundResult, StateOperationNode
from sr.screen_area.screen_phone_menu import ScreenPhoneMenu


class ChooseOeFile(StateOperation):

    def __init__(self, ctx: Context, num: int):
        """
        选择存档 最终返回【位面饰品提取】画面
        """
        super().__init__(ctx, op_name=gt('选择存档', 'ui'))

        self.num: int = num
        """需要选择的存档编号 0代表不选"""

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """
        if self.num < 1 or self.num > 4:
            return self.round_fail('存档编号只能是1~4')

        if self.num == 0:
            return self.round_success('使用默认档案')

        return None

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        # 开始初始化指令结构
        _check_screen = StateOperationNode('识别画面', self.check_screen)

        _click_switch_file = StateOperationNode('点击切换存档', self.click_switch_file)
        self.add_edge(_check_screen, _click_switch_file, status=ScreenDivUni.OE_TITLE.value.status)

        _wait = StateOperationNode('等待存档管理画面', self.wait_management_screen)
        self.add_edge(_click_switch_file, _wait)

        _choose_file = StateOperationNode('选择存档', self.choose_file)
        self.add_edge(_check_screen, _choose_file, status=ScreenDivUni.OE_FILE_MANAGEMENT_TITLE.value.status)
        self.add_edge(_wait, _choose_file)

    def check_screen(self) -> OperationOneRoundResult:
        """
        识别当前所在的画面
        :return:
        """
        screen = self.screenshot()

        area = ScreenDivUni.OE_TITLE.value
        if self.find_area(area, screen):
            return self.round_success(area.status)

        area = ScreenDivUni.OE_FILE_MANAGEMENT_TITLE.value
        if self.find_area(area, screen):
            return self.round_success(area.status)

        return self.round_retry(status='未在指定页面', wait_round_time=1)

    def click_switch_file(self) -> OperationOneRoundResult:
        """
        点击切换存档
        :return:
        """
        screen = self.screenshot()
        area = ScreenDivUni.OE_SWITCH_FILE_BTN.value
        return self.round_by_find_and_click_area(screen, area, success_wait=1.5, retry_wait_round=0.5)

    def wait_management_screen(self) -> OperationOneRoundResult:
        """
        等待选择存档的画面
        :return:
        """
        screen = self.screenshot()

        area = ScreenDivUni.OE_FILE_MANAGEMENT_TITLE.value
        if self.find_area(area, screen):
            return self.round_success(area.status)
        else:
            return self.round_retry(f'未在{area.status}画面', wait_round_time=0.5)

    def choose_file(self) -> OperationOneRoundResult:
        """
        选择存档
        :return:
        """
        file_areas = [
            ScreenDivUni.OE_FILE_1.value,
            ScreenDivUni.OE_FILE_2.value,
            ScreenDivUni.OE_FILE_3.value,
            ScreenDivUni.OE_FILE_4.value
        ]

        # 点击存档 由于每个存档的名字都不一样 就不使用OCR识别了
        area = file_areas[self.num - 1]
        self.ctx.controller.click(area.center)
        time.sleep(0.25)

        screen = self.screenshot()
        area1 = ScreenDivUni.OE_CONFIRM_SWITCH_BTN.value
        area2 = ScreenDivUni.OE_FILE_USING_BTN.value
        part = cv2_utils.crop_image_only(screen, area1.rect)
        ocr_result = self.ctx.ocr.run_ocr_single_line(part)

        if str_utils.find_by_lcs(ocr_result, area1.text, percent=area1.lcs_percent):
            self.ctx.controller.click(area1.center)
            return self.round_success(wait=1.5)  # 选择后 等待一会返回外层界面
        elif str_utils.find_by_lcs(ocr_result, area2.text, percent=area2.lcs_percent):  # 已经在使用了 返回即可
            self.ctx.controller.click(ScreenPhoneMenu.EXIT_BTN.value.center)
            return self.round_success(wait=1.5)  # 选择后 等待一会返回外层界面
        else:
            return self.round_retry(f'点击{area1.status}失败', wait_round_time=0.5)


def __debug_op():
    ctx = get_context()
    ctx.start_running()

    op = ChooseOeFile(ctx, 2)
    op.execute()


if __name__ == '__main__':
    __debug_op()
