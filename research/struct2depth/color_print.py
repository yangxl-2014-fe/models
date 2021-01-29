# coding=utf-8


################################################################################
# Print Text with Color
################################################################################
class ColorPrint:
    """
    References
    ----------
    https://stackoverflow.com/a/39452138
    https://i.stack.imgur.com/j7e4i.gif
    """
    def __init__(self):
        pass

    @staticmethod
    def create_color():
        colors = {
            'CEND': '\33[0m',
            'CBOLD': '\33[1m',
            'CITALIC': '\33[3m',
            'CURL': '\33[4m',
            'CBLINK': '\33[5m',
            'CBLINK2': '\33[6m',
            'CSELECTED': '\33[7m',

            'CBLACK': '\33[30m',
            'CRED': '\33[31m',
            'CGREEN': '\33[32m',
            'CYELLOW': '\33[33m',
            'CBLUE': '\33[34m',
            'CVIOLET': '\33[35m',
            'CBEIGE': '\33[36m',
            'CWHITE': '\33[37m',

            'CBLACKBG': '\33[40m',
            'CREDBG': '\33[41m',
            'CGREENBG': '\33[42m',
            'CYELLOWBG': '\33[43m',
            'CBLUEBG': '\33[44m',
            'CVIOLETBG': '\33[45m',
            'CBEIGEBG': '\33[46m',
            'CWHITEBG': '\33[47m',

            'CGREY': '\33[90m',
            'CRED2': '\33[91m',
            'CGREEN2': '\33[92m',
            'CYELLOW2': '\33[93m',
            'CBLUE2': '\33[94m',
            'CVIOLET2': '\33[95m',
            'CBEIGE2': '\33[96m',
            'CWHITE2': '\33[97m',

            'CGREYBG': '\33[100m',
            'CREDBG2': '\33[101m',
            'CGREENBG2': '\33[102m',
            'CYELLOWBG2': '\33[103m',
            'CBLUEBG2': '\33[104m',
            'CVIOLETBG2': '\33[105m',
            'CBEIGEBG2': '\33[106m',
            'CWHITEBG2': '\33[107m'
        }
        return colors

    @staticmethod
    def print_debug(text):
        color_col = ColorPrint.create_color()
        print('{}{}{}'.format(color_col['CBLUE'], text, color_col['CEND']))

    @staticmethod
    def print_info(text):
        color_col = ColorPrint.create_color()
        print('{}{}{}'.format(color_col['CGREEN'], text, color_col['CEND']))

    @staticmethod
    def print_warn(text):
        color_col = ColorPrint.create_color()
        print('{}{}{}'.format(color_col['CYELLOW'], text, color_col['CEND']))

    @staticmethod
    def print_error(text):
        color_col = ColorPrint.create_color()
        print('{}{}{}'.format(color_col['CREDBG'], text, color_col['CBLACKBG']))

    @staticmethod
    def print_color(text, color):
        color_col = ColorPrint.create_color()
        if color.upper() in color_col.keys():
            print('{}{}{}'.format(color_col[color.upper()], text,
                                  color_col['CEND']))
        else:
            print('{}'.format(text))
