import os

import cv2
import numpy as np
from cv2.typing import MatLike

from basic.img import cv2_utils
from basic.img.os import get_debug_image_dir, get_test_image, save_debug_image, get_debug_image
from sr import constants
from sr.config.game_config import get_game_config
from sr.constants.map import Region
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.image_holder import ImageHolder
from sr.image.sceenshot import mini_map
from sr.map_cal import MapCalculator


def _test_extract_arrow():
    dir = get_debug_image_dir()
    for filename in os.listdir(dir):
        screen = cv2_utils.read_image(os.path.join(dir, filename))
    # for i in range(5):
    #     screen = get_test_image('game%d' % (i+1))
        mm = ctx.map_cal.cut_mini_map(screen)
        cv2_utils.show_image(mm, win_name='mm')
        arrow = mini_map.extract_arrow(mm)
        cv2_utils.show_image(arrow, win_name='arrow')
        _, bw = cv2.threshold(arrow, 180, 255, cv2.THRESH_BINARY)
        cv2_utils.show_image(bw, win_name='bw')
        raw_arrow = cv2.bitwise_and(mm, mm, mask=bw)
        cv2_utils.show_image(raw_arrow, win_name='raw_arrow')

        cv2.waitKey(0)
        cv2.destroyAllWindows()


def _test_get_arrow_mask():
    screen = get_debug_image('1697036916493')
    mm = mc.cut_mini_map(screen)
    m, wm = mini_map.get_arrow_mask(mm)
    cv2_utils.show_image(m, win_name='m')
    cv2_utils.show_image(wm, win_name='wm')
    cv2.waitKey(0)


def _test_analyse_arrow_and_angle():
    screen = get_debug_image('1697036916493')
    mm = mc.cut_mini_map(screen)
    _, _, angle = mini_map.analyse_arrow_and_angle(mm, im)
    print(angle)


def _test_edge():
    screen: MatLike = get_debug_image('c')
    mm = mc.cut_mini_map(screen)
    info = mc.analyse_mini_map(mm)

    gray = cv2.cvtColor(mm, cv2.COLOR_BGR2GRAY)
    cv2_utils.show_image(gray, win_name='gray')

    template_origin = mini_map.get_edge_mask_by_hsv(mm, info.arrow_mask)

    region: Region = constants.map.P01_R02_JZCD
    lm = ih.get_large_map(region, 'mask')
    lm_mask = cv2.Canny(lm, threshold1=200, threshold2=230)

    kernel = np.ones((3, 3), np.uint8)
    source = cv2.dilate(lm_mask, kernel, iterations=1)
    source = mc.find_edge_mask(lm)
    cv2_utils.show_image(source, win_name='source')

    # mc.feature_match(lm_mask, None, hsv_mask, info.center_mask, show=True)

    for i in [1.00, 1.05, 1.10, 1.15, 1.20, 1.25]:
        height = int(template_origin.shape[0] * i)
        width = int(template_origin.shape[1] * i)
        template = cv2.resize(template_origin, (height, width))
        template_mask = cv2.resize(info.center_mask, (height, width))
        cv2_utils.show_image(template, win_name='template')
        result = cv2_utils.match_template(source, template, mask=template_mask, threshold=0.4, ignore_inf=True)
        if len(result) == 0:
            continue
        cv2_utils.show_image(lm_mask, result, win_name='match_template')
        print(result.max)
        cv2_utils.show_overlap(source, template, result.max.x, result.max.y, win_name='ovelap')
        cv2.waitKey(0)

    cv2.waitKey(0)


def _test_get_sp_mask_by_feature_match():
    screen: MatLike = get_debug_image('1696773991417')
    mm = mc.cut_mini_map(screen)
    info = mc.analyse_mini_map(mm)

    mini_map.get_sp_mask_by_feature_match(info, im, show=True)
    cv2.waitKey(0)


def _test_is_under_attack():
    for i in range(2):
        screen = get_test_image('%d' % (i + 1), sub_dir='under_attack')
        mm = mc.cut_mini_map(screen)
        print(mini_map.is_under_attack(mm, get_game_config().mini_map_pos, show=True))
        cv2.waitKey(0)


def _test_radio_mask():
    screen = get_debug_image('1697036262088')
    mm = mc.cut_mini_map(screen)
    road = np.zeros_like(mm, dtype=np.uint8)
    road[:,:] = [65,65,65]
    ans = cv2.subtract(mm, road)
    cv2_utils.show_image(ans, win_name='ans')
    cv2.waitKey(0)


def _test_get_enemy_road_mask():
    pass


def _test_cut_mini_map():
    screen = get_test_image('mm_arrow', sub_dir='mini_map')
    mm = mc.cut_mini_map(screen)
    save_debug_image(mm)
    # dir = get_debug_image_dir()
    # for x in os.listdir(dir):
    #     if not x.endswith('.png'):
    #         continue
    #     screen = cv2_utils.read_image(os.path.join(dir, x))
    #     mm = mc.cut_mini_map(screen)
    #     save_debug_image(mm)


if __name__ == '__main__':
    ih = ImageHolder()
    im = CvImageMatcher(ih)
    mc = MapCalculator(im=im)
    _test_cut_mini_map()