import os
import sys
import subprocess
import argparse
import jinja2

# 引擎目录
engine_dir = 'D:/UnrealEngine-ToonLit/UnrealEngine/Engine'

# 生成代码目录
hpp_dst_dir = '../../Source/Demo/Public/MGameTables'
cpp_dst_dir = '../../Source/Demo/Private/MGameTables'

# API宏名称，根据工程来定
api_name = 'DEMO_API'


# ======================================================================================================================

# 生成代码文件及数据文件的 Excel 文件名
FullExcelFiles = [
    'Item'
]

# 只生成数据文件的 Excel 文件名
DataExcelFiles = [
]

# ======================================================================================================================

P4EDIT_TEMPL = """
# 签出所有可能影响到的文件
{{P4CMD}} edit {{CWD}}/Source/Private/*.*
{{P4CMD}} edit {{CWD}}/Source/Public/*.*
{{P4CMD}} edit {{GDD_DIR}}/*.jsondata
"""

P4REVERT_TEMPL = """
# 还原未修改的文件
{{P4CMD}} revert -a {{CWD}}/Source/Private/...
{{P4CMD}} revert -a {{CWD}}/Source/Public/...
{{P4CMD}} revert -a {{GDD_DIR}}/*.jsondata
"""

XLS_TEMPL = """

# 生成代码文件及数据文件
{%- for xls_name in FullExcelFiles %}
{{XLS}} -src_file={{EXCEL_DIR}}/{{xls_name}}.xlsx -data_dst_dir={{GDD_DIR}}/ -dllexport_decl={{NAME_API}} -hpp_dst_dir={{hpp_dir}} -cpp_dst_dir={{cpp_dir}}
{%- endfor %}

# 只生成数据文件
{%- for xls_name in DataExcelFiles %}
{{XLS}} -src_file={{EXCEL_DIR}}/{{xls_name}}.xlsx -data_dst_dir={{GDD_DIR}}/
{%- endfor %}

"""


def get_ue_platform_name():
    platform = sys.platform
    if platform == 'darwin':
        return 'Mac'
    elif platform == 'win32':
        return 'Win64'
    else:
        return 'Linux'


def str_decode(line):
    try:
        return line.decode('utf-8')
    except:
        return line.decode('gbk')
    

def do_content(content):
    my_env = os.environ.copy()
    my_env['P4CONFIG'] = '.p4config' 
    for line in content.splitlines():
        line = line.strip().strip('\n').strip().strip('\n')
        if not line.startswith('#') and len(line) > 0:
            try:
                ret = subprocess.run(line.split(' '), env=my_env, capture_output=True)
                if ret.returncode != 0:
                    raise Exception(f'code={ret.returncode}\nmessage={str_decode(ret.stdout)} {str_decode(ret.stderr)}')
            except Exception as run_err:
                raise Exception(f'指令执行失败\ncmd={line}\n{run_err} ')   


def main():
    platform = get_ue_platform_name()
    excel_dir = '../../GameDesignData/Excel'
    gdd_dir = '../../Content/GDD'
    if platform == 'Win64':
        py_cmd = f'{engine_dir}/Binaries/ThirdParty/Python3/{platform}/python.exe'
        p4_cmd = f'{engine_dir}/Binaries/ThirdParty/Perforce/{platform}/p4.exe'
    else:
        py_cmd = f'{engine_dir}/Binaries/ThirdParty/Python3/{platform}/bin/python'
        p4_cmd = f'{engine_dir}/Binaries/ThirdParty/Perforce/{platform}/p4'

    cwd = os.getcwd()
    excel_dir = os.path.abspath(cwd + '/' + excel_dir)
    gdd_dir = os.path.abspath(cwd + '/' + gdd_dir)
    #p4_cmd = os.path.abspath(cwd + '/' + p4_cmd)
    #py_cmd = os.path.abspath(cwd + '/' + py_cmd)

    meta_data = {
        "CWD": cwd,
        "EXCEL_DIR": excel_dir,
        "GDD_DIR": gdd_dir,
        "P4CMD": p4_cmd,
        "PYCMD": py_cmd,
        'XLS': f'{py_cmd} xls_tool.py',
        'FullExcelFiles': FullExcelFiles,
        'DataExcelFiles': DataExcelFiles,

        'NAME_API': api_name,
        'hpp_dir': hpp_dst_dir,
        'cpp_dir': cpp_dst_dir,
    }
    
    try:
        edit_content = jinja2.Template(P4EDIT_TEMPL).render(meta_data)
        xls_content = jinja2.Template(XLS_TEMPL).render(meta_data)
        revert_content = jinja2.Template(P4REVERT_TEMPL).render(meta_data)
    except Exception as render_err:
        raise Exception(f'TEMPL 文件渲染失败\n{render_err}')

    # do_content(edit_content)
    try:
        do_content(xls_content)
    except Exception as run_err:
        #do_content(revert_content)
        raise run_err
    # do_content(revert_content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-log_file', nargs='?', const='none', help='日志文件')
    args = parser.parse_args()

    try:
        main()
    except Exception as e:
        text = f'ERROR {e}'
        if args.log_file is not None:
            with open(args.log_file, 'wb') as f:
                f.write(text.encode('utf-8'))
        print(text)
        exit(1)
    print(f'DONE.')
    exit(0)
