import time
from typing import ClassVar, List, Optional

from cv2.typing import MatLike

from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import mini_map, screen_state
from sr.operation import Operation, OperationOneRoundResult
from sr.operation.unit.technique import UseTechnique
from sr.screen_area.dialog import ScreenDialog


class EnterAutoFight(Operation):
    ATTACK_INTERVAL: ClassVar[float] = 0.2  # 发起攻击的间隔
    EXIT_AFTER_NO_ALTER_TIME: ClassVar[int] = 2  # 多久没警报退出
    EXIT_AFTER_NO_BATTLE_TIME: ClassVar[int] = 20  # 持续多久没有进入战斗画面就退出 这时候大概率是小地图判断被怪物锁定有问题
    ATTACK_DIRECTION_ARR: ClassVar[List] = ['w', 's', 'a', 'd']

    STATUS_ENEMY_NOT_FOUND: ClassVar[str] = '未发现敌人'
    STATUS_BATTLE_FAIL: ClassVar[str] = '战斗失败'

    def __init__(self, ctx: Context, use_technique: bool = False,
                 first_state: Optional[str] = None):
        """
        根据小地图的红圈 判断是否被敌人锁定 进行主动攻击
        """
        super().__init__(ctx, op_name=gt('进入战斗', 'ui'))
        self.last_attack_time: float = 0
        self.last_alert_time: float = 0  # 上次警报时间
        self.last_not_in_world_time: float = 0  # 上次不在移动画面的时间
        self.last_state: str = ''  # 上一次的画面状态
        self.current_state: str = ''  # 这一次的画面状态
        self.with_battle: bool = False  # 是否有进入战斗
        self.attack_direction: int = 0  # 攻击方向
        self.use_technique: bool = use_technique  # 使用秘技开怪
        self.first_state: Optional[str] = first_state  # 初始画面状态 传入后会跳过第一次画面状态判断
        self.first_screen_check: bool = True  # 是否第一次检查画面状态

    def _init_before_execute(self):
        super()._init_before_execute()
        self.last_attack_time = time.time()
        self.last_alert_time = time.time()  # 上次警报时间
        self.last_not_in_world_time = time.time() - 1.5  # 上次不在移动画面的时间
        self.attack_direction: int = 0  # 攻击方向
        self.first_screen_check: bool = True  # 是否第一次检查画面状态

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        self.last_state = self.current_state

        if self.first_screen_check and self.first_state is not None:
            self.current_state = self.first_state
        else:
            self.current_state = screen_state.get_world_patrol_screen_state(
                screen, self.ctx.im, self.ctx.ocr,
                in_world=True, battle=True, battle_fail=True,
                fast_recover=self.use_technique)

        self.first_screen_check = False

        if self.current_state == screen_state.ScreenState.NORMAL_IN_WORLD.value:
            self._update_in_world()
            round_result = self._try_attack(screen)
            if self.ctx.controller.is_moving:  # 攻击之后再停止移动 避免停止移动的后摇
                self.ctx.controller.stop_moving_forward()
            return round_result
        elif self.current_state == screen_state.ScreenState.BATTLE_FAIL.value:
            self.ctx.controller.click(screen_state.TargetRect.EMPTY_TO_CLOSE.value.center)
            return Operation.round_fail(EnterAutoFight.STATUS_BATTLE_FAIL, wait=5)
        elif self.current_state == ScreenDialog.FAST_RECOVER_TITLE.value.text:
            result = self._recover_technique_point()
            self._update_not_in_world_time()  # 恢复秘技点的时间不应该在计算内
            return result
        elif self.current_state == screen_state.ScreenState.BATTLE.value:
            return self._in_battle()
        else:
            return Operation.round_retry('未知画面', wait=1)

    def _update_in_world(self):
        """
        在大世界画面的更新
        :return:
        """
        if self.last_state != screen_state.ScreenState.NORMAL_IN_WORLD.value:
            self._update_not_in_world_time()

    def _try_attack(self, screen: MatLike) -> OperationOneRoundResult:
        """
        尝试主动攻击
        :param screen: 屏幕截图
        :return:
        """
        now_time = time.time()
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        if not mini_map.is_under_attack(mm, self.ctx.game_config.mini_map_pos, strict=True):
            if now_time - self.last_alert_time > EnterAutoFight.EXIT_AFTER_NO_ALTER_TIME:
                return Operation.round_success(None if self.with_battle else EnterAutoFight.STATUS_ENEMY_NOT_FOUND)
        else:
            self.last_alert_time = now_time

        if now_time - self.last_not_in_world_time > EnterAutoFight.EXIT_AFTER_NO_BATTLE_TIME:
            return Operation.round_success(None if self.with_battle else EnterAutoFight.STATUS_ENEMY_NOT_FOUND)

        if self.use_technique and not self.ctx.is_buff_technique:  # 攻击类每次都需要使用
            self.ctx.technique_used = False

        if self.use_technique and not self.ctx.technique_used:
            if self.ctx.is_buff_technique or \
                    self.ctx.is_attack_technique and mini_map.with_enemy_nearby(self.ctx.im, mm):  # 攻击类只有附近有敌人时候才使用
                op = UseTechnique(self.ctx, use_consumable=1,
                                  need_check_available=self.ctx.is_pc and not self.ctx.controller.is_moving,  # 只有战斗结束刚出来的时候可能用不了秘技
                                  need_check_point=True,  # 检查秘技点是否足够 可以在没有或者不能用药的情况加快判断
                                  )
                op_result = op.execute()
                self._update_not_in_world_time()  # 使用秘技的时间不应该在计算内

        self._attack(now_time)

        return Operation.round_wait()

    def _attack(self, now_time: float):
        if now_time - self.last_attack_time <= EnterAutoFight.ATTACK_INTERVAL:
            return
        self.last_attack_time = now_time
        if self.attack_direction > 0:
            self.ctx.controller.move(EnterAutoFight.ATTACK_DIRECTION_ARR[self.attack_direction % 4])
            time.sleep(0.2)
        self.attack_direction += 1
        self.ctx.controller.initiate_attack()
        time.sleep(0.5)

    def _update_not_in_world_time(self):
        """
        不在移动画面的情况
        更新一些统计时间
        :return:
        """
        now = time.time()
        self.last_not_in_world_time = now
        self.last_alert_time = now

    def on_resume(self):
        super().on_resume()
        self._update_not_in_world_time()

    def _recover_technique_point(self) -> OperationOneRoundResult:
        """
        恢复秘技点
        :return:
        """
        self.ctx.technique_used = False  # 重置使用情况
        click = self.find_and_click_area(ScreenDialog.FAST_RECOVER_CONFIRM.value)

        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_wait(wait=0.5)
        else:
            return Operation.round_retry('点击确认失败', wait=1)

    def _in_battle(self) -> OperationOneRoundResult:
        """
        战斗
        :return:
        """
        self._update_not_in_world_time()
        self.with_battle = True
        self.ctx.technique_used = False
        return Operation.round_wait(wait=1)
