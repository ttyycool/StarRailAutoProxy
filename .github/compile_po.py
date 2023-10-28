import os

import os_utils
import polib


def compile_lang(model: str, lang: str):
    """
    将特定语言的文件编译成mo文件
    :param model: 模块 不同模块的多语言文本区分
    :param lang: 语言 cn
    :return: None
    """
    po_file_path = os.path.join(os_utils.get_path_under_work_dir('data', 'locales', model), '%s.po' % lang)
    mo_file_path = os.path.join(os_utils.get_path_under_work_dir('data', 'locales', lang, 'LC_MESSAGES'), '%s.mo' % model)

    po = polib.pofile(po_file_path)
    po.save_as_mofile(mo_file_path)


def compile_po_files():
    """
    将不同语言的po文件编译成mo
    :return:
    """
    for model in ['ocr', 'ui']:
        for lang in ['cn', 'en']:
            compile_lang(model, lang)


if __name__ == '__main__':
    compile_po_files()
